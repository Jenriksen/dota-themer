"""
Dota Themer - Core functionality
Suggests a theme and lists matching heroes with their positions.
"""

import json
import random
import sys
from itertools import combinations
from pathlib import Path

import logging_config

# Get logger for this module
logger = logging_config.get_logger(logging_config.LOGGER_CORE)

# Load data files
DATA_DIR = Path(__file__).parent / "data"

# Lane-position mapping (from CONTEXT.md)
SAFELANE_POSITIONS = {1, 5}  # Carry + Hard Support
MID_POSITIONS = {2}  # Midlaner
OFFLANE_POSITIONS = {3, 4}  # Offlaner + Soft Support

# Lane names for display
LANE_NAMES = {1: "Safelane", 2: "Mid", 3: "Offlane", 4: "Offlane", 5: "Safelane"}


def load_heroes():
    """Load heroes from JSON file."""
    logger.debug("Loading heroes from heroes.json")
    try:
        with open(DATA_DIR / "heroes.json", "r") as f:
            heroes = json.load(f)
        logger.info(f"Loaded {len(heroes)} heroes")
        return heroes
    except FileNotFoundError as e:
        logger.error(f"Heroes file not found: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in heroes file: {e}")
        raise


def load_themes():
    """Load themes from JSON file."""
    logger.debug("Loading themes from themes.json")
    try:
        with open(DATA_DIR / "themes.json", "r") as f:
            themes = json.load(f)
        logger.info(f"Loaded {len(themes)} themes")
        return themes
    except FileNotFoundError as e:
        logger.error(f"Themes file not found: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in themes file: {e}")
        raise


def get_heroes_by_ids(hero_ids, all_heroes):
    """Get hero objects for a list of hero IDs."""
    hero_map = {h["id"]: h for h in all_heroes}
    return [hero_map[hid] for hid in hero_ids if hid in hero_map]


def get_positions_display(positions):
    """
    Convert a list of positions to a display string.

    Args:
        positions: List of position integers (1-5)

    Returns:
        str: Comma-separated sorted positions (e.g., "1,2,3")
    """
    return ",".join(map(str, sorted(positions)))


def format_hero_list(heroes):
    """Format a list of heroes with their positions in parentheses."""
    return ", ".join(
        f"{h['name']} ({get_positions_display(h['positions'])})" for h in heroes
    )


def has_position_coverage(heroes, positions_needed={1, 2, 3, 4, 5}):
    """
    Check if a set of heroes has coverage across the needed positions.

    Args:
        heroes: List of hero dicts with 'positions' field
        positions_needed: Set of positions that need coverage

    Returns:
        bool: True if all needed positions are covered by at least one hero
    """
    covered_positions = set()
    for hero in heroes:
        covered_positions.update(hero["positions"])
    return positions_needed.issubset(covered_positions)


def get_theme_hero_count(theme, all_heroes):
    """
    Get the number of valid heroes for a theme.

    Args:
        theme: Theme dict with 'hero_ids' field
        all_heroes: List of all hero dicts

    Returns:
        int: Number of valid heroes matching this theme
    """
    matching_heroes = get_heroes_by_ids(theme["hero_ids"], all_heroes)
    return len(matching_heroes)


def filter_themes(
    themes,
    all_heroes,
    party_size=None,
    min_heroes=None,
    require_position_coverage=False,
):
    """
    Filter themes based on criteria.

    Args:
        themes: List of theme dicts
        all_heroes: List of all hero dicts
        party_size: If provided, filter themes with at least this many heroes
        min_heroes: Minimum number of heroes required (overrides party_size)
        require_position_coverage: If True, filter themes with full position coverage

    Returns:
        list: Filtered list of theme dicts
    """
    filtered = []
    for theme in themes:
        matching_heroes = get_heroes_by_ids(theme["hero_ids"], all_heroes)
        hero_count = len(matching_heroes)

        # Filter by minimum hero count
        required_min = min_heroes if min_heroes is not None else party_size
        # Only apply filtering if required_min is a valid positive integer
        if (
            required_min is not None
            and isinstance(required_min, int)
            and required_min > 0
        ):
            if hero_count < required_min:
                continue

        # Filter by position coverage
        if require_position_coverage and not has_position_coverage(matching_heroes):
            continue

        filtered.append(theme)

    return filtered


