"""
Dota Themer - Discord Bot
Provides theme suggestions via Discord commands.
"""

import os
from datetime import timedelta
from typing import Optional

import discord
from discord.ext import commands, tasks

import __version__
import core
import logging_config
import presentation
import session_state
import snapshot
import storage
import thread_commands

# Get logger for this module
logger = logging_config.get_logger(logging_config.LOGGER_BOT)

# Repository singletons: load data once per process, cache reads,
# invalidate the theme cache on save (R1d). Backend is selected via
# DOTA_THEMER_BACKEND=json|sqlite (#34); S3 snapshot push/pull is
# enabled by DOTA_THEMER_S3_BUCKET.
_snapshot_config = storage.build_snapshot_config()
if _snapshot_config is not None:
    snapshot.pull_snapshot(_snapshot_config.db_path, _snapshot_config)
_hero_repo, _theme_repo = storage.create_repositories(core.DATA_DIR)


def _maybe_wrap_snapshots(repo):
    """Push an S3 snapshot after every theme save when S3 is configured."""
    if _snapshot_config is None:
        return repo
    return storage.SnapshottingThemeRepository(
        repo,
        on_save=lambda themes: snapshot.push_snapshot(
            _snapshot_config.db_path, _snapshot_config
        ),
    )


HERO_REPO = core.CachedHeroRepository(_hero_repo)
THEME_REPO = core.CachedThemeRepository(_maybe_wrap_snapshots(_theme_repo))
HERO_RESOLVER = core.HeroResolver(HERO_REPO)

# Session state: theme suggestions and active modification threads (R5a)
SESSION_STATE = session_state.SessionState()
VOTE_LOCK_POLICY = session_state.VoteLockPolicy()

# Configure bot
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)


@tasks.loop(seconds=60)  # Check every minute
async def cleanup_task():
    """Clean up inactive modification threads after 10 minutes of inactivity."""
    inactive_threads = SESSION_STATE.inactive_threads(cutoff=timedelta(minutes=10))

    # Remove inactive threads from tracking and archive Discord threads
    for thread_id in inactive_threads:

        # Archive the Discord thread
        try:
            thread_channel = bot.get_channel(thread_id)
            if thread_channel and hasattr(thread_channel, "archive"):
                await thread_channel.archive()
                logger.info(f"Archived inactive modification thread: {thread_id}")
            else:
                logger.warning(f"Could not find thread channel {thread_id} to archive")
        except Exception as e:
            logger.warning(f"Failed to archive thread {thread_id}: {e}")

        SESSION_STATE.remove_thread(thread_id)


@bot.event
async def on_ready():
    """Called when the bot connects to Discord."""
    logger.info(f"Dota Themer v{__version__.__version__} started")
    logger.info(f"Discord bot logged in as {bot.user.name} (ID: {bot.user.id})")
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print(f"Dota Themer v{__version__.__version__}")
    print("------")

    # Set bot status to show help command
    await bot.change_presence(
        activity=discord.Game(name="Type !helptheme to get started")
    )

    # Start background task for thread cleanup
    cleanup_task.start()


@bot.event
async def on_reaction_add(reaction, user):
    """Handle reactions to theme suggestion messages.

    The bot's own reactions on theme messages are explicitly excluded from
    being counted as votes to prevent inflation of feedback scores.
    """
    if user == bot.user:
        return
    if reaction.message.author != bot.user:
        return

    message_info = SESSION_STATE.get_suggestion(message_id=reaction.message.id)
    if message_info is None:
        return

    emoji = str(reaction.emoji)
    if emoji == "\U00002753":
        await handle_question_mark_reaction(reaction, user, message_info)
        return
    if emoji in (presentation.UP_VOTE, presentation.DOWN_VOTE):
        await handle_vote_reaction(reaction, user, message_info, emoji)


async def handle_question_mark_reaction(reaction, user, message_info):
    """Start a modification thread when a user reacts with a question mark."""
    message_id = reaction.message.id
    decision = VOTE_LOCK_POLICY.evaluate(SESSION_STATE, message_id=message_id)
    if not decision.allowed:
        if decision.should_lock:
            SESSION_STATE.lock_suggestion(message_id)
            await add_lock_reaction(reaction)
        return

    if SESSION_STATE.message_has_active_thread(message_id):
        await clear_reaction_ignoring_errors(reaction, "\U00002753")
        return

    try:
        await reaction.message.clear_reaction("\U00002753")
        await reaction.message.add_reaction("\U00002705")
    except Exception as e:
        logger.warning(f"Failed to update reactions: {e}")
        return

    await start_modification_thread(reaction, user, message_info)


