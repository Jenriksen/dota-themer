"""
Unit tests for Discord bot functionality.
Tests the bot module structure without requiring discord.py to be installed.
"""

import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock discord before importing bot
mock_discord = MagicMock()
mock_commands = MagicMock()
mock_discord.ext.commands = mock_commands
mock_discord.Intents = MagicMock()
mock_discordIntents = MagicMock()
mock_discord.Intents.default.return_value = mock_discordIntents

sys.modules["discord"] = mock_discord
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = mock_commands


def read_bot_file():
    """Helper to read bot.py with UTF-8 encoding."""
    with open("bot.py", "r", encoding="utf-8") as f:
        return f.read()


class TestBotFileStructure(unittest.TestCase):
    """Tests for bot.py file structure."""

    def test_file_exists(self):
        """bot.py file exists."""
        import os

        self.assertTrue(os.path.exists("bot.py"))

    def test_imports_core(self):
        """Bot imports core module."""
        bot_content = read_bot_file()
        self.assertIn("import core", bot_content)

    def test_uses_get_theme_suggestion(self):
        """Bot uses get_theme_suggestion from core."""
        bot_content = read_bot_file()
        self.assertIn("core.get_theme_suggestion", bot_content)

    def test_uses_correct_prefix(self):
        """Bot uses '!' as command prefix."""
        bot_content = read_bot_file()
        self.assertIn('command_prefix="!"', bot_content)

    def test_message_content_intent_enabled(self):
        """Message content intent is enabled."""
        bot_content = read_bot_file()
        self.assertIn("message_content = True", bot_content)

    def test_uses_environment_variable_for_token(self):
        """Bot reads token from DISCORD_TOKEN environment variable."""
        bot_content = read_bot_file()
        self.assertIn("DISCORD_TOKEN", bot_content)
        self.assertIn("os.getenv", bot_content)


class TestBotCommands(unittest.TestCase):
    """Tests for bot command definitions."""

    def test_theme_command_has_help(self):
        """theme command has help text."""
        bot_content = read_bot_file()
        self.assertIn('help="Get a theme suggestion', bot_content)

    def test_theme_command_has_default_party_size(self):
        """theme command has default party size of 2."""
        bot_content = read_bot_file()
        self.assertIn("party_size: int = 2", bot_content)

    def test_theme_command_validates_party_size(self):
        """theme command validates party size."""
        bot_content = read_bot_file()
        self.assertIn("party_size < 1 or party_size > 5", bot_content)

    def test_has_alias_commands(self):
        """Bot has alias commands like !tr."""
        bot_content = read_bot_file()
        self.assertIn('aliases=["tr"]', bot_content)

    def test_has_help_command(self):
        """Bot has a help command."""
        bot_content = read_bot_file()
        self.assertIn("helptheme", bot_content)

    def test_formats_response_correctly(self):
        """Bot formats response via the presentation module."""
        bot_content = read_bot_file()
        self.assertIn("presentation.render_theme_suggestion(", bot_content)
        with open("presentation.py", encoding="utf-8") as f:
            presentation_content = f.read()
        self.assertIn("**Theme:**", presentation_content)
        self.assertIn("**Heroes:**", presentation_content)


class TestErrorHandling(unittest.TestCase):
    """Tests for error handling in bot."""

    def test_error_handler_for_theme_command(self):
        """Error handler is registered for theme command."""
        bot_content = read_bot_file()
        self.assertIn("@theme_command.error", bot_content)

    def test_handles_missing_token(self):
        """Bot handles missing DISCORD_TOKEN gracefully."""
        bot_content = read_bot_file()
        self.assertIn("DISCORD_TOKEN environment variable not set", bot_content)
        self.assertIn("exit(1)", bot_content)

    def test_handles_invalid_party_size_in_command(self):
        """theme command handles invalid party size."""
        bot_content = read_bot_file()
        self.assertIn("Party size must be between 1 and 5", bot_content)


if __name__ == "__main__":
    unittest.main()


