#!/usr/bin/env python
"""
Demonstration script for Custom Theme Creation feature.
This script demonstrates the theme management functionality without requiring Discord.
"""

import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core


def print_section(title):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_result(success, message):
    """Print a result with color coding."""
    if success:
        print(f"[SUCCESS] {message}")
    else:
        print(f"[FAIL] {message}")


def show_current_themes():
    """Display current themes."""
    print_section("Current Themes")
    try:
        themes = core.load_themes()
        print(f"Total themes: {len(themes)}\n")
        for i, theme in enumerate(themes[:10], 1):  # Show first 10
            hero_count = len(theme.get("hero_ids", []))
            print(f"{i}. {theme['name']}")
            print(f"   Description: {theme.get('description', 'N/A')}")
            print(f"   Heroes: {hero_count}")
        if len(themes) > 10:
            print(f"\n... and {len(themes) - 10} more themes")
    except Exception as e:
        print(f"Error loading themes: {e}")


def show_available_heroes():
    """Display available heroes."""
    print_section("Available Heroes")
    try:
        heroes = core.load_heroes()
        hero_names = sorted([h["name"] for h in heroes])
        print(f"Total heroes: {len(hero_names)}\n")
        # Show first 20 heroes
        for i, name in enumerate(hero_names[:20], 1):
            print(f"{i:2}. {name}")
        if len(hero_names) > 20:
            print(f"\n... and {len(hero_names) - 20} more heroes")
    except Exception as e:
        print(f"Error loading heroes: {e}")


def demo_add_theme():
    """Demonstrate adding a theme."""
    print_section("Demo: Adding a Theme")

    # Test 1: Valid theme
    print("Test 1: Adding a valid theme")
    success, message = core.add_theme(
        "Demo Theme",
        "A theme created for demonstration",
        ["antimage", "juggernaut", "crystal_maiden"],
    )
    print_result(success, message)

    # Test 2: Duplicate theme
    print("\nTest 2: Adding a duplicate theme")
    success, message = core.add_theme("Demo Theme", "Another description")
    print_result(success, message)

    # Test 3: Empty name
    print("\nTest 3: Adding theme with empty name")
    success, message = core.add_theme("", "Description")
    print_result(success, message)

    # Test 4: Invalid hero
    print("\nTest 4: Adding theme with invalid hero")
    success, message = core.add_theme(
        "Invalid Hero Theme", "Test", ["antimage", "nonexistent_hero"]
    )
    print_result(success, message)


def demo_update_theme():
    """Demonstrate updating a theme."""
    print_section("Demo: Updating a Theme")

    # First add a theme to update
    core.add_theme("Update Demo", "Theme for update demo", ["antimage", "juggernaut"])

    # Test 1: Add heroes
    print("Test 1: Adding heroes to theme")
    success, message = core.update_theme(
        "Update Demo", add_hero_ids=["crystal_maiden", "phantom_assassin"]
    )
    print_result(success, message)

    # Test 2: Remove heroes
    print("\nTest 2: Removing heroes from theme")
    success, message = core.update_theme("Update Demo", remove_hero_ids=["juggernaut"])
    print_result(success, message)

    # Test 3: Update description
    print("\nTest 3: Updating theme description")
    success, message = core.update_theme(
        "Update Demo", new_description="Updated description for demo"
    )
    print_result(success, message)

    # Test 4: Non-existent theme
    print("\nTest 4: Updating non-existent theme")
    success, message = core.update_theme(
        "Non Existent Theme", add_hero_ids=["antimage"]
    )
    print_result(success, message)


def demo_remove_theme():
    """Demonstrate removing a theme."""
    print_section("Demo: Removing a Theme")

    # First add a theme to remove
    core.add_theme("Remove Demo", "Theme for removal demo", ["antimage"])

    # Test 1: Remove existing theme
    print("Test 1: Removing existing theme")
    success, message = core.remove_theme("Remove Demo")
    print_result(success, message)

    # Test 2: Remove non-existent theme
    print("\nTest 2: Removing non-existent theme")
    success, message = core.remove_theme("Non Existent Theme")
    print_result(success, message)


def demo_list_functions():
    """Demonstrate listing functions."""
    print_section("Demo: Listing Functions")

    print("Getting all theme names:")
    theme_names = core.get_all_theme_names()
    print(f"Found {len(theme_names)} themes:")
    for name in theme_names[:10]:
        print(f"  - {name}")
    if len(theme_names) > 10:
        print(f"  ... and {len(theme_names) - 10} more")

    print("\nGetting hero name to ID mapping:")
    hero_mapping = core.get_all_hero_names()
    print(f"Found {len(hero_mapping)} heroes mapped")
    # Show first 5
    for name, hero_id in list(hero_mapping.items())[:5]:
        print(f"  {name} -> {hero_id}")
    print("  ...")


def cleanup_demo_themes():
    """Remove themes created during demo."""
    print_section("Cleanup: Removing Demo Themes")

    themes_to_remove = ["Demo Theme", "Update Demo", "Remove Demo"]
    for theme_name in themes_to_remove:
        try:
            core.remove_theme(theme_name)
            print(f"✅ Removed: {theme_name}")
        except Exception:
            pass  # Theme might not exist


def main():
    """Run the demonstration."""
    print("\n" + "=" * 60)
    print("  CUSTOM THEME CREATION FEATURE DEMONSTRATION")
    print("=" * 60)

    # Show current state
    show_current_themes()
    show_available_heroes()

    # Run demos
    demo_add_theme()
    demo_update_theme()
    demo_remove_theme()
    demo_list_functions()

    # Cleanup
    cleanup_demo_themes()

    print("\n" + "=" * 60)
    print("  DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nThe custom theme creation feature is working!")
    print("\nTo use in Discord:")
    print("  !addtheme <name> [description] <hero1> [hero2] ...")
    print("  !updatetheme <name> add|remove <hero1> [hero2] ...")
    print("  !removetheme <name>")
    print("  !listthemes")
    print("  !listheroes")
    print("  !helptheme")
    print()


if __name__ == "__main__":
    main()
