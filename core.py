"""
Dota Themer - Core functionality
Suggests a theme and lists matching heroes with their positions.
"""

import json
import os
import random
import sys
import tempfile
from pathlib import Path
from typing import Protocol, runtime_checkable

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


class ThemeError(Exception):
    """Base class for all theme mutation errors."""


class EmptyThemeNameError(ThemeError):
    """Theme name was empty or whitespace."""


class ThemeAlreadyExistsError(ThemeError):
    """A theme with the same name already exists."""


class InvalidHeroIdsError(ThemeError):
    """One or more hero IDs do not exist in the hero data."""


class DuplicateHeroSetError(ThemeError):
    """Another theme already uses the exact same hero set."""


class ThemeNotFoundError(ThemeError):
    """No theme with the given name exists."""


class ThemeDataError(ThemeError):
    """The theme data could not be loaded or saved."""


@runtime_checkable
class HeroRepository(Protocol):
    """Interface for hero persistence."""

    def load_heroes(self):
        """Return the list of hero dicts."""


@runtime_checkable
class ThemeRepository(Protocol):
    """Interface for theme persistence."""

    def load_themes(self, include_hidden=True):
        """Return the list of theme dicts, optionally filtering hidden."""

    def save_themes(self, themes):
        """Persist the list of theme dicts."""


class CachedHeroRepository:
    """Hero repository wrapper that loads from the delegate once per process."""

    def __init__(self, delegate):
        self.delegate = delegate
        self._cache = None

    def load_heroes(self):
        if self._cache is None:
            self._cache = self.delegate.load_heroes()
        return self._cache


class CachedThemeRepository:
    """Theme repository wrapper that caches loads and invalidates on save."""

    def __init__(self, delegate):
        self.delegate = delegate
        self._cache = None

    def load_themes(self, include_hidden=True):
        if self._cache is None:
            self._cache = self.delegate.load_themes()
        if not include_hidden:
            return [t for t in self._cache if not t.get("is_hidden", False)]
        return self._cache

    def save_themes(self, themes):
        self._cache = None
        return self.delegate.save_themes(themes)


def _default_hero_repo():
    """Build the process-wide default hero repository (SQLite, #52).

    storage imports core, so the import is deferred to call time.
    """
    hero_repo, _ = _default_repositories()
    return hero_repo


def _default_theme_repo():
    """Build the process-wide default theme repository (SQLite, #52)."""
    _, theme_repo = _default_repositories()
    return theme_repo


def _default_repositories():
    """Build the default repository pair (SQLite, #52), migrating JSON once."""
    import storage

    return storage.create_repositories(DATA_DIR)


def load_heroes():
    """Load heroes via the default hero repository."""
    return _default_hero_repo().load_heroes()


def load_themes(include_hidden=True):
    """Load themes via the default theme repository."""
    return _default_theme_repo().load_themes(include_hidden=include_hidden)


def save_themes(themes):
    """Save themes via the default theme repository."""
    _default_theme_repo().save_themes(themes)


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
    include_hidden=True,
):
    """
    Filter themes based on criteria.

    Args:
        themes: List of theme dicts
        all_heroes: List of all hero dicts
        party_size: If provided, filter themes with at least this many heroes
        min_heroes: Minimum number of heroes required (overrides party_size)
        require_position_coverage: If True, filter themes with full position coverage
        include_hidden: If False, filter out themes with is_hidden=True

    Returns:
        list: Filtered list of theme dicts
    """
    filtered = []
    for theme in themes:
        # Skip hidden themes if requested
        if not include_hidden and theme.get("is_hidden", False):
            continue
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
        include_hidden=False,
    )

    if not filtered_themes:
        logger.warning("No themes matched filter criteria, falling back to all themes")
        # Fall back to all themes if filtering removed everything,
        # but never surface hidden themes via the fallback path
        filtered_themes = [t for t in themes if not t.get("is_hidden", False)]

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
    party_size=2,
    use_weighted=False,
    require_position_coverage=False,
    hero_repo=None,
    theme_repo=None,
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

    hero_repo = hero_repo or _default_hero_repo()
    theme_repo = theme_repo or _default_theme_repo()
    heroes = hero_repo.load_heroes()
    themes = theme_repo.load_themes(include_hidden=False)

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
        "feedback_score": theme.get("feedback_score", 0),
    }


