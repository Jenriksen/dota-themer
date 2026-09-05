"""
Dota Themer - Discord Bot
Provides theme suggestions via Discord commands.
"""

import os

import discord
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

    # Set bot status to show help command
    await bot.change_presence(
        activity=discord.Game(name="Type !helptheme to get started")
    )


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


@bot.command(
    name="themeroll",
    aliases=["tr"],
    help="Get a new theme suggestion (alias for !theme)",
)
async def themeroll_command(ctx, party_size: int = 2):
    """Alias for !theme command."""
    await theme_command.callback(ctx, party_size=party_size)


@bot.command(name="helptheme", help="Show help for theme commands")
async def help_theme_command(ctx):
    """Show help information."""
    help_text = """
    **Dota Themer Bot Commands:**
    
    **Theme Suggestions:**
    `!theme [party_size]` - Get a theme suggestion (default: 2 players)
    `!tr [party_size]` - Same as !theme (short alias)
    
    **Theme Management:**
    `!addtheme <name> [description] <hero1> [hero2] ...` - Create a new theme
    `!updatetheme <name> add <hero1> [hero2] ...` - Add heroes to a theme
    `!updatetheme <name> remove <hero1> [hero2] ...` - Remove heroes from a theme
    `!hidetheme <name>` - Hide a theme from suggestions (can be restored)
    `!unhidetheme <name>` - Make a hidden theme visible again
    `!listthemes` - List all available themes (includes hidden themes)
    `!listheroes` - List all available heroes
    
    **Examples:**
    `!theme` - Theme for 2 players
    `!theme 3` - Theme for 3 players
    `!tr 5` - Theme for full 5-player party
    `!addtheme "My Custom Theme" "A test theme" antimage juggernaut` - Create a new theme
    `!updatetheme "Red Heroes" add crystal_maiden` - Add a hero to an existing theme
    `!updatetheme "Red Heroes" remove bloodseeker` - Remove a hero from an existing theme
    `!hidetheme "My Custom Theme"` - Hide from suggestions
    `!unhidetheme "My Custom Theme"` - Show in suggestions again
    
    **Party Sizes:** 1-5 players
    """
    await ctx.send(help_text)


@theme_command.error
async def theme_error_handler(ctx, error):
    """Handle errors in theme command."""
    logger.error(
        f"Error in theme command from {ctx.author}: {error}",
        extra={"error_type": type(error).__name__, "user_id": ctx.author.id},
    )

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            "Usage: `!theme [party_size]` - Party size is optional (default: 2)"
        )
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Party size must be a number between 1 and 5.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")


# Theme Management Commands


@bot.command(name="addtheme", help="Create a new theme")
async def add_theme_command(ctx, theme_name: str, *args):
    """
    Create a new theme.

    Usage:
    !addtheme <name> [description] <hero1> [hero2] ...

    The first argument is the theme name, the second (optional) is the description,
    and all remaining arguments are hero names or IDs.

    Example:
    !addtheme "My Theme" "My description" antimage juggernaut
    !addtheme "Strength Heroes" axe bristleback centaur
    """
    logger.info(f"Add theme command from {ctx.author}: {theme_name}")

    # Parse arguments
    description = ""
    hero_names = []

    if len(args) >= 1:
        # Check if the first arg looks like a description (has spaces or is quoted)
        # For simplicity, we'll treat the first arg as description if it doesn't match a hero
        hero_name_to_id = core.get_all_hero_names()

        # If first arg is not a hero, it's the description
        if args[0].lower() not in hero_name_to_id:
            description = args[0]
            hero_names = list(args[1:])
        else:
            hero_names = list(args)

    # Convert hero names to IDs
    hero_name_to_id = core.get_all_hero_names()
    hero_ids = []
    invalid_heroes = []

    for name in hero_names:
        # Try exact match first (by name)
        hero_id = hero_name_to_id.get(name.lower())
        if hero_id:
            hero_ids.append(hero_id)
        else:
            # Try as direct ID
            try:
                heroes = core.load_heroes()
                valid_ids = {h["id"] for h in heroes}
                if name in valid_ids:
                    hero_ids.append(name)
                else:
                    invalid_heroes.append(name)
            except Exception:
                invalid_heroes.append(name)

    if invalid_heroes:
        await ctx.send(
            f"⚠️ Invalid hero names/IDs: {', '.join(invalid_heroes)}. "
            f"Valid heroes: {', '.join(sorted(hero_name_to_id.keys())[:10])}..."
        )
        return

    # Add the theme
    success, message = core.add_theme(theme_name, description, hero_ids)

    if success:
        logger.info(f"Theme added by {ctx.author}: {theme_name}")
        await ctx.send(f"✅ {message}")
    else:
        logger.warning(f"Failed to add theme for {ctx.author}: {message}")
        await ctx.send(f"❌ {message}")


@bot.command(name="hidetheme", help="Hide a theme from suggestions")
async def hide_theme_command(ctx, theme_name: str):
    """
    Hide a theme (it will no longer appear in suggestions but can be restored).

    Usage:
    !hidetheme <name>

    Example:
    !hidetheme "My Theme"
    """
    logger.info(f"Hide theme command from {ctx.author}: {theme_name}")

    success, message = core.hide_theme(theme_name)

    if success:
        logger.info(f"Theme hidden by {ctx.author}: {theme_name}")
        await ctx.send(f"✅ {message}")
    else:
        logger.warning(f"Failed to hide theme for {ctx.author}: {message}")
        await ctx.send(f"❌ {message}")