def select_theme(
    themes, heroes, party_size=None, use_weighted=False, require_position_coverage=False
):
    """
    Select a theme.

    Args:
        themes: List of theme dicts
        heroes: List of all hero dicts
        party_size: Optional party size for filtering
        use_weighted: If True, use weighted random selection (favors themes with more heroes)
        require_position_coverage: If True, only select themes with full position coverage

    Returns:
        dict: Selected theme

    Raises:
        ValueError: If no themes match the criteria
    """
    logger.debug(
        f"Filtering {len(themes)} themes",
        extra={
            "party_size": party_size,
            "require_position_coverage": require_position_coverage,
        },
    )

    # Filter themes first
    filtered_themes = filter_themes(
        themes,
        heroes,
        party_size=party_size,
        require_position_coverage=require_position_coverage,
    )

    if not filtered_themes:
        logger.warning("No themes matched filter criteria, falling back to all themes")
        # Fall back to all themes if filtering removed everything
        filtered_themes = themes

    logger.debug(f"Selecting from {len(filtered_themes)} filtered themes")

    if use_weighted:
        # Weighted selection: themes with more heroes have higher probability
        weights = [get_theme_hero_count(t, heroes) for t in filtered_themes]
        selected = random.choices(filtered_themes, weights=weights, k=1)[0]
        logger.debug(
            f"Weighted selection chose theme with {get_theme_hero_count(selected, heroes)} heroes"
        )
        return selected
    else:
        return random.choice(filtered_themes)


def get_lane_for_position(position):
    """
    Get the lane name for a given position (1-5).

    Args:
        position: Position number (1-5)

    Returns:
        str: Lane name ("Safelane", "Mid", or "Offlane")
    """
    return LANE_NAMES.get(position, "Unknown")


def group_heroes_by_lane(heroes):
    """
    Group heroes by their lane assignments.

    Args:
        heroes: List of hero dicts with 'positions' field

    Returns:
        dict: {lane_name: [heroes]} with lanes as keys
    """
    lanes = {"Safelane": [], "Mid": [], "Offlane": []}
    for hero in heroes:
        for position in hero["positions"]:
            lane = get_lane_for_position(position)
            if lane in lanes and hero not in lanes[lane]:
                lanes[lane].append(hero)
    return lanes


def format_lane_grouping(heroes):
    """
    Format heroes grouped by lane for display.

    Args:
        heroes: List of hero dicts

    Returns:
        str: Formatted string with heroes grouped by lane
    """
    lanes = group_heroes_by_lane(heroes)
    parts = []
    for lane, lane_heroes in sorted(lanes.items()):
        if lane_heroes:
            hero_names = [
                h["name"] for h in sorted(lane_heroes, key=lambda h: h["name"])
            ]
            parts.append(f"{lane}: {', '.join(hero_names)}")
    return "; ".join(parts)


def get_party_configurations(party_size):
    """
    Get valid lane configurations for a given party size.

    Based on CONTEXT.md:
    - Party of 2: safelane(2) OR offlane(2)
    - Party of 3: safelane(2) + mid(1) OR offlane(2) + mid(1)
    - Party of 4: safelane(2) + offlane(2)
    - Party of 5: safelane(2) + mid(1) + offlane(2)

    Args:
        party_size: Number of players (1-5)

    Returns:
        list: List of dict with lane assignments, e.g.
              [{"Safelane": 2, "Mid": 0, "Offlane": 0}, ...]
    """
    configs = []

    if party_size == 1:
        # Single player can go anywhere
        configs = [
            {"Safelane": 1, "Mid": 0, "Offlane": 0},
            {"Safelane": 0, "Mid": 1, "Offlane": 0},
            {"Safelane": 0, "Mid": 0, "Offlane": 1},
        ]
    elif party_size == 2:
        # Two players: safelane pair OR offlane pair
        configs = [
            {"Safelane": 2, "Mid": 0, "Offlane": 0},
            {"Safelane": 0, "Mid": 0, "Offlane": 2},
        ]
    elif party_size == 3:
        # Three players: safelane pair + mid OR offlane pair + mid
        configs = [
            {"Safelane": 2, "Mid": 1, "Offlane": 0},
            {"Safelane": 0, "Mid": 1, "Offlane": 2},
        ]
    elif party_size == 4:
        # Four players: safelane pair + offlane pair
        configs = [
            {"Safelane": 2, "Mid": 0, "Offlane": 2},
        ]
    elif party_size == 5:
        # Five players: safelane(2) + mid(1) + offlane(2)
        configs = [
            {"Safelane": 2, "Mid": 1, "Offlane": 2},
        ]

    return configs