def add_theme(
    theme_name, description="", hero_ids=None, hero_repo=None, theme_repo=None
):
    """
    Add a new theme via the theme repository.

    Args:
        theme_name: Name of the new theme
        description: Optional description of the theme
        hero_ids: List of hero IDs that match this theme
        hero_repo: Hero repository to read from (defaults to the file repository)
        theme_repo: Theme repository to read/write (defaults to the file repository)

    Returns:
        tuple: (success: bool, message: str)
    """
    hero_repo = hero_repo or _default_hero_repo()
    theme_repo = theme_repo or _default_theme_repo()
    logger.info(f"Attempting to add theme: {theme_name}")

    if not theme_name or not theme_name.strip():
        logger.warning("Theme name cannot be empty")
        raise EmptyThemeNameError("Theme name cannot be empty")

    theme_name = theme_name.strip()

    # Load existing themes (include hidden for duplicate checking)
    try:
        themes = theme_repo.load_themes(include_hidden=True)
        heroes = hero_repo.load_heroes()
    except Exception as e:
        logger.error(f"Failed to load themes or heroes: {e}")
        raise ThemeDataError(f"Failed to load data: {str(e)}") from e

    # Check if theme already exists
    for theme in themes:
        if theme["name"].lower() == theme_name.lower():
            logger.warning(f"Theme '{theme_name}' already exists")
            raise ThemeAlreadyExistsError(f"Theme '{theme_name}' already exists")

    # Validate hero IDs if provided
    valid_hero_ids = {h["id"] for h in heroes}
    if hero_ids:
        # Filter out invalid hero IDs
        validated_hero_ids = [hid for hid in hero_ids if hid in valid_hero_ids]
        invalid_ids = set(hero_ids) - set(validated_hero_ids)

        if invalid_ids:
            logger.warning(f"Ignoring invalid hero IDs: {invalid_ids}")
            raise InvalidHeroIdsError(
                f"Invalid hero IDs: {', '.join(sorted(invalid_ids))}. Valid IDs: {', '.join(sorted(valid_hero_ids)[:20])}..."
            )

        # Remove duplicates
        validated_hero_ids = sorted(set(validated_hero_ids))
    else:
        validated_hero_ids = []

    # Check for duplicate hero-set (identical sets would skew weighted
    # selection probabilities, see issue #5)
    if validated_hero_ids:
        new_hero_set = frozenset(validated_hero_ids)
        for theme in themes:
            if frozenset(theme["hero_ids"]) == new_hero_set:
                logger.warning(
                    f"Theme '{theme_name}' has same hero set as '{theme['name']}'"
                )
                raise DuplicateHeroSetError(
                    f"Hero set already used by theme '{theme['name']}'"
                )

    # Create new theme
    new_theme = {
        "name": theme_name,
        "description": description.strip() if description else "",
        "hero_ids": validated_hero_ids,
    }

    # Add to themes
    themes.append(new_theme)

    # Sort themes by name
    themes.sort(key=lambda t: t["name"])

    # Save back to the repository
    try:
        theme_repo.save_themes(themes)

        logger.info(
            f"Successfully added theme: {theme_name} with {len(validated_hero_ids)} heroes"
        )
        return f"Theme '{theme_name}' added successfully with {len(validated_hero_ids)} heroes"
    except Exception as e:
        logger.error(f"Failed to save themes: {e}")
        raise ThemeDataError(f"Failed to save theme: {str(e)}") from e


