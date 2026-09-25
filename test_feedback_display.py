import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

import bot
import presentation


class FakeThemeRepo:
    """In-memory theme repository so tests never touch live data files."""

    def __init__(self, themes=None):
        self.themes = list(themes or [])

    def load_themes(self, include_hidden=True):
        return [t for t in self.themes if include_hidden or not t.get("is_hidden")]

    def save_themes(self, themes):
        self.themes = list(themes)


class FakeHeroRepo:
    """In-memory hero repository."""

    def __init__(self, heroes=None):
        self.heroes = list(heroes or [])

    def load_heroes(self):
        return self.heroes

    def save_heroes(self, heroes):
        self.heroes = list(heroes)


def make_theme():
    return {
        "name": "Carry Duo",
        "description": "Two hard carries",
        "hero_ids": ["axe"],
        "is_hidden": False,
        "feedback_score": 0,
    }


def make_vote_reaction(message_id=111):
    """Build a 👍 reaction on a bot-owned suggestion message."""
    message = MagicMock()
    message.id = message_id
    message.author = bot.bot.user
    message.edit = AsyncMock()
    message.add_reaction = AsyncMock()
    message.clear_reaction = AsyncMock()
    reaction = MagicMock()
    reaction.message = message
    reaction.emoji = presentation.UP_VOTE
    return reaction


class FeedbackDisplayTestCase(unittest.TestCase):
    """Hermetic fixture: fresh session state + in-memory repos (#51)."""

    def setUp(self):
        self._real_state = bot.SESSION_STATE
        self._real_theme_repo = bot.THEME_REPO
        self._real_hero_repo = bot.HERO_REPO
        bot.SESSION_STATE = type(bot.SESSION_STATE)()
        self.theme_repo = FakeThemeRepo([make_theme()])
        bot.THEME_REPO = self.theme_repo
        bot.HERO_REPO = FakeHeroRepo(
            [{"id": "axe", "name": "Axe", "positions": [3, 4]}]
        )
        bot.SESSION_STATE.register_suggestion(message_id=111, theme_name="Carry Duo")

    def tearDown(self):
        bot.SESSION_STATE = self._real_state
        bot.THEME_REPO = self._real_theme_repo
        bot.HERO_REPO = self._real_hero_repo

    def registered_reaction(self):
        reaction = make_vote_reaction()
        user = MagicMock()
        return reaction, user

    def test_vote_add_updates_displayed_score(self):
        reaction, user = self.registered_reaction()
        message_info = bot.SESSION_STATE.get_suggestion(message_id=111)

        asyncio.run(
            bot.handle_vote_reaction(reaction, user, message_info, presentation.UP_VOTE)
        )

        self.assertEqual(self.theme_repo.themes[0]["feedback_score"], 1)

    def test_vote_add_edits_message_with_new_score(self):
        reaction, user = self.registered_reaction()
        message_info = bot.SESSION_STATE.get_suggestion(message_id=111)

        asyncio.run(
            bot.handle_vote_reaction(reaction, user, message_info, presentation.UP_VOTE)
        )

        reaction.message.edit.assert_awaited_once()
        rendered = reaction.message.edit.await_args.kwargs.get("content", "")
        self.assertIn("**Feedback:** 1", rendered)

    def test_vote_remove_edits_message_with_new_score(self):
        reaction, user = self.registered_reaction()
        reaction.emoji = presentation.UP_VOTE
        message_info = bot.SESSION_STATE.get_suggestion(message_id=111)

        asyncio.run(bot.handle_vote_removal(reaction, user, message_info))

        reaction.message.edit.assert_awaited_once()
        rendered = reaction.message.edit.await_args.kwargs.get("content", "")
        self.assertIn("**Feedback:** -1", rendered)

    def test_failed_edit_does_not_break_vote(self):
        reaction, user = self.registered_reaction()
        reaction.message.edit = AsyncMock(side_effect=Exception("edit failed"))
        message_info = bot.SESSION_STATE.get_suggestion(message_id=111)

        asyncio.run(
            bot.handle_vote_reaction(reaction, user, message_info, presentation.UP_VOTE)
        )

        self.assertEqual(self.theme_repo.themes[0]["feedback_score"], 1)

    def test_locked_message_is_not_edited(self):
        bot.SESSION_STATE.lock_suggestion(111)
        reaction, user = self.registered_reaction()
        message_info = bot.SESSION_STATE.get_suggestion(message_id=111)

        asyncio.run(
            bot.handle_vote_reaction(reaction, user, message_info, presentation.UP_VOTE)
        )

        reaction.message.edit.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