@bot.command(name="unhidetheme", help="Make a hidden theme visible again")
async def unhide_theme_command(ctx, theme_name: str):
    """
    Unhide a theme (it will appear in suggestions again).

    Usage:
    !unhidetheme <name>

    Example:
    !unhidetheme "My Theme"
    """
    logger.info(f"Unhide theme command from {ctx.author}: {theme_name}")

    success, message = core.unhide_theme(theme_name)

    if success:
        logger.info(f"Theme unhidden by {ctx.author}: {theme_name}")
        await ctx.send(f"✅ {message}")
    else:
        logger.warning(f"Failed to unhide theme for {ctx.author}: {message}")
        await ctx.send(f"❌ {message}")


@bot.command(
    name="updatetheme", help="Update a theme (add/remove heroes or change description)"
)
async def update_theme_command(ctx, theme_name: str, action: str, *args):
    """
    Update an existing theme.

    Usage:
    !updatetheme <name> add <hero1> [hero2] ... - Add heroes to theme
    !updatetheme <name> remove <hero1> [hero2] ... - Remove heroes from theme

    Example:
    !updatetheme "Red Heroes" add crystal_maiden
    !updatetheme "Red Heroes" remove bloodseeker
    """
    logger.info(f"Update theme command from {ctx.author}: {theme_name} {action} {args}")

    action = action.lower()

    if action not in ["add", "remove"]:
        await ctx.send(
            f"❌ Invalid action: '{action}'. Use 'add' or 'remove'."
            f"\nExample: `!updatetheme ThemeName add hero1 hero2`"
        )
        return

    # Convert hero names to IDs
    hero_name_to_id = core.get_all_hero_names()
    hero_ids = []
    invalid_heroes = []

    for name in args:
        hero_id = hero_name_to_id.get(name.lower())
        if hero_id:
            hero_ids.append(hero_id)
        else:
            try:
                heroes = core.load_heroes()
                valid_ids = {h["id"] for h in heroes}
                if name in valid_ids:
                    hero_ids.append(name)
                else:
                    invalid_heroes.append(name)
            except Exception:
                invalid_heroes.append(name)

    if invalid_heroes:
        await ctx.send(
            f"⚠️ Invalid hero names/IDs: {', '.join(invalid_heroes)}. "
            f"Valid heroes: {', '.join(sorted(hero_name_to_id.keys())[:10])}..."
        )
        return

    # Update the theme
    if action == "add":
        success, message = core.update_theme(theme_name, add_hero_ids=hero_ids)
    else:  # remove
        success, message = core.update_theme(theme_name, remove_hero_ids=hero_ids)

    if success:
        logger.info(f"Theme updated by {ctx.author}: {theme_name}")
        await ctx.send(f"✅ {message}")
    else:
        logger.warning(f"Failed to update theme for {ctx.author}: {message}")
        await ctx.send(f"❌ {message}")


@bot.command(name="listthemes", help="List all available themes")
async def list_themes_command(ctx):
    """List all available themes with hidden status."""
    logger.info(f"List themes command from {ctx.author}")

    themes = core.get_all_themes_with_status()

    if not themes:
        await ctx.send("❌ No themes found.")
        return

    # Paginate the response (Discord has a 2000 character limit)
    chunks = []
    current_chunk = "**Available Themes:**\n"

    for i, theme in enumerate(themes, 1):
        hidden_marker = " (hidden)" if theme["is_hidden"] else ""
        line = f"{i}. {theme['name']}{hidden_marker}\n"
        if len(current_chunk + line) > 1800:  # Leave room for more
            chunks.append(current_chunk)
            current_chunk = ""
        current_chunk += line

    if current_chunk:
        chunks.append(current_chunk)

    for chunk in chunks:
        await ctx.send(chunk)


@bot.command(name="listheroes", help="List all available heroes")
async def list_heroes_command(ctx):
    """List all available heroes."""
    logger.info(f"List heroes command from {ctx.author}")

    try:
        heroes = core.load_heroes()
        hero_list = sorted([h["name"] for h in heroes])
    except Exception as e:
        logger.error(f"Failed to load heroes: {e}")
        await ctx.send(f"❌ Failed to load heroes: {str(e)}")
        return

    # Paginate the response
    chunks = []
    current_chunk = "**Available Heroes:**\n"

    for i, name in enumerate(hero_list, 1):
        line = f"{i}. {name}\n"
        if len(current_chunk + line) > 1800:
            chunks.append(current_chunk)
            current_chunk = ""
        current_chunk += line

    if current_chunk:
        chunks.append(current_chunk)

    for chunk in chunks:
        await ctx.send(chunk)


if __name__ == "__main__":
    # Setup logging from environment
    logging_config.setup_logging_from_env()

    logger.info("Starting Dota Themer Discord bot")

    # Load token from environment variable
    token = os.getenv("DISCORD_TOKEN")

    if not token:
        logger.error("DISCORD_TOKEN environment variable not set")
        print("Error: DISCORD_TOKEN environment variable not set.")
        print("Set it with: export DISCORD_TOKEN='your-token-here' (bash)")
        print("       or: $env:DISCORD_TOKEN='your-token-here' (PowerShell)")
        exit(1)

    logger.info("Discord token loaded, starting bot")
    print("Starting Dota Themer bot...")
    bot.run(token)
