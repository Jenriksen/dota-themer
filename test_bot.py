"""
Unit tests for Discord bot functionality.
Tests the bot commands without requiring Discord connection.
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import sys

# Mock discord module since it may not be installed
sys.modules['discord'] = MagicMock()
sys.modules['discord.ext'] = MagicMock()
sys.modules['discord.ext.commands'] = MagicMock()

# Now import bot module
import bot
import core


class TestBotSetup(unittest.TestCase):
    """Tests for bot setup and configuration."""

    def test_bot_exists(self):
        """Bot instance is created."""
        self.assertIsNotNone(bot.bot)

    def test_bot_has_correct_prefix(self):
        """Bot uses '!' as command prefix."""
        self.assertEqual(bot.bot.command_prefix, "!")

    def test_intents_configured(self):
        """Message content intents are enabled."""
        self.assertTrue(bot.intents.message_content)


class TestThemeCommand(unittest.IsolatedAsyncioTestCase):
    """Tests for the !theme command."""

    async def test_theme_command_uses_core_function(self):
        """!theme command calls get_theme_suggestion from core."""
        # Create a mock context
        mock_ctx = MagicMock()
        mock_ctx.send = AsyncMock()
        
        # Mock get_theme_suggestion
        with patch.object(core, 'get_theme_suggestion') as mock_suggestion:
            mock_suggestion.return_value = {
                'theme': 'Test Theme',
                'description': 'A test theme',
                'heroes': 'Hero1 (1,2), Hero2 (3,4)',
                'hero_count': 2
            }
            
            # Call the command
            await bot.theme_command.callback(mock_ctx, party_size=2)
            
            # Verify get_theme_suggestion was called
            mock_suggestion.assert_called_once_with(2)
            
            # Verify response was sent
            mock_ctx.send.assert_called_once()
            call_args = mock_ctx.send.call_args[0][0]
            self.assertIn("Test Theme", call_args)
            self.assertIn("A test theme", call_args)
            self.assertIn("Hero1 (1,2), Hero2 (3,4)", call_args)

    async def test_theme_command_default_party_size(self):
        """!theme without party size uses default of 2."""
        mock_ctx = MagicMock()
        mock_ctx.send = AsyncMock()
        
        with patch.object(core, 'get_theme_suggestion') as mock_suggestion:
            mock_suggestion.return_value = {
                'theme': 'Test',
                'description': '',
                'heroes': 'Hero (1,2)',
                'hero_count': 1
            }
            
            await bot.theme_command.callback(mock_ctx)
            mock_suggestion.assert_called_once_with(2)

    async def test_theme_command_validates_party_size(self):
        """!theme rejects party size outside 1-5 range."""
        mock_ctx = MagicMock()
        mock_ctx.send = AsyncMock()
        
        await bot.theme_command.callback(mock_ctx, party_size=0)
        mock_ctx.send.assert_called_once()
        call_args = mock_ctx.send.call_args[0][0]
        self.assertIn("Party size must be between 1 and 5", call_args)
        
        mock_ctx.reset_mock()
        await bot.theme_command.callback(mock_ctx, party_size=6)
        mock_ctx.send.assert_called_once()
        call_args = mock_ctx.send.call_args[0][0]
        self.assertIn("Party size must be between 1 and 5", call_args)

    async def test_theme_command_no_description(self):
        """!theme handles themes without description."""
        mock_ctx = MagicMock()
        mock_ctx.send = AsyncMock()
        
        with patch.object(core, 'get_theme_suggestion') as mock_suggestion:
            mock_suggestion.return_value = {
                'theme': 'Test',
                'description': '',
                'heroes': 'Hero (1)',
                'hero_count': 1
            }
            
            await bot.theme_command.callback(mock_ctx, party_size=1)
            call_args = mock_ctx.send.call_args[0][0]
            # Description should not appear in output
            self.assertNotIn("**Description:**", call_args)


class TestBotErrorHandling(unittest.IsolatedAsyncioTestCase):
    """Tests for bot error handling."""

    async def test_theme_command_handles_core_error(self):
        """!theme handles errors from core gracefully."""
        mock_ctx = MagicMock()
        mock_ctx.send = AsyncMock()
        
        with patch.object(core, 'get_theme_suggestion') as mock_suggestion:
            mock_suggestion.side_effect = Exception("Test error")
            
            await bot.theme_command.callback(mock_ctx, party_size=2)
            # Should have sent an error message
            mock_ctx.send.assert_called()


class TestBotCommandsRegistered(unittest.TestCase):
    """Tests that all expected commands are registered."""

    def test_theme_command_registered(self):
        """!theme command is registered."""
        self.assertIn('theme', bot.bot.commands)

    def test_themeroll_command_registered(self):
        """!themeroll command is registered."""
        self.assertIn('themeroll', bot.bot.commands)

    def test_tr_alias_registered(self):
        """!tr alias is registered."""
        # Check if 'tr' is an alias of themeroll
        self.assertIn('tr', bot.bot.commands)

    def test_helptheme_command_registered(self):
        """!helptheme command is registered."""
        self.assertIn('helptheme', bot.bot.commands)


if __name__ == "__main__":
    unittest.main()
