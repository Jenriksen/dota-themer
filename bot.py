"""
Dota Themer - Discord Bot
Provides theme suggestions via Discord commands.
"""

import os
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands, tasks

import core
import logging_config

# Get logger for this module
logger = logging_config.get_logger(logging_config.LOGGER_BOT)

# Configure bot
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Track theme suggestion messages for feedback
# Maps message_id to {"theme_name": str, "timestamp": datetime, "locked": bool}
theme_suggestion_messages = {}

# Track active modification threads
# Maps thread_id to {"theme_name": str, "user_id": int, "created_at": datetime, "message_id": int}
active_modification_threads = {}

# Track which message_ids have active modification threads
messages_with_active_threads = set()


@tasks.loop(seconds=60)  # Check every minute
async def cleanup_task():
    """Clean up inactive modification threads after 10 minutes of inactivity."""
    current_time = datetime.now(timezone.utc)
    inactive_threads = []

    for thread_id, thread_info in active_modification_threads.items():
        # Check if thread is older than 10 minutes
        time_elapsed = current_time - thread_info["created_at"]
        if time_elapsed >= timedelta(minutes=10):
            inactive_threads.append(thread_id)

    # Remove inactive threads from tracking and archive Discord threads
    for thread_id in inactive_threads:
        thread_info = active_modification_threads[thread_id]
        message_id = thread_info.get("message_id")
        if message_id in messages_with_active_threads:
            messages_with_active_threads.remove(message_id)

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

        del active_modification_threads[thread_id]


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

    # Start background task for thread cleanup
    cleanup_task.start()


@bot.event
async def on_reaction_add(reaction, user):
    """Handle reactions to theme suggestion messages.

    Note: The bot's own reactions (👍, 👎) on theme messages are explicitly
    excluded from being counted as votes to prevent inflation of feedback scores.
    """
    # Don't count the bot's own reactions as votes
    if user == bot.user:
        return

    # Only handle reactions on our own messages
    if reaction.message.author != bot.user:
        return

    # Check if this is a theme suggestion message
    message_id = reaction.message.id
    if message_id not in theme_suggestion_messages:
        return

    message_info = theme_suggestion_messages[message_id]
    theme_name = message_info["theme_name"]

    # Handle question mark reaction - start modification thread
    if str(reaction.emoji) == "❓":
        # Check if theme message is locked (2+ hours old)
        if message_info.get("locked", False):
            return

        time_elapsed = datetime.now(timezone.utc) - message_info["timestamp"]
        if time_elapsed >= timedelta(hours=2):
            # Lock the voting and modification
            message_info["locked"] = True
            try:
                await reaction.message.add_reaction("🔒")
            except Exception:
                pass
            return

        # Check if there's already an active modification thread for this message
        message_has_active_thread = message_id in messages_with_active_threads

        if message_has_active_thread:
            # Just remove the ❓ reaction - clicking again will restart
            try:
                await reaction.message.clear_reaction("❓")
            except Exception as e:
                logger.warning(f"Failed to clear ❓ reaction: {e}")
            return

        # Remove ❓ and add ✅
        try:
            await reaction.message.clear_reaction("❓")
            await reaction.message.add_reaction("✅")
        except Exception as e:
            logger.warning(f"Failed to update reactions: {e}")
            return

        # Create thread and post instructions
        try:
            thread = await reaction.message.create_thread(name=f"Modify: {theme_name}")

            # Get theme details for instructions
            try:
                themes = core.load_themes(include_hidden=True)
                theme = next(t for t in themes if t["name"] == theme_name)
                heroes_list = ", ".join(
                    sorted(
                        [
                            h["name"]
                            for h in core.get_heroes_by_ids(
                                theme["hero_ids"], core.load_heroes()
                            )
                        ]
                    )
                )
            except Exception:
                heroes_list = "Unknown"

            # Post instructions in thread
            instructions = f"""
**Theme:** {theme_name}
**Current Heroes:** {heroes_list}

To modify this theme, reply with:
- "Add HeroName" to add a hero
- "Remove HeroName" to remove a hero
- "+HeroName" or "+ HeroName" to add
- "-HeroName" or "- HeroName" to remove

Examples:
- "Add Anti Mage"
- "Remove Bloodseeker"
- "+PA"
- "-BS"

Type "Done", "Cancel", "Exit", or "Quit" to finish.
"""
            await thread.send(instructions)

            # Track the active modification thread
            active_modification_threads[thread.id] = {
                "theme_name": theme_name,
                "user_id": user.id,
                "created_at": datetime.now(timezone.utc),
                "message_id": message_id,
            }
            messages_with_active_threads.add(message_id)

            logger.info(
                f"Started modification thread for theme '{theme_name}' by {user}"
            )

        except Exception as e:
            logger.warning(f"Failed to create modification thread: {e}")
            # Try to add ✅ back if thread creation failed
            try:
                await reaction.message.add_reaction("❓")
            except Exception:
                pass

        return

    # Check if voting is locked (2 hours have passed)
    if message_info["locked"]:
        return

    # Check if 2 hours have passed since message was created
    time_elapsed = datetime.now(timezone.utc) - message_info["timestamp"]
    if time_elapsed >= timedelta(hours=2):
        # Lock the voting
        message_info["locked"] = True
        try:
            await reaction.message.add_reaction("🔒")
        except Exception:
            pass  # Lock emoji might already be added
        return

    # Handle thumbs up (👍) and thumbs down (👎) reactions
    if str(reaction.emoji) == "👍":
        delta = 1
    elif str(reaction.emoji) == "👎":
        delta = -1
    else:
        # Ignore other reactions
        return

    logger.info(
        f"Feedback reaction from {user}: {reaction.emoji} on theme '{theme_name}'"
    )

    # Update the feedback score
    success, message = core.update_theme_feedback(theme_name, delta)

    if success:
        logger.info(f"Feedback updated: {message}")
    else:
        logger.warning(f"Failed to update feedback: {message}")


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
    if message_id not in theme_suggestion_messages:
        return

    message_info = theme_suggestion_messages[message_id]

    # Check if voting is locked
    if message_info["locked"]:
        return

    # Check if 2 hours have passed
    time_elapsed = datetime.now(timezone.utc) - message_info["timestamp"]
    if time_elapsed >= timedelta(hours=2):
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
    success, message = core.update_theme_feedback(theme_name, delta)

    if success:
        logger.info(f"Feedback updated: {message}")
    else:
        logger.warning(f"Failed to update feedback: {message}")


