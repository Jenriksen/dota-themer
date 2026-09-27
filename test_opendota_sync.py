"""Tests for the OpenDota hero data comparison script (scripts/compare_opendota.py).

The script validates data/heroes.json against the live OpenDota hero
roster (https://api.opendota.com/api). These tests cover the pure
comparison logic; network fetching is injected so tests never hit the
API.
"""

import importlib.util
import json
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent / "scripts" / "compare_opendota.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("compare_opendota", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCompareHeroes(unittest.TestCase):
    """compare_heroes() reports drift between local and API hero data."""

    @classmethod
    def setUpClass(cls):
        cls.script = load_script_module()

    def test_matching_sets_report_no_drift(self):
        local = [{"id": "abaddon", "name": "Abaddon"}]
        api = [{"id": 1, "name": "npc_dota_hero_abaddon", "localized_name": "Abaddon"}]
        report = self.script.compare_heroes(local, api)
        self.assertEqual(report["missing_locally"], [])
        self.assertEqual(report["not_in_api"], [])
        self.assertEqual(report["api_count"], 1)
        self.assertEqual(report["local_count"], 1)

    def test_hero_in_api_missing_locally_is_reported(self):
        local = []
        api = [{"id": 1, "name": "npc_dota_hero_abaddon", "localized_name": "Abaddon"}]
        report = self.script.compare_heroes(local, api)
        self.assertEqual(report["missing_locally"], ["Abaddon"])
        self.assertEqual(report["not_in_api"], [])

    def test_hero_not_in_api_is_reported(self):
        local = [{"id": "abaddon", "name": "Abaddon"}]
        api = []
        report = self.script.compare_heroes(local, api)
        self.assertEqual(report["missing_locally"], [])
        self.assertEqual(report["not_in_api"], ["Abaddon"])

    def test_duplicate_local_display_names_are_reported(self):
        local = [
            {"id": "abaddon", "name": "Abaddon"},
            {"id": "abaddon2", "name": "Abaddon"},
        ]
        api = [{"id": 1, "name": "npc_dota_hero_abaddon", "localized_name": "Abaddon"}]
        report = self.script.compare_heroes(local, api)
        self.assertEqual(report["duplicate_local_names"], ["Abaddon"])

    def test_matching_is_by_display_name(self):
        """Local ids may differ from API npc names; only display names matter."""
        local = [{"id": "wraith_king", "name": "Wraith King"}]
        api = [
            {
                "id": 80,
                "name": "npc_dota_hero_skeleton_king",
                "localized_name": "Wraith King",
            }
        ]
        report = self.script.compare_heroes(local, api)
        self.assertEqual(report["missing_locally"], [])
        self.assertEqual(report["not_in_api"], [])


class TestFormatReport(unittest.TestCase):
    """format_report() renders the comparison as human-readable lines."""

    @classmethod
    def setUpClass(cls):
        cls.script = load_script_module()

    def test_clean_report_has_no_drift_lines(self):
        report = {
            "api_count": 2,
            "local_count": 2,
            "missing_locally": [],
            "not_in_api": [],
            "duplicate_local_names": [],
        }
        text = self.script.format_report(report)
        self.assertIn("Heroes in OpenDota API: 2", text)
        self.assertIn("Heroes in data/heroes.json: 2", text)
        self.assertIn("No drift detected", text)

    def test_drift_report_lists_hero_names(self):
        report = {
            "api_count": 2,
            "local_count": 1,
            "missing_locally": ["Batrider"],
            "not_in_api": ["Doom Bringer"],
            "duplicate_local_names": [],
        }
        text = self.script.format_report(report)
        self.assertIn("Missing locally (1): Batrider", text)
        self.assertIn("Not in OpenDota API (1): Doom Bringer", text)
        self.assertNotIn("No drift detected", text)

    def test_has_drift_flag(self):
        clean = {
            "missing_locally": [],
            "not_in_api": [],
            "duplicate_local_names": [],
        }
        drifted = {
            "missing_locally": ["Batrider"],
            "not_in_api": [],
            "duplicate_local_names": [],
        }
        self.assertFalse(self.script.has_drift(clean))
        self.assertTrue(self.script.has_drift(drifted))


class TestLocalDataAgainstStructure(unittest.TestCase):
    """Local hero data must be structurally ready for comparison."""

    def test_local_heroes_have_unique_display_names(self):
        heroes = json.loads(
            (Path(__file__).parent / "data" / "heroes.json").read_text(encoding="utf-8")
        )
        names = [h["name"] for h in heroes]
        duplicates = sorted({n for n in names if names.count(n) > 1})
        self.assertEqual(duplicates, [])


FIXTURES_DIR = Path(__file__).parent / "tests" / "fixtures"
HEROES_FIXTURE = FIXTURES_DIR / "opendota_heroes.json"
HEROSTATS_FIXTURE = FIXTURES_DIR / "opendota_herostats.json"


class TestOfflineFixtureDrift(unittest.TestCase):
    """The pinned API fixture and the repo hero data must agree offline.

    This is the CI-side drift guard (#56 Step 3): no network access,
    the fixture pins the roster the data was last synced against.
    """

    @classmethod
    def setUpClass(cls):
        cls.api_heroes = json.loads(HEROES_FIXTURE.read_text(encoding="utf-8"))
        cls.local_heroes = json.loads(
            (Path(__file__).parent / "data" / "heroes.json").read_text(encoding="utf-8")
        )

    def test_local_roster_matches_pinned_fixture(self):
        """No drift between data/heroes.json and the pinned API fixture."""
        report = load_script_module().compare_heroes(self.local_heroes, self.api_heroes)
        self.assertEqual(report["missing_locally"], [], format_report_drift(report))
        self.assertEqual(report["not_in_api"], [], format_report_drift(report))

    def test_seed_data_has_no_winrates(self):
        """Winrates are runtime-fetched only; the seed must not carry them."""
        stale = [h["name"] for h in self.local_heroes if "turbo_winrate" in h]
        self.assertEqual(stale, [])


def format_report_drift(report):
    script = load_script_module()
    return script.format_report(report)


if __name__ == "__main__":
    unittest.main()