def validate_party_composition(heroes, party_size):
    """
    Validate if a set of heroes can form a valid party composition.

    Checks if there are enough heroes for each lane in at least one
    valid configuration for the party size.

    Args:
        heroes: List of hero dicts with 'positions' field
        party_size: Number of players (1-5)

    Returns:
        tuple: (bool, str) - (is_valid, reason)
    """
    if len(heroes) < party_size:
        return (False, f"Not enough heroes: {len(heroes)} < {party_size}")

    configs = get_party_configurations(party_size)

    for config in configs:
        # Check if we can assign heroes to satisfy this configuration
        safelane_heroes = [
            h for h in heroes if SAFELANE_POSITIONS.intersection(set(h["positions"]))
        ]
        mid_heroes = [
            h for h in heroes if MID_POSITIONS.intersection(set(h["positions"]))
        ]
        offlane_heroes = [
            h for h in heroes if OFFLANE_POSITIONS.intersection(set(h["positions"]))
        ]

        if (
            config["Safelane"] <= len(safelane_heroes)
            and config["Mid"] <= len(mid_heroes)
            and config["Offlane"] <= len(offlane_heroes)
        ):
            return (True, f"Valid configuration: {config}")

    return (False, "No valid lane configuration found")


def suggest_balanced_team(heroes, party_size):
    """
    Suggest a balanced team composition from a set of heroes.

    Tries to select heroes that fit a valid lane configuration.

    Args:
        heroes: List of hero dicts
        party_size: Number of players (1-5)

    Returns:
        dict: {"heroes": [selected_heroes], "configuration": config, "by_lane": {lane: [heroes]}}
              or None if no valid composition found
    """
    if len(heroes) < party_size:
        return None

    configs = get_party_configurations(party_size)

    for config in configs:
        result = _try_configuration(heroes, config)
        if result:
            return result

    return None


def _try_configuration(heroes, config):
    """
    Try to select heroes that fit a specific lane configuration.

    Args:
        heroes: List of hero dicts
        config: Dict with lane counts, e.g., {"Safelane": 2, "Mid": 1, "Offlane": 0}

    Returns:
        dict or None: Result with selected heroes and lane grouping
    """
    # Categorize heroes by which lanes they can play
    safelane_heroes = [
        h for h in heroes if SAFELANE_POSITIONS.intersection(set(h["positions"]))
    ]
    mid_heroes = [h for h in heroes if MID_POSITIONS.intersection(set(h["positions"]))]
    offlane_heroes = [
        h for h in heroes if OFFLANE_POSITIONS.intersection(set(h["positions"]))
    ]

    # Check if we have enough heroes for each lane
    if (
        config["Safelane"] > len(safelane_heroes)
        or config["Mid"] > len(mid_heroes)
        or config["Offlane"] > len(offlane_heroes)
    ):
        return None

    # Select heroes for each lane
    selected = []
    remaining = list(heroes)

    # Safelane heroes
    for _ in range(config["Safelane"]):
        for h in safelane_heroes:
            if h in remaining:
                selected.append(h)
                remaining.remove(h)
                break

    # Mid heroes
    for _ in range(config["Mid"]):
        for h in mid_heroes:
            if h in remaining:
                selected.append(h)
                remaining.remove(h)
                break

    # Offlane heroes
    for _ in range(config["Offlane"]):
        for h in offlane_heroes:
            if h in remaining:
                selected.append(h)
                remaining.remove(h)
                break

    if len(selected) == sum(config.values()):
        # Group by lane for display
        by_lane = group_heroes_by_lane(selected)
        return {"heroes": selected, "configuration": config, "by_lane": by_lane}

    return None


def get_theme_suggestion(
    party_size=2, use_weighted=False, require_position_coverage=False
):
    """
    Get a theme suggestion for a given party size.

    Args:
        party_size: Number of players (1-5)
        use_weighted: If True, use weighted random selection (favors themes with more heroes)
        require_position_coverage: If True, only select themes with heroes in all positions 1-5

    Returns:
        dict: {"theme": theme_name, "description": theme_desc, "heroes": formatted_hero_list, "hero_count": int}
    """
    logger.info(
        f"Generating theme suggestion for party size {party_size}",
        extra={
            "use_weighted": use_weighted,
            "require_position_coverage": require_position_coverage,
        },
    )

    heroes = load_heroes()
    themes = load_themes()

    # Select a theme with filtering and weighting options
    theme = select_theme(
        themes,
        heroes,
        party_size=party_size,
        use_weighted=use_weighted,
        require_position_coverage=require_position_coverage,
    )

    logger.debug(f"Selected theme: {theme['name']}")

    # Get matching heroes
    matching_heroes = get_heroes_by_ids(theme["hero_ids"], heroes)

    # Sort heroes by name for consistent output
    matching_heroes.sort(key=lambda h: h["name"])

    logger.info(
        f"Found {len(matching_heroes)} matching heroes for theme '{theme['name']}'"
    )

    return {
        "theme": theme["name"],
        "description": theme.get("description", ""),
        "heroes": format_hero_list(matching_heroes),
        "hero_count": len(matching_heroes),
    }


