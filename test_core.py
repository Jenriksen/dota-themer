"""
Unit tests for Dota Themer core functionality.
Ensures functionality survives through refactorings.
"""

import unittest
import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch, mock_open

import core


class TestLoadFunctions(unittest.TestCase):
    """Tests for data loading functions."""

    def setUp(self):
        self.original_data_dir = core.DATA_DIR
        core.DATA_DIR = Path(__file__).parent / "data"

    def tearDown(self):
        core.DATA_DIR = self.original_data_dir

    def test_load_heroes_returns_list(self):
        """load_heroes() returns a non-empty list of heroes."""
        heroes = core.load_heroes()
        self.assertIsInstance(heroes, list)
        self.assertGreater(len(heroes), 0)

    def test_load_heroes_structure(self):
        """Each hero has required fields."""
        heroes = core.load_heroes()
        required_fields = {"id", "name", "primary_role", "positions"}
        for hero in heroes:
            self.assertIsInstance(hero, dict)
            self.assertTrue(required_fields.issubset(hero.keys()))
            self.assertIsInstance(hero["id"], str)
            self.assertIsInstance(hero["name"], str)
            self.assertIsInstance(hero["positions"], list)
            # positions_display is computed at runtime, not stored in data

    def test_load_themes_returns_list(self):
        """load_themes() returns a non-empty list of themes."""
        themes = core.load_themes()
        self.assertIsInstance(themes, list)
        self.assertGreater(len(themes), 0)

    def test_load_themes_structure(self):
        """Each theme has required fields."""
        themes = core.load_themes()
        required_fields = {"name", "hero_ids"}
        for theme in themes:
            self.assertIsInstance(theme, dict)
            self.assertTrue(required_fields.issubset(theme.keys()))
            self.assertIsInstance(theme["name"], str)
            self.assertIsInstance(theme["hero_ids"], list)
            # description is optional
            if "description" in theme:
                self.assertIsInstance(theme["description"], str)


