"""Behavioral tests for the Discord bot commands.

Executes the real command callbacks against in-memory repositories and a
mocked Discord context, so command wiring (parsing, errors, replies, side
effects) is covered without discord.py or a live connection.
"""

import asyncio
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Mock discord before importing bot, keeping the command functions intact.
# A plain MagicMock would swallow the @bot.command decorators and replace
# every command with a mock, so the mock's Bot.command()/Bot.event()
# decorators pass the original coroutine through (with .callback/.error
# attributes the bot code relies on).
if "bot" not in sys.modules:

    class _PassthroughCommand:
        """Real function wrapped like a discord.py command object."""

        def __init__(self, func):
            self.callback = func
            self.__name__ = getattr(func, "__name__", "command")
            functools_update = __import__("functools").update_wrapper
            functools_update(self, func, updated=())

        def __call__(self, *args, **kwargs):
            return self.callback(*args, **kwargs)

        def error(self, handler):
            return handler

    def _command_decorator(*args, **kwargs):
        def decorate(func):
            return _PassthroughCommand(func)

        return decorate

    def _event_decorator(func):
        return func

    mock_discord = MagicMock()
    mock_commands = MagicMock()
    mock_ext = MagicMock()
    mock_ext.commands = mock_commands
    mock_discord.ext = mock_ext
    mock_bot_instance = MagicMock()
    mock_commands.Bot.return_value = mock_bot_instance
    mock_bot_instance.command = MagicMock(side_effect=_command_decorator)
    mock_bot_instance.event = MagicMock(side_effect=_event_decorator)
    sys.modules["discord"] = mock_discord
    sys.modules["discord.ext"] = mock_ext
    sys.modules["discord.ext.commands"] = mock_commands

import bot  # noqa: E402
import core  # noqa: E402


class FakeThemeRepo:
    """In-memory theme repository; tests never touch live data files."""

    def __init__(self, themes=None):
        self.themes = [dict(t) for t in (themes or [])]

    def load_themes(self, include_hidden=True):
        if include_hidden:
            return self.themes
        return [t for t in self.themes if not t.get("is_hidden", False)]

    def save_themes(self, themes):
        self.themes = [dict(t) for t in themes]


class FakeHeroRepo:
    """In-memory hero repository."""

    def __init__(self, heroes=None):
        self.heroes = list(heroes or [])

    def load_heroes(self):
        return self.heroes

    def save_heroes(self, heroes):
        self.heroes = list(heroes)


def make_hero(hero_id, name=None, positions=None):
    return {
        "id": hero_id,
        "name": name or hero_id.replace("_", " ").title(),
        "primary_role": "Carry",
        "positions": positions or [1],
        "aliases": [],
    }


def make_theme(name, hero_ids, description="", hidden=False):
    return {
        "name": name,
        "description": description,
        "hero_ids": list(hero_ids),
        "is_hidden": hidden,
        "feedback_score": 0,
    }


def make_suggestion(theme="Red", hero_count=2):
    return {
        "theme": theme,
        "description": "A test theme",
        "heroes": "- [Axe](https://www.dota2.com/hero/axe) (pos 3)",
        "hero_count": hero_count,
        "feedback_score": 0,
    }


def make_ctx():
    """A mocked command context: send awaited, message controllable."""
    ctx = MagicMock()
    ctx.send = AsyncMock()
    sent = MagicMock()
    sent.add_reaction = AsyncMock()
    ctx.send.return_value = sent
    ctx.author = MagicMock()
    ctx.author.id = 42
    ctx.message = MagicMock()
    return ctx


def sent_texts(ctx):
    """All plain strings the command sent, concatenated."""
    chunks = []
    for call in ctx.send.await_args_list:
        args, kwargs = call
        if args:
            chunks.append(args[0])
    return "\n".join(chunks)


class BotCommandTestCase(unittest.TestCase):
    """Hermetic fixture: swapped-in fakes are restored after each test."""

    HEROES = [
        make_hero("axe", "Axe", [3, 4]),
        make_hero("lina", "Lina", [2]),
        make_hero("crystal_maiden", "Crystal Maiden", [5]),
    ]

    def setUp(self):
        self._saved = (
            bot.THEME_REPO,
            bot.HERO_REPO,
            bot.HERO_RESOLVER,
            bot.SESSION_STATE,
        )
        self.hero_repo = FakeHeroRepo(self.HEROES)
        self.theme_repo = FakeThemeRepo(
            [
                make_theme("Red", ["axe"]),
                make_theme("Blue", ["lina", "crystal_maiden"]),
                make_theme("Hidden", ["axe"], hidden=True),
            ]
        )
        bot.HERO_REPO = self.hero_repo
        bot.THEME_REPO = self.theme_repo
        bot.HERO_RESOLVER = core.HeroResolver(self.hero_repo)
        bot.SESSION_STATE = type(bot.SESSION_STATE)()

    def tearDown(self):
        (
            bot.THEME_REPO,
            bot.HERO_REPO,
            bot.HERO_RESOLVER,
            bot.SESSION_STATE,
        ) = self._saved