async def start_modification_thread(reaction, user, message_info):
    """Create the modification thread, post instructions, and track it."""
    theme_name = message_info["theme_name"]
    message_id = reaction.message.id
    try:
        thread = await reaction.message.create_thread(name=f"Modify: {theme_name}")
        heroes_list = build_heroes_list_text(theme_name)
        instructions = presentation.render_modification_instructions(
            theme_name=theme_name, heroes_list=heroes_list
        )
        await thread.send(instructions)
        SESSION_STATE.register_thread(
            thread_id=thread.id,
            theme_name=theme_name,
            user_id=user.id,
            message_id=message_id,
        )
        logger.info(f"Started modification thread for theme '{theme_name}' by {user}")
    except Exception as e:
        logger.warning(f"Failed to create modification thread: {e}")
        await add_reaction_ignoring_errors(reaction, "\U00002753")


async def clear_reaction_ignoring_errors(reaction, emoji):
    """Clear a reaction, logging failures without raising."""
    try:
        await reaction.message.clear_reaction(emoji)
    except Exception as e:
        logger.warning(f"Failed to clear {emoji} reaction: {e}")


async def add_reaction_ignoring_errors(reaction, emoji):
    """Add a reaction, ignoring failures."""
    try:
        await reaction.message.add_reaction(emoji)
    except Exception:
        pass


async def handle_vote_reaction(reaction, user, message_info, emoji):
    """Apply a thumbs-up/down vote to the theme's feedback score."""
    message_id = reaction.message.id
    decision = VOTE_LOCK_POLICY.evaluate(SESSION_STATE, message_id=message_id)
    if not decision.allowed:
        if decision.should_lock:
            SESSION_STATE.lock_suggestion(message_id)
            await add_lock_reaction(reaction)
        return

    theme_name = message_info["theme_name"]
    delta = 1 if emoji == presentation.UP_VOTE else -1
    logger.info(
        f"Feedback reaction from {user}: {reaction.emoji} on theme '{theme_name}'"
    )
    try:
        message = core.update_theme_feedback(theme_name, delta, theme_repo=THEME_REPO)
        logger.info(f"Feedback updated: {message}")
    except core.ThemeError as e:
        logger.warning(f"Failed to update feedback: {e}")


async def add_lock_reaction(reaction):
    """Add the lock emoji, ignoring an already-added reaction."""
    try:
        await reaction.message.add_reaction("\U0001f512")
    except Exception:
        pass


def build_heroes_list_text(theme_name):
    """Comma-join the current hero names of a theme, or 'Unknown' on failure."""
    try:
        themes = THEME_REPO.load_themes(include_hidden=True)
        theme = next(t for t in themes if t["name"] == theme_name)
        return ", ".join(
            sorted(
                [
                    h["name"]
                    for h in core.get_heroes_by_ids(
                        theme["hero_ids"], HERO_REPO.load_heroes()
                    )
                ]
            )
        )
    except Exception:
        return "Unknown"


@bot.event
async def on_reaction_remove(reaction, user):
    """Handle removal of reactions from theme suggestion messages.

    When a user removes their 👍 or 👎 reaction, decrement the feedback score.
    """
    # Don't process the bot's own reactions
    if user == bot.user:
        return

    # Only handle reactions on our own messages
    if reaction.message.author != bot.user:
        return

    # Check if this is a theme suggestion message
    message_id = reaction.message.id
    message_info = SESSION_STATE.get_suggestion(message_id=message_id)
    if message_info is None:
        return

    decision = VOTE_LOCK_POLICY.evaluate(SESSION_STATE, message_id=message_id)
    if not decision.allowed:
        return

    theme_name = message_info["theme_name"]

    # Handle removal of thumbs up (👍) and thumbs down (👎) reactions
    if str(reaction.emoji) == "👍":
        delta = -1  # Removing upvote = -1
    elif str(reaction.emoji) == "👎":
        delta = 1  # Removing downvote = +1
    else:
        # Ignore other reactions
        return

    logger.info(
        f"Feedback reaction removed by {user}: {reaction.emoji} on theme '{theme_name}'"
    )

    # Update the feedback score
    try:
        message = core.update_theme_feedback(theme_name, delta, theme_repo=THEME_REPO)
        logger.info(f"Feedback updated: {message}")
    except core.ThemeError as e:
        logger.warning(f"Failed to update feedback: {e}")