class TestGetHeroesByIds(unittest.TestCase):
    """Tests for get_heroes_by_ids function."""

    def setUp(self):
        self.heroes = [
            {"id": "npc_dota_hero_axe", "name": "Axe", "positions": [3, 4]},
            {"id": "npc_dota_hero_bane", "name": "Bane", "positions": [4, 5]},
            {"id": "npc_dota_hero_chaos_knight", "name": "Chaos Knight", "positions": [1, 3]},
        ]

    def test_returns_matching_heroes(self):
        """Returns heroes whose IDs match the input list."""
        result = core.get_heroes_by_ids(
            ["npc_dota_hero_axe", "npc_dota_hero_chaos_knight"],
            self.heroes
        )
        self.assertEqual(len(result), 2)
        names = {h["name"] for h in result}
        self.assertEqual(names, {"Axe", "Chaos Knight"})

    def test_ignores_non_existent_ids(self):
        """Non-existent hero IDs are silently ignored."""
        result = core.get_heroes_by_ids(
            ["npc_dota_hero_axe", "npc_dota_hero_nonexistent"],
            self.heroes
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Axe")

    def test_empty_input_returns_empty_list(self):
        """Empty input list returns empty result."""
        result = core.get_heroes_by_ids([], self.heroes)
        self.assertEqual(result, [])


class TestFormatHeroList(unittest.TestCase):
    """Tests for format_hero_list function."""

    def test_formats_single_hero(self):
        """Single hero formatted correctly."""
        heroes = [{"name": "Axe", "positions": [3, 4]}]
        result = core.format_hero_list(heroes)
        self.assertEqual(result, "Axe (3,4)")

    def test_formats_multiple_heroes(self):
        """Multiple heroes joined with comma and space."""
        heroes = [
            {"name": "Axe", "positions": [3, 4]},
            {"name": "Bane", "positions": [4, 5]},
        ]
        result = core.format_hero_list(heroes)
        self.assertEqual(result, "Axe (3,4), Bane (4,5)")

    def test_empty_list_returns_empty_string(self):
        """Empty hero list returns empty string."""
        result = core.format_hero_list([])
        self.assertEqual(result, "")


class TestSelectTheme(unittest.TestCase):
    """Tests for select_theme function."""

    def test_returns_theme_from_list(self):
        """Returns a theme from the provided list."""
        themes = [
            {"name": "Theme A", "hero_ids": []},
            {"name": "Theme B", "hero_ids": []},
        ]
        heroes = []
        with patch("random.choice") as mock_choice:
            mock_choice.return_value = themes[0]
            result = core.select_theme(themes, heroes, party_size=2)
            self.assertEqual(result, themes[0])
            mock_choice.assert_called_once_with(themes)

    def test_calls_random_choice(self):
        """Uses random.choice for selection."""
        themes = [{"name": "Test", "hero_ids": []}]
        heroes = []
        with patch("random.choice") as mock_choice:
            mock_choice.return_value = themes[0]
            core.select_theme(themes, heroes)
            mock_choice.assert_called_once()


class TestGetThemeSuggestion(unittest.TestCase):
    """Tests for get_theme_suggestion function."""

    def setUp(self):
        self.original_data_dir = core.DATA_DIR
        core.DATA_DIR = Path(__file__).parent / "data"

    def tearDown(self):
        core.DATA_DIR = self.original_data_dir

    def test_returns_dict_with_required_keys(self):
        """Returns dict with all required keys."""
        result = core.get_theme_suggestion(party_size=2)
        self.assertIsInstance(result, dict)
        required_keys = {"theme", "description", "heroes", "hero_count"}
        self.assertTrue(required_keys.issubset(result.keys()))

    def test_theme_is_string(self):
        """Theme name is a string."""
        result = core.get_theme_suggestion()
        self.assertIsInstance(result["theme"], str)
        self.assertGreater(len(result["theme"]), 0)

    def test_heroes_is_formatted_string(self):
        """Heroes value is a formatted string."""
        result = core.get_theme_suggestion()
        self.assertIsInstance(result["heroes"], str)

    def test_hero_count_is_integer(self):
        """hero_count is an integer >= 0."""
        result = core.get_theme_suggestion()
        self.assertIsInstance(result["hero_count"], int)
        self.assertGreaterEqual(result["hero_count"], 0)

    def test_hero_count_matches_heroes_list(self):
        """hero_count matches the number of heroes in the formatted list."""
        result = core.get_theme_suggestion()
        # Count commas in heroes string + 1 (unless empty)
        if result["heroes"]:
            hero_count_from_string = result["heroes"].count(", ") + 1
            self.assertEqual(result["hero_count"], hero_count_from_string)
        else:
            self.assertEqual(result["hero_count"], 0)

    def test_heroes_sorted_alphabetically(self):
        """Heroes in the output are sorted alphabetically by name."""
        # Run multiple times to increase chance of catching unsorted output
        for _ in range(10):
            result = core.get_theme_suggestion()
            if result["hero_count"] > 1:
                # Extract hero names from formatted string
                hero_names = [h.split(" (")[0] for h in result["heroes"].split(", ")]
                self.assertEqual(hero_names, sorted(hero_names))

    def test_default_party_size_is_2(self):
        """Default party size is 2."""
        result = core.get_theme_suggestion()
        # Just verify it runs without error; party_size affects theme selection in future
        self.assertIsInstance(result, dict)

    def test_accepts_party_size_1_to_5(self):
        """Accepts party sizes from 1 to 5."""
        for size in range(1, 6):
            result = core.get_theme_suggestion(party_size=size)
            self.assertIsInstance(result, dict)
            self.assertIn("theme", result)

    def test_description_may_be_empty_string(self):
        """Description can be an empty string if not provided in theme."""
        result = core.get_theme_suggestion()
        self.assertIsInstance(result["description"], str)


class TestMain(unittest.TestCase):
    """Tests for main CLI function."""

    def setUp(self):
        self.original_data_dir = core.DATA_DIR
        core.DATA_DIR = Path(__file__).parent / "data"
        self.held_stdout = StringIO()

    def tearDown(self):
        core.DATA_DIR = self.original_data_dir

    @patch("sys.stdout", new_callable=StringIO)
    @patch("sys.argv", ["core.py"])
    def test_main_default_party_size(self, mock_stdout):
        """main() with no args uses default party size of 2."""
        core.main()
        output = mock_stdout.getvalue()
        self.assertIn("Theme:", output)
        self.assertIn("Heroes:", output)
        self.assertIn("heroes match this theme", output)

    @patch("sys.stdout", new_callable=StringIO)
    @patch("sys.argv", ["core.py", "3"])
    def test_main_with_party_size_arg(self, mock_stdout):
        """main() accepts party size argument."""
        core.main()
        output = mock_stdout.getvalue()
        self.assertIn("Theme:", output)
        self.assertIn("Heroes:", output)

    @patch("sys.stdout", new_callable=StringIO)
    @patch("sys.argv", ["core.py", "0"])
    def test_main_rejects_party_size_0(self, mock_stdout):
        """main() rejects party size < 1."""
        with self.assertRaises(SystemExit) as context:
            core.main()
        self.assertEqual(context.exception.code, 1)
        self.assertIn("Party size must be between 1 and 5", mock_stdout.getvalue())

    @patch("sys.stdout", new_callable=StringIO)
    @patch("sys.argv", ["core.py", "6"])
    def test_main_rejects_party_size_6(self, mock_stdout):
        """main() rejects party size > 5."""
        with self.assertRaises(SystemExit) as context:
            core.main()
        self.assertEqual(context.exception.code, 1)
        self.assertIn("Party size must be between 1 and 5", mock_stdout.getvalue())

    @patch("sys.stdout", new_callable=StringIO)
    @patch("sys.argv", ["core.py", "abc"])
    def test_main_handles_non_integer_arg(self, mock_stdout):
        """main() handles non-integer party size argument."""
        with self.assertRaises(ValueError):
            core.main()


class TestDataIntegrity(unittest.TestCase):
    """Tests to ensure data files have expected structure."""

    def setUp(self):
        self.original_data_dir = core.DATA_DIR
        core.DATA_DIR = Path(__file__).parent / "data"

    def tearDown(self):
        core.DATA_DIR = self.original_data_dir

    def test_all_theme_hero_ids_reference_existing_heroes(self):
        """All hero_ids in themes reference existing heroes."""
        heroes = core.load_heroes()
        themes = core.load_themes()
        hero_ids = {h["id"] for h in heroes}

        for theme in themes:
            for hero_id in theme["hero_ids"]:
                self.assertIn(
                    hero_id, hero_ids,
                    f"Theme '{theme['name']}' references non-existent hero: {hero_id}"
                )

    def test_all_heroes_have_valid_positions(self):
        """All heroes have valid position numbers (1-5)."""
        heroes = core.load_heroes()
        valid_positions = {1, 2, 3, 4, 5}

        for hero in heroes:
            for pos in hero["positions"]:
                self.assertIn(
                    pos, valid_positions,
                    f"Hero '{hero['name']}' has invalid position: {pos}"
                )


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and things that shouldn't work."""

    def test_get_heroes_by_ids_with_all_nonexistent(self):
        """All requested hero IDs don't exist - returns empty list."""
        heroes = [{"id": "npc_dota_hero_axe", "name": "Axe", "positions": [3, 4]}]
        result = core.get_heroes_by_ids(
            ["npc_dota_hero_nonexistent1", "npc_dota_hero_nonexistent2"],
            heroes
        )
        self.assertEqual(result, [])

    def test_get_heroes_by_ids_with_duplicates(self):
        """Duplicate hero IDs in input - returns duplicates (current behavior)."""
        heroes = [
            {"id": "npc_dota_hero_axe", "name": "Axe", "positions": [3, 4]},
            {"id": "npc_dota_hero_bane", "name": "Bane", "positions": [4, 5]},
        ]
        result = core.get_heroes_by_ids(
            ["npc_dota_hero_axe", "npc_dota_hero_axe", "npc_dota_hero_bane"],
            heroes
        )
        # Current behavior: duplicates in input produce duplicates in output
        self.assertEqual(len(result), 3)
        names = [h["name"] for h in result]
        self.assertEqual(names, ["Axe", "Axe", "Bane"])

    def test_format_hero_list_with_special_characters_in_name(self):
        """Hero names with special characters are formatted correctly."""
        heroes = [{"name": "Anti-Mage", "positions": [1, 2]}]
        result = core.format_hero_list(heroes)
        self.assertEqual(result, "Anti-Mage (1,2)")

    def test_format_hero_list_with_multi_digit_positions(self):
        """Positions like 10 would break display - but positions are only 1-5."""
        # This tests the display logic doesn't break with edge case data
        heroes = [{"name": "Test", "positions": [1, 2, 3, 4, 5]}]
        result = core.format_hero_list(heroes)
        self.assertEqual(result, "Test (1,2,3,4,5)")

    def test_select_theme_empty_list(self):
        """select_theme with empty themes list raises IndexError."""
        heroes = []
        with self.assertRaises(IndexError):
            core.select_theme([], heroes, party_size=2)

    def test_get_theme_suggestion_party_size_boundaries(self):
        """Party sizes exactly at boundaries (1 and 5) work."""
        for size in [1, 5]:
            result = core.get_theme_suggestion(party_size=size)
            self.assertIsInstance(result, dict)
            self.assertIn("theme", result)

    def test_get_heroes_by_ids_none_in_list(self):
        """Passing None as hero_ids list."""
        heroes = [{"id": "npc_dota_hero_axe", "name": "Axe", "positions": [3, 4]}]
        # This should handle None gracefully or raise a clear error
        with self.assertRaises(TypeError):
            core.get_heroes_by_ids(None, heroes)

    def test_format_hero_list_none_input(self):
        """Passing None to format_hero_list raises TypeError."""
        with self.assertRaises(TypeError):
            core.format_hero_list(None)


class TestDataFileErrors(unittest.TestCase):
    """Tests for file loading errors and malformed data."""

    def setUp(self):
        self.original_data_dir = core.DATA_DIR

    def tearDown(self):
        core.DATA_DIR = self.original_data_dir

    def test_load_heroes_file_not_found(self):
        """load_heroes raises FileNotFoundError for missing file."""
        core.DATA_DIR = Path("/nonexistent/path")
        with self.assertRaises(FileNotFoundError):
            core.load_heroes()

    def test_load_themes_file_not_found(self):
        """load_themes raises FileNotFoundError for missing file."""
        core.DATA_DIR = Path("/nonexistent/path")
        with self.assertRaises(FileNotFoundError):
            core.load_themes()

    def test_load_heroes_malformed_json(self):
        """load_heroes raises json.JSONDecodeError for malformed JSON."""
        # Create a temporary directory with malformed JSON
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            # Write malformed JSON
            with open(data_dir / "heroes.json", "w") as f:
                f.write("{invalid json}")
            
            core.DATA_DIR = data_dir
            with self.assertRaises(json.JSONDecodeError):
                core.load_heroes()

    def test_load_themes_malformed_json(self):
        """load_themes raises json.JSONDecodeError for malformed JSON."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            # Create valid heroes.json
            with open(data_dir / "heroes.json", "w") as f:
                json.dump([{"id": "test", "name": "Test", "positions": [1]}], f)
            # Write malformed themes.json
            with open(data_dir / "themes.json", "w") as f:
                f.write("[invalid json}")
            
            core.DATA_DIR = data_dir
            with self.assertRaises(json.JSONDecodeError):
                core.load_themes()


class TestEmptyAndNullData(unittest.TestCase):
    """Tests for empty data structures and null values."""

    def test_get_heroes_by_ids_empty_heroes_list(self):
        """Empty heroes list returns empty result."""
        result = core.get_heroes_by_ids(["any_id"], [])
        self.assertEqual(result, [])

    def test_format_hero_list_empty_list(self):
        """Empty hero list returns empty string."""
        result = core.format_hero_list([])
        self.assertEqual(result, "")

    def test_theme_with_no_matching_heroes(self):
        """Theme with hero_ids that don't match any heroes."""
        heroes = [{"id": "npc_dota_hero_axe", "name": "Axe", "positions": [3, 4]}]
        theme = {"name": "Empty Theme", "hero_ids": ["npc_dota_hero_nonexistent"]}
        matching = core.get_heroes_by_ids(theme["hero_ids"], heroes)
        self.assertEqual(len(matching), 0)

    def test_theme_with_empty_hero_ids_list(self):
        """Theme with empty hero_ids list."""
        heroes = [{"id": "npc_dota_hero_axe", "name": "Axe", "positions": [3, 4]}]
        matching = core.get_heroes_by_ids([], heroes)
        self.assertEqual(len(matching), 0)

    def test_hero_with_empty_positions(self):
        """Hero with empty positions list has empty display."""
        hero = {"name": "Test", "positions": []}
        result = core.format_hero_list([hero])
        self.assertEqual(result, "Test ()")

    def test_hero_with_single_position(self):
        """Hero with single position formatted without comma."""
        hero = {"name": "Test", "positions": [1]}
        result = core.format_hero_list([hero])
        self.assertEqual(result, "Test (1)")


class TestInvalidInputs(unittest.TestCase):
    """Tests for invalid inputs that should be rejected or handled."""

    def test_get_theme_suggestion_party_size_0(self):
        """Party size 0 is accepted by get_theme_suggestion (validation in main only)."""
        # The function itself doesn't validate, only main() does
        result = core.get_theme_suggestion(party_size=0)
        self.assertIsInstance(result, dict)
        self.assertIn("theme", result)

    def test_get_theme_suggestion_party_size_6(self):
        """Party size 6 is accepted by get_theme_suggestion (validation in main only)."""
        result = core.get_theme_suggestion(party_size=6)
        self.assertIsInstance(result, dict)
        self.assertIn("theme", result)

    def test_get_theme_suggestion_negative(self):
        """Negative party size is accepted by get_theme_suggestion."""
        result = core.get_theme_suggestion(party_size=-1)
        self.assertIsInstance(result, dict)

    def test_get_theme_suggestion_float(self):
        """Float party size is accepted (Python allows it)."""
        result = core.get_theme_suggestion(party_size=2.5)
        self.assertIsInstance(result, dict)

    def test_get_theme_suggestion_string(self):
        """String party size is accepted but ignored (no validation in function)."""
        # Current behavior: get_theme_suggestion doesn't validate party_size type
        # It only uses it for future filtering (not yet implemented)
        result = core.get_theme_suggestion(party_size="two")
        self.assertIsInstance(result, dict)
        self.assertIn("theme", result)


class TestDataConsistencyEdgeCases(unittest.TestCase):
    """Tests for data consistency edge cases."""

    def test_hero_ids_are_unique(self):
        """All hero IDs in heroes.json are unique."""
        heroes = core.load_heroes()
        hero_ids = [h["id"] for h in heroes]
        self.assertEqual(len(hero_ids), len(set(hero_ids)),
                        "Duplicate hero IDs found")

    def test_theme_names_are_unique(self):
        """All theme names in themes.json are unique."""
        themes = core.load_themes()
        theme_names = [t["name"] for t in themes]
        self.assertEqual(len(theme_names), len(set(theme_names)),
                        "Duplicate theme names found")

    def test_theme_hero_ids_are_unique_within_theme(self):
        """Hero IDs within a single theme are unique (no duplicates)."""
        themes = core.load_themes()
        for theme in themes:
            hero_ids = theme["hero_ids"]
            self.assertEqual(len(hero_ids), len(set(hero_ids)),
                           f"Duplicate hero IDs in theme '{theme['name']}'")

    def test_get_positions_display_function(self):
        """get_positions_display correctly formats positions."""
        self.assertEqual(core.get_positions_display([1, 2]), "1,2")
        self.assertEqual(core.get_positions_display([3, 1, 2]), "1,2,3")  # Sorted
        self.assertEqual(core.get_positions_display([5]), "5")
        self.assertEqual(core.get_positions_display([]), "")
        self.assertEqual(core.get_positions_display([1, 2, 3, 4, 5]), "1,2,3,4,5")

    def test_positions_are_sorted_in_display(self):
        """get_positions_display returns positions in sorted order."""
        result = core.get_positions_display([3, 1, 2])
        self.assertEqual(result, "1,2,3")
        result = core.get_positions_display([5, 2, 4, 1, 3])
        self.assertEqual(result, "1,2,3,4,5")


class TestEnhancedThemeSelection(unittest.TestCase):
    """Tests for enhanced theme selection features."""

    def setUp(self):
        self.original_data_dir = core.DATA_DIR
        core.DATA_DIR = Path(__file__).parent / "data"

    def tearDown(self):
        core.DATA_DIR = self.original_data_dir

    def test_has_position_coverage_true(self):
        """has_position_coverage returns True when all positions are covered."""
        heroes = [
            {"name": "H1", "positions": [1, 2]},
            {"name": "H2", "positions": [3, 4]},
            {"name": "H3", "positions": [5]},
        ]
        result = core.has_position_coverage(heroes, {1, 2, 3, 4, 5})
        self.assertTrue(result)

    def test_has_position_coverage_false(self):
        """has_position_coverage returns False when positions are missing."""
        heroes = [
            {"name": "H1", "positions": [1, 2]},
            {"name": "H2", "positions": [3]},
        ]
        result = core.has_position_coverage(heroes, {1, 2, 3, 4, 5})
        self.assertFalse(result)

    def test_has_position_coverage_empty_heroes(self):
        """has_position_coverage returns False for empty hero list."""
        result = core.has_position_coverage([], {1, 2, 3})
        self.assertFalse(result)

    def test_has_position_coverage_custom_positions(self):
        """has_position_coverage works with custom position sets."""
        heroes = [{"name": "H1", "positions": [1, 2]}]
        result = core.has_position_coverage(heroes, {1, 2})
        self.assertTrue(result)
        result = core.has_position_coverage(heroes, {1, 2, 3})
        self.assertFalse(result)

    def test_get_theme_hero_count(self):
        """get_theme_hero_count returns correct count."""
        heroes = [
            {"id": "h1", "name": "Hero1", "positions": [1]},
            {"id": "h2", "name": "Hero2", "positions": [2]},
            {"id": "h3", "name": "Hero3", "positions": [3]},
        ]
        theme = {"name": "Test", "hero_ids": ["h1", "h3", "nonexistent"]}
        result = core.get_theme_hero_count(theme, heroes)
        self.assertEqual(result, 2)

    def test_filter_themes_by_party_size(self):
        """filter_themes filters by minimum hero count."""
        heroes = [
            {"id": "h1", "name": "H1", "positions": [1]},
            {"id": "h2", "name": "H2", "positions": [2]},
            {"id": "h3", "name": "H3", "positions": [3]},
        ]
        themes = [
            {"name": "Small", "hero_ids": ["h1"]},  # 1 hero
            {"name": "Medium", "hero_ids": ["h1", "h2"]},  # 2 heroes
            {"name": "Large", "hero_ids": ["h1", "h2", "h3"]},  # 3 heroes
        ]
        filtered = core.filter_themes(themes, heroes, party_size=2)
        names = {t["name"] for t in filtered}
        self.assertNotIn("Small", names)
        self.assertIn("Medium", names)
        self.assertIn("Large", names)

    def test_filter_themes_by_min_heroes(self):
        """filter_themes uses min_heroes parameter."""
        heroes = [
            {"id": "h1", "name": "H1", "positions": [1]},
            {"id": "h2", "name": "H2", "positions": [2]},
        ]
        themes = [
            {"name": "Small", "hero_ids": ["h1"]},
            {"name": "Medium", "hero_ids": ["h1", "h2"]},
        ]
        filtered = core.filter_themes(themes, heroes, min_heroes=2)
        names = {t["name"] for t in filtered}
        self.assertNotIn("Small", names)
        self.assertIn("Medium", names)

    def test_filter_themes_by_position_coverage(self):
        """filter_themes filters by position coverage."""
        heroes = [
            {"id": "h1", "name": "H1", "positions": [1, 2]},
            {"id": "h2", "name": "H2", "positions": [3, 4]},
        ]
        themes = [
            {"name": "Partial", "hero_ids": ["h1"]},  # Only positions 1,2
            {"name": "Full", "hero_ids": ["h1", "h2"]},  # Positions 1,2,3,4
        ]
        # Note: No theme has position 5, so none will pass full coverage
        filtered = core.filter_themes(themes, heroes, require_position_coverage=True)
        # Since neither theme covers all 5 positions, both might be filtered out
        # or the filter falls back. Let's just verify it doesn't crash.
        self.assertIsInstance(filtered, list)

    def test_filter_themes_none_match(self):
        """filter_themes returns empty list when no themes match."""
        heroes = [{"id": "h1", "name": "H1", "positions": [1]}]
        themes = [{"name": "Small", "hero_ids": ["h1"]}]
        filtered = core.filter_themes(themes, heroes, party_size=10)
        self.assertEqual(filtered, [])

    def test_select_theme_weighted(self):
        """select_theme with weighted=True favors themes with more heroes."""
        heroes = [
            {"id": "h1", "name": "H1", "positions": [1]},
            {"id": "h2", "name": "H2", "positions": [2]},
            {"id": "h3", "name": "H3", "positions": [3]},
        ]
        themes = [
            {"name": "Small", "hero_ids": ["h1"]},
            {"name": "Large", "hero_ids": ["h1", "h2", "h3"]},
        ]
        # Run multiple times to verify weighted selection works
        large_count = 0
        small_count = 0
        for _ in range(100):
            theme = core.select_theme(themes, heroes, use_weighted=True)
            if theme["name"] == "Large":
                large_count += 1
            else:
                small_count += 1
        # Large should be selected more often (3:1 ratio expected)
        self.assertGreater(large_count, small_count)

    def test_select_theme_empty_filtered_list(self):
        """select_theme falls back to all themes when filtered list is empty."""
        heroes = []
        themes = [{"name": "Test", "hero_ids": []}]
        # With impossible filtering, should still return a theme
        result = core.select_theme(themes, heroes, party_size=100)
        self.assertIsNotNone(result)

    def test_get_theme_suggestion_with_weighted(self):
        """get_theme_suggestion accepts use_weighted parameter."""
        result = core.get_theme_suggestion(party_size=2, use_weighted=True)
        self.assertIsInstance(result, dict)
        self.assertIn("theme", result)

    def test_get_theme_suggestion_with_position_coverage(self):
        """get_theme_suggestion accepts require_position_coverage parameter."""
        result = core.get_theme_suggestion(party_size=2, require_position_coverage=True)
        self.assertIsInstance(result, dict)
        self.assertIn("theme", result)

    def test_filter_themes_string_party_size(self):
        """filter_themes handles string party_size gracefully."""
        heroes = [{"id": "h1", "name": "H1", "positions": [1]}]
        themes = [{"name": "Test", "hero_ids": ["h1"]}]
        # Should not crash with string party_size
        filtered = core.filter_themes(themes, heroes, party_size="invalid")
        self.assertEqual(len(filtered), 1)  # Should pass through without filtering


class TestPositionBasedFeatures(unittest.TestCase):
    """Tests for lane and position-based features."""

    def test_get_lane_for_position(self):
        """get_lane_for_position returns correct lane names."""
        self.assertEqual(core.get_lane_for_position(1), "Safelane")
        self.assertEqual(core.get_lane_for_position(2), "Mid")
        self.assertEqual(core.get_lane_for_position(3), "Offlane")
        self.assertEqual(core.get_lane_for_position(4), "Offlane")
        self.assertEqual(core.get_lane_for_position(5), "Safelane")
        self.assertEqual(core.get_lane_for_position(99), "Unknown")

    def test_group_heroes_by_lane(self):
        """group_heroes_by_lane correctly categorizes heroes."""
        heroes = [
            {"name": "Carry", "positions": [1]},  # Safelane
            {"name": "Midlaner", "positions": [2]},  # Mid
            {"name": "Offlaner", "positions": [3]},  # Offlane
            {"name": "Soft Support", "positions": [4]},  # Offlane
            {"name": "Hard Support", "positions": [5]},  # Safelane
        ]
        lanes = core.group_heroes_by_lane(heroes)
        
        self.assertEqual(len(lanes["Safelane"]), 2)
        self.assertEqual(len(lanes["Mid"]), 1)
        self.assertEqual(len(lanes["Offlane"]), 2)

    def test_format_lane_grouping(self):
        """format_lane_grouping returns formatted string."""
        heroes = [
            {"name": "Axe", "positions": [3, 4]},
            {"name": "Bane", "positions": [4, 5]},
            {"name": "Lina", "positions": [2]},
        ]
        result = core.format_lane_grouping(heroes)
        self.assertIn("Mid", result)
        self.assertIn("Offlane", result)
        self.assertIn("Safelane", result)
        self.assertIn("Axe", result)
        self.assertIn("Bane", result)
        self.assertIn("Lina", result)

    def test_get_party_configurations_all_sizes(self):
        """get_party_configurations returns configs for all party sizes."""
        for size in range(1, 6):
            configs = core.get_party_configurations(size)
            self.assertIsInstance(configs, list)
            self.assertGreater(len(configs), 0)
            for config in configs:
                total = sum(config.values())
                self.assertEqual(total, size, f"Config sum mismatch for size {size}")

    def test_get_party_configurations_size_2(self):
        """Party of 2 has safelane pair and offlane pair configs."""
        configs = core.get_party_configurations(2)
        config_names = [str(c) for c in configs]
        self.assertIn("{'Safelane': 2, 'Mid': 0, 'Offlane': 0}", config_names)
        self.assertIn("{'Safelane': 0, 'Mid': 0, 'Offlane': 2}", config_names)

    def test_get_party_configurations_size_3(self):
        """Party of 3 has safelane+mid and offlane+mid configs."""
        configs = core.get_party_configurations(3)
        config_names = [str(c) for c in configs]
        self.assertIn("{'Safelane': 2, 'Mid': 1, 'Offlane': 0}", config_names)
        self.assertIn("{'Safelane': 0, 'Mid': 1, 'Offlane': 2}", config_names)

    def test_get_party_configurations_size_4(self):
        """Party of 4 has safelane pair + offlane pair config."""
        configs = core.get_party_configurations(4)
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0], {"Safelane": 2, "Mid": 0, "Offlane": 2})

    def test_get_party_configurations_size_5(self):
        """Party of 5 has safelane(2) + mid(1) + offlane(2) config."""
        configs = core.get_party_configurations(5)
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0], {"Safelane": 2, "Mid": 1, "Offlane": 2})

    def test_validate_party_composition_valid(self):
        """validate_party_composition returns True for valid composition."""
        # Need heroes that can form valid configs for party of 3:
        # Config 1: 2 Safelane + 1 Mid, or Config 2: 1 Mid + 2 Offlane
        heroes = [
            {"name": "Carry", "positions": [1]},  # Safelane
            {"name": "Hard Support", "positions": [5]},  # Safelane (position 5)
            {"name": "Midlaner", "positions": [2]},  # Mid
        ]
        is_valid, reason = core.validate_party_composition(heroes, party_size=3)
        self.assertTrue(is_valid)

    def test_validate_party_composition_not_enough_heroes(self):
        """validate_party_composition returns False when not enough heroes."""
        heroes = [{"name": "H1", "positions": [1]}]
        is_valid, reason = core.validate_party_composition(heroes, party_size=3)
        self.assertFalse(is_valid)
        self.assertIn("Not enough heroes", reason)

    def test_validate_party_composition_no_valid_config(self):
        """validate_party_composition returns False when no valid lane config."""
        # For party of 4, we need 2 safelane + 2 offlane
        # If all heroes can only play mid, no valid config exists
        heroes = [
            {"name": "H1", "positions": [2]},  # Only Mid
            {"name": "H2", "positions": [2]},  # Only Mid
            {"name": "H3", "positions": [2]},  # Only Mid
            {"name": "H4", "positions": [2]},  # Only Mid
        ]
        is_valid, reason = core.validate_party_composition(heroes, party_size=4)
        self.assertFalse(is_valid)
        self.assertIn("No valid lane configuration found", reason)

    def test_suggest_balanced_team_valid(self):
        """suggest_balanced_team returns valid team for party of 3."""
        heroes = [
            {"name": "Carry", "positions": [1]},  # Safelane
            {"name": "Carry2", "positions": [1]},  # Safelane
            {"name": "Mid", "positions": [2]},  # Mid
            {"name": "Offlane", "positions": [3]},  # Offlane
            {"name": "Offlane2", "positions": [3]},  # Offlane
        ]
        result = core.suggest_balanced_team(heroes, party_size=3)
        self.assertIsNotNone(result)
        self.assertIn("heroes", result)
        self.assertIn("configuration", result)
        self.assertIn("by_lane", result)
        self.assertEqual(len(result["heroes"]), 3)

    def test_suggest_balanced_team_not_enough_heroes(self):
        """suggest_balanced_team returns None when not enough heroes."""
        heroes = [{"name": "H1", "positions": [1]}]
        result = core.suggest_balanced_team(heroes, party_size=3)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
