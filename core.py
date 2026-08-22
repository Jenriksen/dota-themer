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

def select_theme(themes, heroes, party_size=None):
    """
    Select a theme.
    For MVP: random selection.
    
    Future: Could filter themes that have enough heroes for party_size,
    or have good position coverage.
    """
    return random.choice(themes)

def get_theme_suggestion(party_size=2):
    """
    Get a theme suggestion for a given party size.
    
    Args:
        party_size: Number of players (1-5)
    
    Returns:
        dict: {"theme": theme_name, "description": theme_desc, "heroes": formatted_hero_list}
    """
    heroes = load_heroes()
    themes = load_themes()
    
    # Select a theme (for MVP: random)
    theme = select_theme(themes, heroes, party_size)
    
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
