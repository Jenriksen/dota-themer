"""
Dota Themer - Presentation layer

Renders Discord message text for theme suggestions and modification
threads. Extracted from bot.py (R4a) so the message format lives in
one place and can be tested without discord.py.
"""

UP_VOTE = "\U0001f44d"
DOWN_VOTE = "\U0001f44e"


def render_theme_suggestion(
    theme_name, description, heroes_display, hero_count, feedback_score
):
    """Render the theme suggestion message shown in Discord.

    Args:
        theme_name: Display name of the theme
        description: Theme description (line omitted when empty)
        heroes_display: Pre-formatted hero list (e.g. "Axe (3), Zeus (2)")
        hero_count: Number of matching heroes
        feedback_score: Current feedback score

    Returns:
        str: The full message text
    """
    lines = [f"**Theme:** {theme_name}"]
    if description:
        lines.append(f"**Description:** {description}")
    lines.append(f"**Heroes:** {heroes_display}")
    lines.append(f"**Feedback:** {feedback_score} {UP_VOTE}{DOWN_VOTE}")
    lines.append(f"*({hero_count} heroes match this theme)*")
    lines.append("")
    lines.append(
        f"React with {UP_VOTE} to upvote this theme, or {DOWN_VOTE} to downvote it!"
        " (Voting locks after 2 hours)"
    )
    return "\n".join(lines)


def render_modification_instructions(theme_name, heroes_list):
    """Render the how-to message posted in a modification thread.

    Args:
        theme_name: Display name of the theme being modified
        heroes_list: Comma-separated hero display names (may be "Unknown")

    Returns:
        str: The full instructions text
    """
    return f"""**Theme:** {theme_name}
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

Type "Done", "Cancel", "Exit", or "Quit" to finish."""