def update_theme(
    theme_name,
    add_hero_ids=None,
    remove_hero_ids=None,
    new_description=None,
    hero_repo=None,
    theme_repo=None,
):
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
    hero_repo = hero_repo or _default_hero_repo()
    theme_repo = theme_repo or _default_theme_repo()
    logger.info(f"Attempting to update theme: {theme_name}")

    if not theme_name or not theme_name.strip():
        logger.warning("Theme name cannot be empty")
        raise EmptyThemeNameError("Theme name cannot be empty")

    theme_name = theme_name.strip()

    # Load existing themes and heroes (include hidden)
    try:
        themes = theme_repo.load_themes(include_hidden=True)
        heroes = hero_repo.load_heroes()
    except Exception as e:
        logger.error(f"Failed to load themes or heroes: {e}")
        raise ThemeDataError(f"Failed to load data: {str(e)}") from e

    # Find the theme to update
    theme_index = None
    for i, theme in enumerate(themes):
        if theme["name"].lower() == theme_name.lower():
            theme_index = i
            break

    if theme_index is None:
        logger.warning(f"Theme '{theme_name}' not found")
        raise ThemeNotFoundError(
            f"Theme '{theme_name}' not found. Available themes: {', '.join(sorted([t['name'] for t in themes])[:20])}..."
        )

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
        theme_repo.save_themes(themes)

        logger.info(f"Successfully updated theme: {theme_name}")
        return f"Theme '{theme_name}' updated successfully. Now has {len(current_hero_ids)} heroes"
    except Exception as e:
        logger.error(f"Failed to save themes: {e}")
        raise ThemeDataError(f"Failed to save theme: {str(e)}") from e


def hide_theme(theme_name, theme_repo=None):
    """
    Hide a theme (mark as hidden so it doesn't appear in suggestions).

    Args:
        theme_name: Name of the theme to hide

    Returns:
        tuple: (success: bool, message: str)
    """
    theme_repo = theme_repo or _default_theme_repo()
    logger.info(f"Attempting to hide theme: {theme_name}")

    if not theme_name or not theme_name.strip():
        logger.warning("Theme name cannot be empty")
        raise EmptyThemeNameError("Theme name cannot be empty")

    theme_name = theme_name.strip()

    # Load existing themes
    try:
        themes = theme_repo.load_themes()
    except Exception as e:
        logger.error(f"Failed to load themes: {e}")
        raise ThemeDataError(f"Failed to load themes: {str(e)}") from e

    # Find the theme to hide
    theme_index = None
    for i, theme in enumerate(themes):
        if theme["name"].lower() == theme_name.lower():
            theme_index = i
            break

    if theme_index is None:
        logger.warning(f"Theme '{theme_name}' not found")
        raise ThemeNotFoundError(
            f"Theme '{theme_name}' not found. Available themes: {', '.join(sorted([t['name'] for t in themes])[:20])}..."
        )

    # Hide the theme
    themes[theme_index]["is_hidden"] = True

    # Sort themes by name
    themes.sort(key=lambda t: t["name"])

    # Save back to file
    try:
        theme_repo.save_themes(themes)

        logger.info(f"Successfully hid theme: {theme_name}")
        return f"Theme '{theme_name}' hidden successfully. It will no longer appear in suggestions."
    except Exception as e:
        logger.error(f"Failed to save themes: {e}")
        raise ThemeDataError(f"Failed to save theme: {str(e)}") from e


