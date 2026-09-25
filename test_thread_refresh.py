import unittest
from unittest.mock import AsyncMock, MagicMock

import bot


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


def make_thread_message(thread_id=55):
    """Build a message that lives inside a modification thread."""
    parent = MagicMock()
    parent.id = 777
    parent.fetch_message = AsyncMock()

    thread = MagicMock()
    thread.id = thread_id
    thread.parent_id = parent.id
    thread.parent = parent
    thread.fetch_message = AsyncMock()

    message = MagicMock()
    message.channel = thread
    message.id = 900
    message.channel.parent = parent

    bot.bot.fetch_channel = AsyncMock(return_value=parent)
    return message, parent, thread


class ThreadRefreshTestCase(unittest.TestCase):
    """Shared fixture: hermetic session state + in-memory repos."""

    def setUp(self):
        self._real_state = bot.SESSION_STATE
        self._real_theme_repo = bot.THEME_REPO
        self._real_hero_repo = bot.HERO_REPO
        self._real_fetch_channel = bot.bot.fetch_channel
        bot.SESSION_STATE = type(bot.SESSION_STATE)()
        bot.THEME_REPO = FakeThemeRepo(
            [
                {
                    "name": "Carry Duo",
                    "description": "Two hard carries",
                    "hero_ids": ["axe"],
                    "is_hidden": False,
                    "feedback_score": 0,
                }
            ]
        )
        bot.HERO_REPO = FakeHeroRepo(
            [{"id": "axe", "name": "Axe", "positions": [3, 4]}]
        )

    def tearDown(self):
        bot.SESSION_STATE = self._real_state
        bot.THEME_REPO = self._real_theme_repo
        bot.HERO_REPO = self._real_hero_repo
        bot.bot.fetch_channel = self._real_fetch_channel


class TestRefreshOriginalSuggestion(ThreadRefreshTestCase):
    """refresh_original_suggestion fetches the tracked message, not the channel id.

    Regression tests for #50: fetch_message(parent_id) passed a channel id
    where a message id was expected, causing 10008 Unknown Message.
    """

    def test_fetches_stored_message_id_via_parent_channel(self):
        """The original message is fetched by the id stored in session state."""
        import asyncio

        message, parent, thread = make_thread_message()
        bot.SESSION_STATE.register_suggestion(message_id=111, theme_name="Carry Duo")
        bot.SESSION_STATE.register_thread(
            thread_id=thread.id, theme_name="Carry Duo", user_id=7, message_id=111
        )

        target = MagicMock()
        target.id = 111
        target.edit = AsyncMock()
        parent.fetch_message = AsyncMock(return_value=target)

        async def run():
            await bot.refresh_original_suggestion(message, "Carry Duo")

        asyncio.run(run())
        parent.fetch_message.assert_awaited_once_with(111)
        thread.fetch_message.assert_not_awaited()
        target.edit.assert_awaited_once()

    def test_does_not_fetch_message_with_channel_id(self):
        """fetch_message must never be called with the parent channel id."""
        import asyncio

        message, parent, thread = make_thread_message()
        bot.SESSION_STATE.register_suggestion(message_id=111, theme_name="Carry Duo")
        bot.SESSION_STATE.register_thread(
            thread_id=thread.id, theme_name="Carry Duo", user_id=7, message_id=111
        )

        async def run():
            await bot.refresh_original_suggestion(message, "Carry Duo")

        asyncio.run(run())
        for call in parent.fetch_message.await_args_list:
            self.assertNotEqual(call.args[0], 777)
        parent.fetch_message.assert_awaited_once_with(111)

    def test_unknown_thread_is_a_noop(self):
        """A message in an untracked thread does not fetch anything."""
        import asyncio

        message, parent, thread = make_thread_message()

        async def run():
            await bot.refresh_original_suggestion(message, "Carry Duo")

        asyncio.run(run())
        parent.fetch_message.assert_not_awaited()


class TestEndModificationSession(ThreadRefreshTestCase):
    """end_modification_session restores reactions on the tracked message (#50)."""

    def test_restores_reactions_on_stored_message_id(self):
        """The restore targets the message id from session state, not parent_id."""
        import asyncio

        message, parent, thread = make_thread_message()
        bot.SESSION_STATE.register_suggestion(message_id=111, theme_name="Carry Duo")
        bot.SESSION_STATE.register_thread(
            thread_id=thread.id, theme_name="Carry Duo", user_id=7, message_id=111
        )

        target = MagicMock()
        target.id = 111
        target.clear_reaction = AsyncMock()
        target.add_reaction = AsyncMock()
        parent.fetch_message = AsyncMock(return_value=target)
        thread.send = AsyncMock()
        thread.archive = AsyncMock()

        async def run():
            await bot.end_modification_session(message, thread.id)

        asyncio.run(run())
        parent.fetch_message.assert_awaited_once_with(111)
        target.clear_reaction.assert_awaited_once_with("\u2705")
        target.add_reaction.assert_awaited_once_with("\u2753")
        # The thread is still removed from tracking when the session ends
        self.assertFalse(bot.SESSION_STATE.has_thread(thread.id))


if __name__ == "__main__":
    unittest.main()