class TestAddThemeCommand(BotCommandTestCase):
    """!addtheme creates, validates, and reports themes."""

    def test_adds_theme_with_heroes(self):
        ctx = make_ctx()
        asyncio.run(bot.add_theme_command(ctx, "New Theme", "axe", "lina"))
        names = [t["name"] for t in self.theme_repo.themes]
        self.assertIn("New Theme", names)
        self.assertIn("added successfully", sent_texts(ctx))

    def test_first_non_hero_argument_is_description(self):
        ctx = make_ctx()
        asyncio.run(bot.add_theme_command(ctx, "Described", "A theme", "axe", "lina"))
        theme = next(t for t in self.theme_repo.themes if t["name"] == "Described")
        self.assertEqual(theme["description"], "A theme")
        self.assertEqual(theme["hero_ids"], ["axe", "lina"])

    def test_rejects_invalid_hero_names(self):
        ctx = make_ctx()
        asyncio.run(bot.add_theme_command(ctx, "Broken", "notahero", "alsonotahero"))
        names = [t["name"] for t in self.theme_repo.themes]
        self.assertNotIn("Broken", names)
        self.assertIn("Invalid hero names", sent_texts(ctx))

    def test_duplicate_theme_is_rejected(self):
        ctx = make_ctx()
        asyncio.run(bot.add_theme_command(ctx, "Red", "axe"))
        self.assertEqual(
            len([t for t in self.theme_repo.themes if t["name"] == "Red"]), 1
        )
        self.assertIn("already exists", sent_texts(ctx))


class TestHideUnhideCommands(BotCommandTestCase):
    """!hidetheme / !unhidetheme flip visibility and reply clearly."""

    def test_hides_existing_theme(self):
        ctx = make_ctx()
        asyncio.run(bot.hide_theme_command(ctx, "Red"))
        theme = next(t for t in self.theme_repo.themes if t["name"] == "Red")
        self.assertTrue(theme.get("is_hidden"))
        self.assertIn("hidden", sent_texts(ctx))

    def test_hide_unknown_theme_reports_error(self):
        ctx = make_ctx()
        asyncio.run(bot.hide_theme_command(ctx, "Nope"))
        self.assertIn("not found", sent_texts(ctx).lower())

    def test_unhides_hidden_theme(self):
        ctx = make_ctx()
        asyncio.run(bot.unhide_theme_command(ctx, "Hidden"))
        theme = next(t for t in self.theme_repo.themes if t["name"] == "Hidden")
        self.assertFalse(theme.get("is_hidden"))
        self.assertIn("appear in suggestions", sent_texts(ctx).lower())


class TestUpdateThemeCommand(BotCommandTestCase):
    """!updatetheme add/remove heroes directly."""

    def test_add_heroes_directly(self):
        ctx = make_ctx()
        asyncio.run(bot.update_theme_command(ctx, "Red", "add", "lina"))
        theme = next(t for t in self.theme_repo.themes if t["name"] == "Red")
        self.assertEqual(theme["hero_ids"], ["axe", "lina"])
        self.assertIn("updated successfully", sent_texts(ctx))

    def test_remove_heroes_directly(self):
        """Removing one hero from a 3-hero theme succeeds."""
        ctx = make_ctx()
        asyncio.run(bot.update_theme_command(ctx, "Blue", "add", "axe"))
        asyncio.run(bot.update_theme_command(ctx, "Blue", "remove", "lina"))
        theme = next(t for t in self.theme_repo.themes if t["name"] == "Blue")
        self.assertEqual(theme["hero_ids"], ["axe", "crystal_maiden"])

    def test_remove_below_minimum_heroes_is_rejected(self):
        """Removing heroes down to one is rejected with a friendly message."""
        ctx = make_ctx()
        asyncio.run(bot.update_theme_command(ctx, "Blue", "remove", "lina"))
        theme = next(t for t in self.theme_repo.themes if t["name"] == "Blue")
        # The 2-hero theme is untouched; the user sees the min-heroes rule
        self.assertEqual(theme["hero_ids"], ["lina", "crystal_maiden"])
        self.assertIn("at least 2", sent_texts(ctx))

    def test_invalid_action_is_rejected(self):
        ctx = make_ctx()
        asyncio.run(bot.update_theme_command(ctx, "Red", "rename", "lina"))
        self.assertIn("Invalid action", sent_texts(ctx))

    def test_invalid_hero_names_are_reported(self):
        ctx = make_ctx()
        asyncio.run(bot.update_theme_command(ctx, "Red", "add", "notahero"))
        self.assertIn("Invalid hero names", sent_texts(ctx))