def unhide_theme(theme_name, theme_repo=None):
    """
    Unhide a theme (mark as visible so it appears in suggestions).

    Args:
        theme_name: Name of the theme to unhide

    Returns:
        tuple: (success: bool, message: str)
    """
    theme_repo = theme_repo or _default_theme_repo()
    logger.info(f"Attempting to unhide theme: {theme_name}")

    if not theme_name or not theme_name.strip():
        logger.warning("Theme name cannot be empty")
        raise EmptyThemeNameError("Theme name cannot be empty")

    theme_name = theme_name.strip()

    # Load existing themes (include hidden ones)
    try:
        themes = theme_repo.load_themes(include_hidden=True)
    except Exception as e:
        logger.error(f"Failed to load themes: {e}")
        raise ThemeDataError(f"Failed to load themes: {str(e)}") from e

    # Find the theme to unhide
    theme_index = None
    for i, theme in enumerate(themes):
        if theme["name"].lower() == theme_name.lower():
            theme_index = i
            break

    if theme_index is None:
        logger.warning(f"Theme '{theme_name}' not found")
        raise ThemeNotFoundError(
            f"Theme '{theme_name}' not found. Available themes: {', '.join(sorted([t['name'] for t in themes])[:20])}..."
        )

    # Check if theme is already visible
    if not themes[theme_index].get("is_hidden", False):
        logger.info(f"Theme '{theme_name}' is already visible")
        return f"Theme '{theme_name}' is already visible."

    # Unhide the theme
    themes[theme_index]["is_hidden"] = False

    # Sort themes by name
    themes.sort(key=lambda t: t["name"])

    # Save back to file
    try:
        theme_repo.save_themes(themes)

        logger.info(f"Successfully unhid theme: {theme_name}")
        return f"Theme '{theme_name}' unhidden successfully. It will now appear in suggestions."
    except Exception as e:
        logger.error(f"Failed to save themes: {e}")
        raise ThemeDataError(f"Failed to save theme: {str(e)}") from e


def update_theme_feedback(theme_name, delta, theme_repo=None):
    """
    Update the feedback score for a theme.

    Args:
        theme_name: Name of the theme to update
        delta: Amount to change the feedback score by (+1 for thumbsup, -1 for thumbsdown)

    Returns:
        tuple: (success: bool, message: str)
    """
    logger.info(f"Attempting to update feedback for theme: {theme_name} by {delta}")

    if not theme_name or not theme_name.strip():
        logger.warning("Theme name cannot be empty")
        raise EmptyThemeNameError("Theme name cannot be empty")

    theme_name = theme_name.strip()

    # Load existing themes
    try:
        themes = theme_repo.load_themes(include_hidden=True)
    except Exception as e:
        logger.error(f"Failed to load themes: {e}")
        raise ThemeDataError(f"Failed to load themes: {str(e)}") from e

    # Find the theme to update
    theme_index = None
    for i, theme in enumerate(themes):
        if theme["name"].lower() == theme_name.lower():
            theme_index = i
            break

    if theme_index is None:
        logger.warning(f"Theme '{theme_name}' not found")
        raise ThemeNotFoundError(f"Theme '{theme_name}' not found.")

    # Update feedback score
    themes[theme_index]["feedback_score"] = (
        themes[theme_index].get("feedback_score", 0) + delta
    )

    # Sort themes by name
    themes.sort(key=lambda t: t["name"])

    # Save back to file
    try:
        theme_repo.save_themes(themes)

        logger.info(f"Successfully updated feedback for theme: {theme_name}")
        return f"Theme '{theme_name}' feedback updated to {themes[theme_index]['feedback_score']}"
    except Exception as e:
        logger.error(f"Failed to save themes: {e}")
        raise ThemeDataError(f"Failed to save feedback: {str(e)}") from e