def add_theme(theme_name, description="", hero_ids=None):
    """
    Add a new theme to themes.json.
    
    Args:
        theme_name: Name of the new theme
        description: Optional description of the theme
        hero_ids: List of hero IDs that match this theme
    
    Returns:
        tuple: (success: bool, message: str)
    """
    logger.info(f"Attempting to add theme: {theme_name}")
    
    if not theme_name or not theme_name.strip():
        logger.warning("Theme name cannot be empty")
        return False, "Theme name cannot be empty"
    
    theme_name = theme_name.strip()
    
    # Load existing themes
    try:
        themes = load_themes()
        heroes = load_heroes()
    except Exception as e:
        logger.error(f"Failed to load themes or heroes: {e}")
        return False, f"Failed to load data: {str(e)}"
    
    # Check if theme already exists
    for theme in themes:
        if theme["name"].lower() == theme_name.lower():
            logger.warning(f"Theme '{theme_name}' already exists")
            return False, f"Theme '{theme_name}' already exists"
    
    # Validate hero IDs if provided
    valid_hero_ids = {h["id"] for h in heroes}
    if hero_ids:
        # Filter out invalid hero IDs
        validated_hero_ids = [hid for hid in hero_ids if hid in valid_hero_ids]
        invalid_ids = set(hero_ids) - set(validated_hero_ids)
        
        if invalid_ids:
            logger.warning(f"Ignoring invalid hero IDs: {invalid_ids}")
            return False, f"Invalid hero IDs: {', '.join(sorted(invalid_ids))}. Valid IDs: {', '.join(sorted(valid_hero_ids)[:20])}..."
        
        # Remove duplicates
        validated_hero_ids = list(set(validated_hero_ids))
    else:
        validated_hero_ids = []
    
    # Create new theme
    new_theme = {
        "name": theme_name,
        "description": description.strip() if description else "",
        "hero_ids": validated_hero_ids
    }
    
    # Add to themes
    themes.append(new_theme)
    
    # Sort themes by name
    themes.sort(key=lambda t: t["name"])
    
    # Save back to file
    try:
        themes_path = DATA_DIR / "themes.json"
        with open(themes_path, "w") as f:
            json.dump(themes, f, indent=2)
        
        logger.info(f"Successfully added theme: {theme_name} with {len(validated_hero_ids)} heroes")
        return True, f"Theme '{theme_name}' added successfully with {len(validated_hero_ids)} heroes"
    except Exception as e:
        logger.error(f"Failed to save themes: {e}")
        return False, f"Failed to save theme: {str(e)}"


