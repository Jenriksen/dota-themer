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
        """Bot formats response with theme, description, heroes."""
        bot_content = read_bot_file()
        self.assertIn("**Theme:**", bot_content)
        self.assertIn("**Heroes:**", bot_content)


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