@bot.event
async def on_message(message):
    """Handle messages in active modification threads for natural language theme modification."""
    # Ignore the bot's own messages
    if message.author == bot.user:
        return

    # Check if this message is in an active modification thread
    if message.channel.type != discord.ChannelType.public_thread:
        return

    thread_id = message.channel.id
    if thread_id not in active_modification_threads:
        return

    thread_info = active_modification_threads[thread_id]
    theme_name = thread_info["theme_name"]

    # Get the message content
    content = message.content.strip()

    # Check for exit commands
    if content.lower() in ["done", "cancel", "exit", "quit"]:
        try:
            await message.channel.send("✅ Theme modification session ended.")

            # Archive the Discord thread
            try:
                await message.channel.archive()
                logger.info(f"Archived modification thread: {thread_id}")
            except Exception as e:
                logger.warning(f"Failed to archive thread {thread_id}: {e}")

            # Remove thread from tracking
            thread_info = active_modification_threads.get(thread_id, {})
            message_id_to_clean = thread_info.get("message_id")
            if message_id_to_clean in messages_with_active_threads:
                messages_with_active_threads.remove(message_id_to_clean)
            del active_modification_threads[thread_id]

            # Re-add ❓ reaction to the original message if it exists
            try:
                original_message = await message.channel.fetch_message(
                    message.channel.parent_id
                )
                if original_message.id in theme_suggestion_messages:
                    # Remove ✅ and re-add ❓
                    try:
                        await original_message.clear_reaction("✅")
                        await original_message.add_reaction("❓")
                    except Exception as e:
                        logger.warning(f"Failed to restore ❓ reaction: {e}")
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"Failed to end modification session: {e}")
        return

    # Parse the command
    action = None
    hero_names = []

    # Check for +/prefixes without space
    if content.startswith("+"):
        action = "add"
        hero_part = content[1:].strip()
    elif content.startswith("-"):
        action = "remove"
        hero_part = content[1:].strip()
    elif content.lower().startswith("add"):
        action = "add"
        hero_part = content[3:].strip()
    elif content.lower().startswith("remove"):
        action = "remove"
        hero_part = content[6:].strip()

    if action is None:
        await message.channel.send(
            "❌ Invalid command. Use 'Add', 'Remove', '+', or '-' followed by hero names."
        )
        return

    # Parse hero names from the remaining part
    # Simple quoted string handling
    hero_names = []
    current = ""
    in_quotes = False
    for char in hero_part:
        if char == '"':
            in_quotes = not in_quotes
        elif char == " " and not in_quotes:
            if current:
                hero_names.append(current)
                current = ""
        else:
            current += char
    if current:
        hero_names.append(current)

    # If no quotes were used, fall back to simple split
    if not any('"' in s for s in hero_names) and '"' not in hero_part:
        hero_names = hero_part.split()

    # Convert hero names/aliases to IDs
    hero_ids = []
    invalid_heroes = []
    all_heroes = core.load_heroes()

    for name in hero_names:
        # Try exact match (case-insensitive)
        matched = False
        name_lower = name.lower()

        # Check all heroes for match
        best_match = None
        best_score = 0  # Higher is better

        for hero in all_heroes:
            hero_name_lower = hero["name"].lower()
            hero_id = hero["id"]

            # Check exact match on name
            if hero_name_lower == name_lower:
                hero_ids.append(hero["id"])
                matched = True
                break

            # Check aliases
            aliases = hero.get("aliases", [])
            for alias in aliases:
                if alias.lower() == name_lower:
                    hero_ids.append(hero["id"])
                    matched = True
                    break
            if matched:
                break

            # Simple fuzzy matching: count matching characters
            # Score based on: exact matches, prefix matches, substring matches
            score = 0

            # Check if one string contains the other
            if name_lower in hero_name_lower or hero_name_lower in name_lower:
                score = len(name_lower) * 2
            else:
                # Count matching characters in sequence
                min_len = min(len(name_lower), len(hero_name_lower))
                for i in range(min_len):
                    if name_lower[i] == hero_name_lower[i]:
                        score += 2
                    else:
                        break

                # Also check aliases
                for alias in aliases:
                    alias_lower = alias.lower()
                    if name_lower in alias_lower or alias_lower in name_lower:
                        score = max(score, len(name_lower) * 2)
                    else:
                        for i in range(min(len(name_lower), len(alias_lower))):
                            if name_lower[i] == alias_lower[i]:
                                score += 2
                            else:
                                break

            if score > best_score:
                best_score = score
                best_match = hero["id"]

        if not matched and best_match and best_score >= len(name_lower):
            hero_ids.append(best_match)
            matched = True

        if not matched:
            invalid_heroes.append(name)

    if invalid_heroes:
        await message.channel.send(
            f"⚠️ Invalid hero names: {', '.join(invalid_heroes)}. "
            f"Type a valid hero name or alias."
        )
        return

    # Apply the modification
    if action == "add":
        success, message_text = core.update_theme(theme_name, add_hero_ids=hero_ids)
    else:  # remove
        success, message_text = core.update_theme(theme_name, remove_hero_ids=hero_ids)

    if success:
        # Update the original theme message
        try:
            original_message = await message.channel.fetch_message(
                message.channel.parent_id
            )
            if original_message.id in theme_suggestion_messages:
                # Re-fetch theme and rebuild the message
                new_suggestion = core.get_theme_suggestion(2)  # Re-fetch for that theme
                # Actually we need to fetch the specific theme
                themes = core.load_themes(include_hidden=True)
                theme = next(t for t in themes if t["name"] == theme_name)
                matching_heroes = core.get_heroes_by_ids(theme["hero_ids"], all_heroes)
                matching_heroes.sort(key=lambda h: h["name"])

                new_response = f"**Theme:** {theme['name']}"
                if theme.get("description"):
                    new_response += f"\n**Description:** {theme['description']}"
                new_response += (
                    f"\n**Heroes:** {core.format_hero_list(matching_heroes)}"
                )
                new_response += f"\n**Feedback:** {theme.get('feedback_score', 0)} 👍👎"
                new_response += f"\n*({len(matching_heroes)} heroes match this theme)*"
                new_response += f"\n\nReact with 👍 to upvote this theme, or 👎 to downvote it! (Voting locks after 2 hours)"

                await original_message.edit(content=new_response)
        except Exception as e:
            logger.warning(f"Failed to update original message: {e}")

        await message.channel.send(f"✅ {message_text}")
        logger.info(
            f"Theme '{theme_name}' modified by {message.author}: {action} {hero_names}"
        )
    else:
        await message.channel.send(f"❌ {message_text}")
        logger.warning(
            f"Failed to modify theme '{theme_name}' for {message.author}: {message_text}"
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
    response += f"\n**Feedback:** {suggestion['feedback_score']} 👍👎"
    response += f"\n*({suggestion['hero_count']} heroes match this theme)*"
    response += f"\n\nReact with 👍 to upvote this theme, or 👎 to downvote it! (Voting locks after 2 hours)"

    sent_message = await ctx.send(response)

    # Store the message_id with metadata for reaction handling
    theme_suggestion_messages[sent_message.id] = {
        "theme_name": suggestion["theme"],
        "timestamp": datetime.now(timezone.utc),
        "locked": False,
    }

    # Add bot's own reactions to make it easier for users
    # Note: Bot's own reactions are explicitly excluded in on_reaction_add
    try:
        await sent_message.add_reaction("👍")
        await sent_message.add_reaction("👎")
        await sent_message.add_reaction("❓")
    except Exception as e:
        logger.warning(f"Failed to add reactions to message: {e}")
        # Clean up tracking if reactions couldn't be added
        theme_suggestion_messages.pop(sent_message.id, None)


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
    name="updatetheme",
    help="Update a theme (add/remove heroes) or open interactive modification",
)
async def update_theme_command(ctx, theme_name: str, action: str = None, *args):
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

    # If no action provided, open interactive modification thread
    if action is None:
        # Check if this is a reply to a theme suggestion message
        replied_message = ctx.message.reference
        if replied_message and replied_message.message_id in theme_suggestion_messages:
            message_info = theme_suggestion_messages[replied_message.message_id]
            theme_name = message_info["theme_name"]

        # Get theme details for instructions
        try:
            themes = core.load_themes(include_hidden=True)
            theme = next(t for t in themes if t["name"] == theme_name)
            heroes_list = ", ".join(
                sorted(
                    [
                        h["name"]
                        for h in core.get_heroes_by_ids(
                            theme["hero_ids"], core.load_heroes()
                        )
                    ]
                )
            )
        except Exception:
            heroes_list = "Unknown"

        # Create thread and post instructions
        try:
            thread = await ctx.message.create_thread(name=f"Modify: {theme_name}")

            instructions = f"""
**Theme:** {theme_name}
**Current Heroes:** {heroes_list}

To modify this theme, reply with:
- "Add HeroName" to add a hero
- "Remove HeroName" to remove a hero
- "+HeroName" or "+ HeroName" to add
- "-HeroName" or "- HeroName" to remove

Examples:
- "Add Anti Mage"
- "Remove Bloodseeker"
- "+PA"
- "-BS"

Type "Done", "Cancel", "Exit", or "Quit" to finish.
"""
            await thread.send(instructions)

            # Track the active modification thread
            active_modification_threads[thread.id] = {
                "theme_name": theme_name,
                "user_id": ctx.author.id,
                "created_at": datetime.now(timezone.utc),
                "message_id": ctx.message.id,
            }
            messages_with_active_threads.add(ctx.message.id)

            # Add ✅ reaction to original message if it's from the bot
            if (
                ctx.message.reference
                and ctx.message.reference.message_id in theme_suggestion_messages
            ):
                try:
                    message = await ctx.fetch_message(ctx.message.reference.message_id)
                    await message.clear_reaction("❓")
                    await message.add_reaction("✅")
                except Exception as e:
                    logger.warning(f"Failed to update reactions: {e}")

            logger.info(
                f"Started modification thread for theme '{theme_name}' by {ctx.author}"
            )
            return
        except Exception as e:
            logger.warning(f"Failed to create modification thread: {e}")
            await ctx.send(f"❌ Failed to create modification thread: {str(e)}")
            return

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