def update_theme(theme_name, add_hero_ids=None, remove_hero_ids=None, new_description=None):
    """
    Update an existing theme by adding/removing heroes or changing description.
    
    Args:
        theme_name: Name of the theme to update
        add_hero_ids: List of hero IDs to add to the theme
        remove_hero_ids: List of hero IDs to remove from the theme
        new_description: New description for the theme
    
    Returns:
        tuple: (success: bool, message: str)
    """
    logger.info(f"Attempting to update theme: {theme_name}")
    
    if not theme_name or not theme_name.strip():
        logger.warning("Theme name cannot be empty")
        return False, "Theme name cannot be empty"
    
    theme_name = theme_name.strip()
    
    # Load existing themes and heroes
    try:
        themes = load_themes()
        heroes = load_heroes()
    except Exception as e:
        logger.error(f"Failed to load themes or heroes: {e}")
        return False, f"Failed to load data: {str(e)}"
    
    # Find the theme to update
    theme_index = None
    for i, theme in enumerate(themes):
        if theme["name"].lower() == theme_name.lower():
            theme_index = i
            break
    
    if theme_index is None:
        logger.warning(f"Theme '{theme_name}' not found")
        return False, f"Theme '{theme_name}' not found. Available themes: {', '.join(sorted([t['name'] for t in themes])[:20])}..."
    
    # Get valid hero IDs
    valid_hero_ids = {h["id"] for h in heroes}
    theme = themes[theme_index]
    current_hero_ids = set(theme["hero_ids"])
    
    # Process additions
    if add_hero_ids:
        additions = set()
        for hid in add_hero_ids:
            if hid in valid_hero_ids:
                additions.add(hid)
            else:
                logger.warning(f"Ignoring invalid hero ID: {hid}")
        current_hero_ids.update(additions)
    
    # Process removals
    if remove_hero_ids:
        removals = set(remove_hero_ids) & current_hero_ids
        current_hero_ids.difference_update(removals)
    
    # Update description if provided
    if new_description is not None:
        theme["description"] = new_description.strip()
    
    # Update hero IDs
    theme["hero_ids"] = sorted(list(current_hero_ids))
    
    # Sort themes by name
    themes.sort(key=lambda t: t["name"])
    
    # Save back to file
    try:
        themes_path = DATA_DIR / "themes.json"
        with open(themes_path, "w") as f:
            json.dump(themes, f, indent=2)
        
        logger.info(f"Successfully updated theme: {theme_name}")
        return True, f"Theme '{theme_name}' updated successfully. Now has {len(current_hero_ids)} heroes"
    except Exception as e:
        logger.error(f"Failed to save themes: {e}")
        return False, f"Failed to save theme: {str(e)}"


def remove_theme(theme_name):
    """
    Remove a theme from themes.json.
    
    Args:
        theme_name: Name of the theme to remove
    
    Returns:
        tuple: (success: bool, message: str)
    """
    logger.info(f"Attempting to remove theme: {theme_name}")
    
    if not theme_name or not theme_name.strip():
        logger.warning("Theme name cannot be empty")
        return False, "Theme name cannot be empty"
    
    theme_name = theme_name.strip()
    
    # Load existing themes
    try:
        themes = load_themes()
    except Exception as e:
        logger.error(f"Failed to load themes: {e}")
        return False, f"Failed to load themes: {str(e)}"
    
    # Find and remove the theme
    theme_index = None
    for i, theme in enumerate(themes):
        if theme["name"].lower() == theme_name.lower():
            theme_index = i
            break
    
    if theme_index is None:
        logger.warning(f"Theme '{theme_name}' not found")
        return False, f"Theme '{theme_name}' not found. Available themes: {', '.join(sorted([t['name'] for t in themes])[:20])}..."
    
    # Remove the theme
    removed_theme = themes.pop(theme_index)
    
    # Sort themes by name
    themes.sort(key=lambda t: t["name"])
    
    # Save back to file
    try:
        themes_path = DATA_DIR / "themes.json"
        with open(themes_path, "w") as f:
            json.dump(themes, f, indent=2)
        
        logger.info(f"Successfully removed theme: {theme_name}")
        return True, f"Theme '{theme_name}' removed successfully"
    except Exception as e:
        logger.error(f"Failed to save themes: {e}")
        return False, f"Failed to save themes: {str(e)}"


def get_all_theme_names():
    """
    Get a list of all theme names.
    
    Returns:
        list: Sorted list of theme names
    """
    try:
        themes = load_themes()
        return sorted([t["name"] for t in themes])
    except Exception as e:
        logger.error(f"Failed to load themes: {e}")
        return []


def get_all_hero_names():
    """
    Get a list of all hero names with their IDs.
    
    Returns:
        dict: Mapping of hero name (lowercase) to hero ID
    """
    try:
        heroes = load_heroes()
        return {h["name"].lower(): h["id"] for h in heroes}
    except Exception as e:
        logger.error(f"Failed to load heroes: {e}")
        return {}


def main():
    """CLI interface for testing."""
    party_size = int(sys.argv[1]) if len(sys.argv) > 1 else 2

    if party_size < 1 or party_size > 5:
        print("Party size must be between 1 and 5.")
        sys.exit(1)

    suggestion = get_theme_suggestion(party_size)

    # Format output
    output = f"Theme: {suggestion['theme']}"
    if suggestion["description"]:
        output += f"\nDescription: {suggestion['description']}"
    output += f"\nHeroes: {suggestion['heroes']}"
    output += f"\n({suggestion['hero_count']} heroes match this theme)"

    print(output)


if __name__ == "__main__":
    main()
