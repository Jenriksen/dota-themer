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
        self.assertIn("SESSION_STATE.is_locked(", content)