class TestListCommands(BotCommandTestCase):
    """!listthemes / !listheroes list data with hidden status."""

    def test_listthemes_includes_hidden_marker(self):
        ctx = make_ctx()
        asyncio.run(bot.list_themes_command(ctx))
        text = sent_texts(ctx)
        self.assertIn("Red", text)
        self.assertIn("Hidden (hidden)", text)

    def test_listheroes_lists_names(self):
        ctx = make_ctx()
        asyncio.run(bot.list_heroes_command(ctx))
        text = sent_texts(ctx)
        self.assertIn("Axe", text)
        self.assertIn("Lina", text)


class TestThemeSuggestionCommand(BotCommandTestCase):
    """!theme: help word, validation, single and multiple suggestions."""

    def test_help_word_shows_in_context_help(self):
        ctx = make_ctx()
        asyncio.run(bot.theme_command(ctx, "help"))
        text = sent_texts(ctx)
        self.assertIn("!theme", text)
        self.assertIn("!dailytheme", text)

    def test_question_mark_also_shows_help(self):
        ctx = make_ctx()
        asyncio.run(bot.theme_command(ctx, "?"))
        self.assertIn("!theme", sent_texts(ctx))

    def test_invalid_party_size_is_rejected(self):
        ctx = make_ctx()
        asyncio.run(bot.theme_command(ctx, "9"))
        self.assertIn("between 1 and 5", sent_texts(ctx))

    def test_non_numeric_party_size_is_rejected(self):
        ctx = make_ctx()
        asyncio.run(bot.theme_command(ctx, "big"))
        self.assertIn("between 1 and 5", sent_texts(ctx))

    def test_default_call_sends_one_suggestion(self):
        ctx = make_ctx()
        with patch.object(bot.core, "get_theme_suggestion") as sug, patch.object(
            bot, "lane_duos_for_theme", return_value=""
        ):
            sug.return_value = make_suggestion()
            asyncio.run(bot.theme_command(ctx))
        sug.assert_called_once()
        self.assertEqual(ctx.send.await_count, 1)
        self.assertTrue(bot.SESSION_STATE.has_suggestion(ctx.send.return_value.id))

    def test_invalid_suggestion_count_is_rejected(self):
        ctx = make_ctx()
        asyncio.run(bot.theme_command(ctx, "2", "99"))
        self.assertIn("between 1 and 5", sent_texts(ctx))

    def test_multiple_count_sends_distinct_suggestions(self):
        ctx = make_ctx()
        suggestions = [make_suggestion("Red"), make_suggestion("Blue")]
        with patch.object(bot.core, "get_theme_suggestions") as multi, patch.object(
            bot, "lane_duos_for_theme", return_value=""
        ):
            multi.return_value = suggestions
            asyncio.run(bot.theme_command(ctx, "3", "2"))
        multi.assert_called_once()
        self.assertEqual(ctx.send.await_count, 2)

    def test_sent_suggestion_gets_vote_reactions(self):
        ctx = make_ctx()
        with patch.object(bot.core, "get_theme_suggestion") as sug, patch.object(
            bot, "lane_duos_for_theme", return_value=""
        ):
            sug.return_value = make_suggestion()
            asyncio.run(bot.theme_command(ctx))
        sent = ctx.send.return_value
        self.assertEqual(sent.add_reaction.await_count, 3)

    def test_tr_alias_delegates_to_theme_command(self):
        ctx = make_ctx()
        with patch.object(bot.core, "get_theme_suggestion") as sug, patch.object(
            bot, "lane_duos_for_theme", return_value=""
        ):
            sug.return_value = make_suggestion()
            asyncio.run(bot.themeroll_command(ctx, "2"))
        sug.assert_called_once()


class TestDailyThemeCommand(BotCommandTestCase):
    """!dailytheme posts today's theme with a date footer."""

    def test_posts_daily_theme(self):
        ctx = make_ctx()
        with patch.object(bot.core, "get_daily_theme") as daily, patch.object(
            bot, "lane_duos_for_theme", return_value=""
        ):
            daily.return_value = dict(make_suggestion(), date="2026-10-25")
            asyncio.run(bot.daily_theme_command(ctx))
        daily.assert_called_once()
        self.assertEqual(ctx.send.await_count, 1)
        self.assertTrue(bot.SESSION_STATE.has_suggestion(ctx.send.return_value.id))

    def test_invalid_party_size_is_rejected(self):
        ctx = make_ctx()
        asyncio.run(bot.daily_theme_command(ctx, "6"))
        self.assertIn("between 1 and 5", sent_texts(ctx))


if __name__ == "__main__":
    unittest.main()