@bot.event
async def on_message(message):
    """Handle messages in active modification threads for natural language theme modification."""
    if message.author == bot.user:
        return

    is_command = message.content.startswith(bot.command_prefix)
    is_thread_message = message.channel.type == discord.ChannelType.public_thread
    in_active_thread = is_thread_message and SESSION_STATE.has_thread(
        message.channel.id
    )

    if is_command or not in_active_thread:
        await bot.process_commands(message)
        return

    thread_id = message.channel.id
    thread_info = SESSION_STATE.get_thread(thread_id=thread_id)
    theme_name = thread_info["theme_name"]
    content = message.content.strip()

    if thread_commands.is_exit_command(content):
        await end_modification_session(message, thread_id)
        return

    parsed = thread_commands.parse_modification(content)
    if parsed is None:
        await message.channel.send(
            "\u274c Invalid command. Use 'Add', 'Remove', '+', or '-' followed by hero names."
        )
        return

    hero_ids, invalid_heroes = HERO_RESOLVER.resolve_all(parsed.hero_names)
    if invalid_heroes:
        await message.channel.send(
            f"\u26a0\ufe0f Invalid hero names: {', '.join(invalid_heroes)}. "
            f"Type a valid hero name or alias."
        )
        return

    try:
        if parsed.action == "add":
            message_text = core.update_theme(
                theme_name, add_hero_ids=hero_ids, theme_repo=THEME_REPO
            )
        else:
            message_text = core.update_theme(
                theme_name, remove_hero_ids=hero_ids, theme_repo=THEME_REPO
            )
    except core.ThemeError as e:
        await message.channel.send(f"\u274c {e}")
        return

    await refresh_original_suggestion(message, theme_name)
    await message.channel.send(f"\u2705 {message_text}")
    logger.info(
        f"Theme '{theme_name}' modified by {message.author}: "
        f"{parsed.action} {parsed.hero_names}"
    )


async def end_modification_session(message, thread_id):
    """End a modification session: confirm, archive, restore reactions."""
    try:
        await message.channel.send("\u2705 Theme modification session ended.")
        try:
            await message.channel.archive()
            logger.info(f"Archived modification thread: {thread_id}")
        except Exception as e:
            logger.warning(f"Failed to archive thread {thread_id}: {e}")

        SESSION_STATE.remove_thread(thread_id)

        try:
            original_message = await message.channel.fetch_message(
                message.channel.parent_id
            )
            if SESSION_STATE.has_suggestion(original_message.id):
                try:
                    await original_message.clear_reaction("\u2705")
                    await original_message.add_reaction("\u2753")
                except Exception as e:
                    logger.warning(f"Failed to restore \u2753 reaction: {e}")
        except Exception:
            pass
    except Exception as e:
        logger.warning(f"Failed to end modification session: {e}")


