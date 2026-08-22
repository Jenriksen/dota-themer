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
        required_fields = {"id", "name", "primary_role", "positions", "positions_display"}
        for hero in heroes:
            self.assertIsInstance(hero, dict)
            self.assertTrue(required_fields.issubset(hero.keys()))
            self.assertIsInstance(hero["id"], str)
            self.assertIsInstance(hero["name"], str)
            self.assertIsInstance(hero["positions"], list)
            self.assertIsInstance(hero["positions_display"], str)

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
            {"id": "npc_dota_hero_axe", "name": "Axe", "positions_display": "3,4"},
            {"id": "npc_dota_hero_bane", "name": "Bane", "positions_display": "4,5"},
            {"id": "npc_dota_hero_chaos_knight", "name": "Chaos Knight", "positions_display": "1,3"},
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
        heroes = [{"name": "Axe", "positions_display": "3,4"}]
        result = core.format_hero_list(heroes)
        self.assertEqual(result, "Axe (3,4)")

    def test_formats_multiple_heroes(self):
        """Multiple heroes joined with comma and space."""
        heroes = [
            {"name": "Axe", "positions_display": "3,4"},
            {"name": "Bane", "positions_display": "4,5"},
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

    def test_positions_display_matches_positions(self):
        """positions_display string matches positions list."""
        heroes = core.load_heroes()

        for hero in heroes:
            expected_display = ",".join(map(str, sorted(hero["positions"])))
            self.assertEqual(
                hero["positions_display"], expected_display,
                f"Hero '{hero['name']}' has mismatched positions_display. "
                f"Expected: {expected_display}, Got: {hero['positions_display']}"
            )


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and things that shouldn't work."""

    def test_get_heroes_by_ids_with_all_nonexistent(self):
        """All requested hero IDs don't exist - returns empty list."""
        heroes = [{"id": "npc_dota_hero_axe", "name": "Axe", "positions_display": "3,4"}]
        result = core.get_heroes_by_ids(
            ["npc_dota_hero_nonexistent1", "npc_dota_hero_nonexistent2"],
            heroes
        )
        self.assertEqual(result, [])

    def test_get_heroes_by_ids_with_duplicates(self):
        """Duplicate hero IDs in input - returns duplicates (current behavior)."""
        heroes = [
            {"id": "npc_dota_hero_axe", "name": "Axe", "positions_display": "3,4"},
            {"id": "npc_dota_hero_bane", "name": "Bane", "positions_display": "4,5"},
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
        heroes = [{"name": "Anti-Mage", "positions_display": "1,2"}]
        result = core.format_hero_list(heroes)
        self.assertEqual(result, "Anti-Mage (1,2)")

    def test_format_hero_list_with_multi_digit_positions(self):
        """Positions like 10 would break display - but positions are only 1-5."""
        # This tests the display logic doesn't break with edge case data
        heroes = [{"name": "Test", "positions_display": "1,2,3,4,5"}]
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
        heroes = [{"id": "npc_dota_hero_axe", "name": "Axe", "positions_display": "3,4"}]
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
                json.dump([{"id": "test", "name": "Test", "positions": [1], "positions_display": "1"}], f)
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
        heroes = [{"id": "npc_dota_hero_axe", "name": "Axe", "positions_display": "3,4"}]
        theme = {"name": "Empty Theme", "hero_ids": ["npc_dota_hero_nonexistent"]}
        matching = core.get_heroes_by_ids(theme["hero_ids"], heroes)
        self.assertEqual(len(matching), 0)

    def test_theme_with_empty_hero_ids_list(self):
        """Theme with empty hero_ids list."""
        heroes = [{"id": "npc_dota_hero_axe", "name": "Axe", "positions_display": "3,4"}]
        matching = core.get_heroes_by_ids([], heroes)
        self.assertEqual(len(matching), 0)

    def test_hero_with_empty_positions(self):
        """Hero with empty positions list has empty display."""
        hero = {"name": "Test", "positions": [], "positions_display": ""}
        result = core.format_hero_list([hero])
        self.assertEqual(result, "Test ()")

    def test_hero_with_single_position(self):
        """Hero with single position formatted without comma."""
        hero = {"name": "Test", "positions": [1], "positions_display": "1"}
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

    def test_positions_list_matches_positions_display(self):
        """Each hero's positions list exactly matches positions_display."""
        heroes = core.load_heroes()
        for hero in heroes:
            expected_display = ",".join(map(str, sorted(hero["positions"])))
            self.assertEqual(
                hero["positions_display"], expected_display,
                f"Mismatch for {hero['name']}: positions={hero['positions']}, "
                f"display={hero['positions_display']}"
            )

    def test_positions_are_sorted_in_display(self):
        """positions_display has positions in sorted order."""
        heroes = core.load_heroes()
        for hero in heroes:
            parts = hero["positions_display"].split(",")
            int_parts = [int(p) for p in parts]
            self.assertEqual(int_parts, sorted(int_parts),
                           f"Positions not sorted for {hero['name']}")


if __name__ == "__main__":
    unittest.main()