def remove_theme(theme_name, theme_repo=None):
    """
    Remove a theme from themes.json.

    Args:
        theme_name: Name of the theme to remove

    Returns:
        tuple: (success: bool, message: str)
    """
    theme_repo = theme_repo or _default_theme_repo()
    logger.info(f"Attempting to remove theme: {theme_name}")

    if not theme_name or not theme_name.strip():
        logger.warning("Theme name cannot be empty")
        raise EmptyThemeNameError("Theme name cannot be empty")

    theme_name = theme_name.strip()

    # Load existing themes (include hidden)
    try:
        themes = theme_repo.load_themes(include_hidden=True)
    except Exception as e:
        logger.error(f"Failed to load themes: {e}")
        raise ThemeDataError(f"Failed to load themes: {str(e)}") from e

    # Find and remove the theme
    theme_index = None
    for i, theme in enumerate(themes):
        if theme["name"].lower() == theme_name.lower():
            theme_index = i
            break

    if theme_index is None:
        logger.warning(f"Theme '{theme_name}' not found")
        raise ThemeNotFoundError(
            f"Theme '{theme_name}' not found. Available themes: {', '.join(sorted([t['name'] for t in themes])[:20])}..."
        )

    # Remove the theme
    removed_theme = themes.pop(theme_index)

    # Sort themes by name
    themes.sort(key=lambda t: t["name"])

    # Save back to file
    try:
        theme_repo.save_themes(themes)

        logger.info(f"Successfully removed theme: {theme_name}")
        return f"Theme '{theme_name}' removed successfully"
    except Exception as e:
        logger.error(f"Failed to save themes: {e}")
        raise ThemeDataError(f"Failed to save themes: {str(e)}") from e


class HeroResolver:
    """Single hero-name resolution service (R2a).

    One contract for every call site: exact ID, exact name
    (case-insensitive), alias (case-insensitive), then fuzzy scoring
    with the same threshold the modification-thread path used.
    """

    def __init__(self, hero_repo):
        self.hero_repo = hero_repo
        self._heroes = None

    def _load_heroes(self):
        if self._heroes is None:
            self._heroes = self.hero_repo.load_heroes()
        return self._heroes

    def resolve(self, name):
        """Resolve one hero name/ID/alias to a hero ID, or None."""
        if not name or not name.strip():
            return None
        name = name.strip()
        name_lower = name.lower()
        heroes = self._load_heroes()

        for hero in heroes:
            if hero["id"] == name:
                return hero["id"]

        best_match = None
        best_score = 0
        for hero in heroes:
            hero_name_lower = hero["name"].lower()
            aliases = hero.get("aliases", [])

            if hero_name_lower == name_lower:
                return hero["id"]
            for alias in aliases:
                if alias.lower() == name_lower:
                    return hero["id"]

            score = 0
            if name_lower in hero_name_lower or hero_name_lower in name_lower:
                score = len(name_lower) * 2
            else:
                min_len = min(len(name_lower), len(hero_name_lower))
                for i in range(min_len):
                    if name_lower[i] == hero_name_lower[i]:
                        score += 2
                    else:
                        break
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

        if best_match and best_score >= len(name_lower):
            return best_match
        return None

    def resolve_all(self, names):
        """Resolve a list of names; returns (hero_ids, invalid_names)."""
        hero_ids = []
        invalid = []
        for name in names:
            hero_id = self.resolve(name)
            if hero_id is None:
                invalid.append(name)
            else:
                hero_ids.append(hero_id)
        return hero_ids, invalid


def get_all_theme_names(include_hidden=True, theme_repo=None):
    """
    Get a list of all theme names.

    Args:
        include_hidden: If False, exclude hidden themes from the list

    Returns:
        list: Sorted list of theme names
    """
    theme_repo = theme_repo or _default_theme_repo()
    themes = theme_repo.load_themes(include_hidden=include_hidden)
    return sorted([t["name"] for t in themes])


def get_all_themes_with_status(theme_repo=None):
    """
    Get all themes with their hidden status.

    Returns:
        list: List of dicts with 'name' and 'is_hidden' for each theme
    """
    theme_repo = theme_repo or _default_theme_repo()
    themes = theme_repo.load_themes(include_hidden=True)
    return [{"name": t["name"], "is_hidden": t.get("is_hidden", False)} for t in themes]


def get_all_hero_names(hero_repo=None):
    """
    Get a list of all hero names with their IDs.

    Returns:
        dict: Mapping of hero name (lowercase) to hero ID
    """
    hero_repo = hero_repo or _default_hero_repo()
    heroes = hero_repo.load_heroes()
    return {h["name"].lower(): h["id"] for h in heroes}


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