async def refresh_original_suggestion(message, theme_name):
    """Re-render the original theme suggestion after a modification."""
    try:
        original_message = await message.channel.fetch_message(
            message.channel.parent_id
        )
        if SESSION_STATE.has_suggestion(original_message.id):
            themes = THEME_REPO.load_themes(include_hidden=True)
            theme = next(t for t in themes if t["name"] == theme_name)
            matching_heroes = core.get_heroes_by_ids(
                theme["hero_ids"], HERO_REPO.load_heroes()
            )
            matching_heroes.sort(key=lambda h: h["name"])
            new_response = presentation.render_theme_suggestion(
                theme_name=theme["name"],
                description=theme.get("description", ""),
                heroes_display=core.format_hero_list(matching_heroes),
                hero_count=len(matching_heroes),
                feedback_score=theme.get("feedback_score", 0),
            )
            await original_message.edit(content=new_response)
    except Exception as e:
        logger.warning(f"Failed to update original message: {e}")


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

    suggestion = core.get_theme_suggestion(
        party_size, hero_repo=HERO_REPO, theme_repo=THEME_REPO
    )

    response = presentation.render_theme_suggestion(
        theme_name=suggestion["theme"],
        description=suggestion["description"],
        heroes_display=suggestion["heroes"],
        hero_count=suggestion["hero_count"],
        feedback_score=suggestion["feedback_score"],
    )

    sent_message = await ctx.send(response)

    # Store the message_id with metadata for reaction handling
    SESSION_STATE.register_suggestion(
        message_id=sent_message.id, theme_name=suggestion["theme"]
    )

    # Add bot's own reactions to make it easier for users
    # Note: Bot's own reactions are explicitly excluded in on_reaction_add
    try:
        await sent_message.add_reaction("👍")
        await sent_message.add_reaction("👎")
        await sent_message.add_reaction("❓")
    except Exception as e:
        logger.warning(f"Failed to add reactions to message: {e}")
        # Clean up tracking if reactions couldn't be added
        SESSION_STATE.remove_suggestion(sent_message.id)


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
    React with 👍 to upvote or 👎 to downvote a theme suggestion
    
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
    
    **Feedback:**
    React with 👍 to upvote a theme or 👎 to downvote it
    
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
        await ctx.send("""
            Usage: `!theme [party_size]` - Party size is optional (default: 2)
            For additional help, use `!helptheme` to see all commands and usage.
            """)
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

    # Load hero names once; a load failure must not silently reclassify args
    try:
        HERO_RESOLVER.resolve("")
    except Exception as e:
        logger.error(f"Failed to load heroes for addtheme: {e}")
        await ctx.send("❌ Failed to load hero data. Please try again later.")
        return

    # Parse arguments
    description = ""
    hero_names = []

    if len(args) >= 1:
        # If first arg is not a hero, it's the description
        if HERO_RESOLVER.resolve(args[0]) is None:
            description = args[0]
            hero_names = list(args[1:])
        else:
            hero_names = list(args)

    # Convert hero names to IDs
    hero_ids, invalid_heroes = HERO_RESOLVER.resolve_all(hero_names)

    if invalid_heroes:
        await ctx.send(
            f"⚠️ Invalid hero names/IDs: {', '.join(invalid_heroes)}. "
            f"Valid heroes: {', '.join(sorted(h['name'].lower() for h in HERO_RESOLVER._load_heroes())[:10])}..."
        )
        return

    # Add the theme
    try:
        message = core.add_theme(
            theme_name, description, hero_ids, theme_repo=THEME_REPO
        )
        logger.info(f"Theme added by {ctx.author}: {theme_name}")
        await ctx.send(f"✅ {message}")
    except core.ThemeError as e:
        logger.warning(f"Failed to add theme for {ctx.author}: {e}")
        await ctx.send(f"❌ {e}")


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

    try:
        message = core.hide_theme(theme_name, theme_repo=THEME_REPO)
        logger.info(f"Theme hidden by {ctx.author}: {theme_name}")
        await ctx.send(f"✅ {message}")
    except core.ThemeError as e:
        logger.warning(f"Failed to hide theme for {ctx.author}: {e}")
        await ctx.send(f"❌ {e}")


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

    try:
        message = core.unhide_theme(theme_name, theme_repo=THEME_REPO)
        logger.info(f"Theme unhidden by {ctx.author}: {theme_name}")
        await ctx.send(f"✅ {message}")
    except core.ThemeError as e:
        logger.warning(f"Failed to unhide theme for {ctx.author}: {e}")
        await ctx.send(f"❌ {e}")


@bot.command(
    name="updatetheme",
    help="Update an existing theme or open interactive modification",
)
async def update_theme_command(
    ctx, theme_name: str, action: Optional[str] = None, *args
):
    """
    Update an existing theme or open interactive modification.

    Usage:
    !updatetheme <name> - Open interactive modification thread
    !updatetheme <name> add <hero1> [hero2] ... - Add heroes to theme
    !updatetheme <name> remove <hero1> [hero2] ... - Remove heroes from theme

    Example:
    !updatetheme "Red Heroes" - Opens thread for interactive modification
    !updatetheme "Red Heroes" add crystal_maiden
    !updatetheme "Red Heroes" remove bloodseeker
    """
    logger.info(f"Update theme command from {ctx.author}: {theme_name} {action} {args}")

    if action is None:
        await open_interactive_modification(ctx, theme_name)
        return

    await apply_direct_theme_update(ctx, theme_name, action.lower(), list(args))


