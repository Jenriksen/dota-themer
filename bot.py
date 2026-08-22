"""
Dota Themer - Discord Bot
Provides theme suggestions via Discord commands.
"""

import discord
import os
from discord.ext import commands

import core
import logging_config

# Get logger for this module
logger = logging_config.get_logger(logging_config.LOGGER_BOT)

# Configure bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    """Called when the bot connects to Discord."""
    logger.info(f"Discord bot logged in as {bot.user.name} (ID: {bot.user.id})")
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("------")


@bot.command(name="theme", help="Get a theme suggestion for hero selection")
async def theme_command(ctx, party_size: int = 2):
    """
    Get a theme suggestion.
    
    Usage:
    !theme - Default party size of 2
    !theme 3 - For a party of 3 players
    
    Args:
        party_size: Number of players (1-5)
    """
    if party_size < 1 or party_size > 5:
        await ctx.send("Party size must be between 1 and 5.")
        return

    suggestion = core.get_theme_suggestion(party_size)
    
    # Format the response
    response = f"**Theme:** {suggestion['theme']}"
    if suggestion["description"]:
        response += f"\n**Description:** {suggestion['description']}"
    response += f"\n**Heroes:** {suggestion['heroes']}"
    response += f"\n*({suggestion['hero_count']} heroes match this theme)*"
    
    await ctx.send(response)


@bot.command(name="themeroll", aliases=["tr"], help="Get a new theme suggestion (alias for !theme)")
async def themeroll_command(ctx, party_size: int = 2):
    """Alias for !theme command."""
    await theme_command.callback(ctx, party_size=party_size)


@bot.command(name="helptheme", help="Show help for theme commands")
async def help_theme_command(ctx):
    """Show help information."""
    help_text = """
    **Dota Themer Bot Commands:**
    
    `!theme [party_size]` - Get a theme suggestion (default: 2 players)
    `!tr [party_size]` - Same as !theme (short alias)
    
    **Examples:**
    `!theme` - Theme for 2 players
    `!theme 3` - Theme for 3 players
    `!tr 5` - Theme for full 5-player party
    
    **Party Sizes:** 1-5 players
    """
    await ctx.send(help_text)


@theme_command.error
async def theme_error_handler(ctx, error):
    """Handle errors in theme command."""
    logger.error(f"Error in theme command from {ctx.author}: {error}", extra={
        "error_type": type(error).__name__,
        "user_id": ctx.author.id
    })
    
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: `!theme [party_size]` - Party size is optional (default: 2)")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Party size must be a number between 1 and 5.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")


if __name__ == "__main__":
    # Setup logging from environment
    logging_config.setup_logging_from_env()
    
    logger.info("Starting Dota Themer Discord bot")
    
    # Load token from environment variable
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        logger.error("DISCORD_TOKEN environment variable not set")
        print("Error: DISCORD_TOKEN environment variable not set.")
        print("Set it with: export DISCORD_TOKEN='your-token-here'")
        exit(1)
    
    logger.info("Discord token loaded, starting bot")
    print("Starting Dota Themer bot...")
    bot.run(token)
