"""
Dota Themer - Core functionality
Suggests a theme and lists matching heroes with their positions.
"""

import json
import random
import sys
from pathlib import Path

# Load data files
DATA_DIR = Path(__file__).parent / "data"

def load_heroes():
    """Load heroes from JSON file."""
    with open(DATA_DIR / "heroes.json", "r") as f:
        return json.load(f)

def load_themes():
    """Load themes from JSON file."""
    with open(DATA_DIR / "themes.json", "r") as f:
        return json.load(f)

def get_heroes_by_ids(hero_ids, all_heroes):
    """Get hero objects for a list of hero IDs."""
    hero_map = {h["id"]: h for h in all_heroes}
    return [hero_map[hid] for hid in hero_ids if hid in hero_map]

def format_hero_list(heroes):
    """Format a list of heroes with their positions in parentheses."""
    return ", ".join(f"{h['name']} ({h['positions_display']})" for h in heroes)

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


def filter_themes(themes, all_heroes, party_size=None, min_heroes=None, require_position_coverage=False):
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
        if required_min is not None and isinstance(required_min, int) and required_min > 0:
            if hero_count < required_min:
                continue
        
        # Filter by position coverage
        if require_position_coverage and not has_position_coverage(matching_heroes):
            continue
        
        filtered.append(theme)
    
    return filtered


def select_theme(themes, heroes, party_size=None, use_weighted=False, require_position_coverage=False):
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
    # Filter themes first
    filtered_themes = filter_themes(
        themes, 
        heroes, 
        party_size=party_size,
        require_position_coverage=require_position_coverage
    )
    
    if not filtered_themes:
        # Fall back to all themes if filtering removed everything
        filtered_themes = themes
    
    if use_weighted:
        # Weighted selection: themes with more heroes have higher probability
        weights = [get_theme_hero_count(t, heroes) for t in filtered_themes]
        return random.choices(filtered_themes, weights=weights, k=1)[0]
    else:
        return random.choice(filtered_themes)

def get_theme_suggestion(party_size=2, use_weighted=False, require_position_coverage=False):
    """
    Get a theme suggestion for a given party size.
    
    Args:
        party_size: Number of players (1-5)
        use_weighted: If True, use weighted random selection (favors themes with more heroes)
        require_position_coverage: If True, only select themes with heroes in all positions 1-5
    
    Returns:
        dict: {"theme": theme_name, "description": theme_desc, "heroes": formatted_hero_list, "hero_count": int}
    """
    heroes = load_heroes()
    themes = load_themes()
    
    # Select a theme with filtering and weighting options
    theme = select_theme(
        themes, 
        heroes, 
        party_size=party_size,
        use_weighted=use_weighted,
        require_position_coverage=require_position_coverage
    )
    
    # Get matching heroes
    matching_heroes = get_heroes_by_ids(theme["hero_ids"], heroes)
    
    # Sort heroes by name for consistent output
    matching_heroes.sort(key=lambda h: h["name"])
    
    return {
        "theme": theme["name"],
        "description": theme.get("description", ""),
        "heroes": format_hero_list(matching_heroes),
        "hero_count": len(matching_heroes)
    }

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