class TestRepositoryWiring(unittest.TestCase):
    """Tests for R1d: bot constructs cached repositories and passes them to core."""

    def test_constructs_cached_repositories_at_startup(self):
        """bot.py creates CachedHeroRepository/CachedThemeRepository singletons."""
        content = read_bot_file()
        self.assertIn("CachedHeroRepository", content)
        self.assertIn("CachedThemeRepository", content)

    def test_no_direct_file_loads_in_bot(self):
        """bot.py no longer calls core.load_heroes/core.load_themes directly."""
        content = read_bot_file()
        self.assertNotIn("core.load_heroes()", content)
        self.assertNotIn("core.load_themes(", content)

    def test_no_uncached_mutation_calls(self):
        """Mutation calls pass theme_repo so the cache stays coherent."""
        content = read_bot_file()
        for call in ("core.add_theme(", "core.update_theme(", "core.hide_theme("):
            self.assertIn(call, content)
        # Every mutation call site must carry theme_repo=THEME_REPO
        import re

        for pattern in (
            r"core\.add_theme\(",
            r"core\.update_theme\(",
            r"core\.hide_theme\(",
            r"core\.unhide_theme\(",
            r"core\.update_theme_feedback\(",
            r"core\.remove_theme\(",
        ):
            for m in re.finditer(pattern, content):
                call_end = content.index(
                    ")",
                    content.index(
                        pattern.replace("\\.", ".").replace("\\(", "("), m.start()
                    ),
                )
                segment = content[m.start() : call_end]
                self.assertIn("theme_repo=", segment, f"{segment} must pass theme_repo")


class TestHeroResolverWiring(unittest.TestCase):
    """Tests for R2a/R2b: bot uses the single HeroResolver service."""

    def test_constructs_hero_resolver(self):
        """bot.py creates a HeroResolver singleton."""
        content = read_bot_file()
        self.assertIn("core.HeroResolver(", content)

    def test_no_inline_resolution_loops(self):
        """The three divergent resolution loops are gone from bot.py."""
        content = read_bot_file()
        self.assertNotIn("best_score", content)
        self.assertNotIn("hero_name_to_id", content)


class TestSessionStateWiring(unittest.TestCase):
    """Tests for R5a: bot uses the SessionState object for session tracking."""

    def test_constructs_session_state(self):
        """bot.py creates a SessionState singleton."""
        content = read_bot_file()
        self.assertIn("session_state.SessionState()", content)

    def test_no_raw_session_dicts(self):
        """The three module-level session dicts are gone from bot.py."""
        content = read_bot_file()
        self.assertNotIn("theme_suggestion_messages", content)
        self.assertNotIn("active_modification_threads", content)
        self.assertNotIn("messages_with_active_threads", content)

    def test_uses_session_state_accessors(self):
        """bot.py reads/writes session data via SessionState methods."""
        content = read_bot_file()
        self.assertIn("SESSION_STATE.register_suggestion(", content)
        self.assertIn("SESSION_STATE.register_thread(", content)
        self.assertIn("SESSION_STATE.remove_thread(", content)


class TestVoteLockPolicyWiring(unittest.TestCase):
    """Tests for R5b: bot uses the VoteLockPolicy for the 2-hour rule."""

    def test_constructs_vote_lock_policy(self):
        """bot.py creates a VoteLockPolicy singleton."""
        content = read_bot_file()
        self.assertIn("session_state.VoteLockPolicy()", content)

    def test_no_inline_two_hour_checks(self):
        """The inlined 2-hour elapsed checks are gone from bot.py."""
        content = read_bot_file()
        self.assertNotIn("timedelta(hours=2)", content)

    def test_reaction_handlers_use_policy(self):
        """All lock decisions go through VOTE_LOCK_POLICY.evaluate."""
        content = read_bot_file()
        self.assertGreaterEqual(content.count("VOTE_LOCK_POLICY.evaluate("), 3)


class TestHandlerSplit(unittest.TestCase):
    """Tests for R5c/R5d: the giant handlers are split into units."""

    def test_on_message_is_slim(self):
        """on_message delegates parsing to thread_commands and actions to helpers."""
        content = read_bot_file()
        self.assertIn("thread_commands.is_exit_command(", content)
        self.assertIn("thread_commands.parse_modification(", content)
        self.assertIn("end_modification_session(", content)
        self.assertIn("refresh_original_suggestion(", content)

    def test_on_reaction_add_is_slim(self):
        """on_reaction_add dispatches to per-emoji handlers."""
        content = read_bot_file()
        self.assertIn("handle_question_mark_reaction(", content)
        self.assertIn("handle_vote_reaction(", content)
        self.assertIn("build_heroes_list_text(", content)

    def test_modification_success_path_replies_success(self):
        """A successful thread modification replies with the success message.

        Regression guard for the R3 migration bug where the success block
        sat dead inside the except arm.
        """
        content = read_bot_file()
        self.assertNotIn(
            'else:\n        await message.channel.send(f"\u274c {message_text}")',
            content,
        )