async def open_interactive_modification(ctx, theme_name):
    """Open an interactive modification thread for the theme."""
    replied_message = ctx.message.reference
    if replied_message and SESSION_STATE.has_suggestion(replied_message.message_id):
        message_info = SESSION_STATE.get_suggestion(
            message_id=replied_message.message_id
        )
        if message_info is not None:
            theme_name = message_info["theme_name"]

    heroes_list = build_heroes_list_text(theme_name)

    try:
        thread = await ctx.message.create_thread(name=f"Modify: {theme_name}")
        instructions = presentation.render_modification_instructions(
            theme_name=theme_name, heroes_list=heroes_list
        )
        await thread.send(instructions)
        SESSION_STATE.register_thread(
            thread_id=thread.id,
            theme_name=theme_name,
            user_id=ctx.author.id,
            message_id=ctx.message.id,
        )
        await mark_thread_started_on_original(ctx)
        logger.info(
            f"Started modification thread for theme '{theme_name}' by {ctx.author}"
        )
    except Exception as e:
        logger.warning(f"Failed to create modification thread: {e}")
        await ctx.send(f"\u274c Failed to create modification thread: {str(e)}")


async def mark_thread_started_on_original(ctx):
    """Swap the question-mark reaction for a check mark on the original message."""
    if not (
        ctx.message.reference
        and SESSION_STATE.has_suggestion(ctx.message.reference.message_id)
    ):
        return
    try:
        message = await ctx.fetch_message(ctx.message.reference.message_id)
        await message.clear_reaction("\u2753")
        await message.add_reaction("\u2705")
    except Exception as e:
        logger.warning(f"Failed to update reactions: {e}")


async def apply_direct_theme_update(ctx, theme_name, action, hero_name_args):
    """Apply a direct !updatetheme <name> add/remove <heroes> update."""
    if action not in ("add", "remove"):
        await ctx.send(
            f"\u274c Invalid action: '{action}'. Use 'add' or 'remove'."
            f"\nExample: `!updatetheme ThemeName add hero1 hero2`"
        )
        return

    try:
        HERO_RESOLVER.resolve("")
    except Exception as e:
        logger.error(f"Failed to load heroes for updatetheme: {e}")
        await ctx.send("\u274c Failed to load hero data. Please try again later.")
        return
    hero_ids, invalid_heroes = HERO_RESOLVER.resolve_all(hero_name_args)
    if invalid_heroes:
        await ctx.send(
            f"\u26a0\ufe0f Invalid hero names/IDs: {', '.join(invalid_heroes)}. "
            f"Valid heroes: {', '.join(sorted(h['name'].lower() for h in HERO_RESOLVER._load_heroes())[:10])}..."
        )
        return

    try:
        if action == "add":
            message = core.update_theme(
                theme_name, add_hero_ids=hero_ids, theme_repo=THEME_REPO
            )
        else:
            message = core.update_theme(
                theme_name, remove_hero_ids=hero_ids, theme_repo=THEME_REPO
            )
        logger.info(f"Theme updated by {ctx.author}: {theme_name}")
        await ctx.send(f"\u2705 {message}")
    except core.ThemeError as e:
        logger.warning(f"Failed to update theme for {ctx.author}: {e}")
        await ctx.send(f"\u274c {e}")


@bot.command(name="listthemes", help="List all available themes")
async def list_themes_command(ctx):
    """List all available themes with hidden status."""
    logger.info(f"List themes command from {ctx.author}")

    try:
        themes = core.get_all_themes_with_status(theme_repo=THEME_REPO)
    except Exception as e:
        logger.error(f"Failed to load themes for listthemes: {e}")
        await ctx.send("❌ Failed to load theme data. Please try again later.")
        return

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
        heroes = HERO_REPO.load_heroes()
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

    logger.info(f"Starting Dota Themer v{__version__.__version__} Discord bot")

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
