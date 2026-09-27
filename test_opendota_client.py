"""Tests for opendota_client: runtime Turbo winrate sync from OpenDota.

The bot refreshes hero turbo winrates from
https://api.opendota.com/api/heroStats at startup and weekly (issue #56).
These tests cover the pure logic with injected payloads; no network.
"""

import unittest
from unittest import mock
from unittest.mock import MagicMock

import opendota_client


class TestComputeTurboWinrates(unittest.TestCase):
    """compute_turbo_winrates derives winrates from heroStats payloads."""

    def test_winrate_is_percent_rounded_to_one_decimal(self):
        stats = [{"localized_name": "Axe", "turbo_wins": 51, "turbo_picks": 100}]
        self.assertEqual(opendota_client.compute_turbo_winrates(stats), {"Axe": 51.0})

    def test_hero_with_zero_picks_is_omitted(self):
        stats = [{"localized_name": "Axe", "turbo_wins": 0, "turbo_picks": 0}]
        self.assertEqual(opendota_client.compute_turbo_winrates(stats), {})

    def test_legacy_api_names_are_aliased(self):
        """heroStats legacy localized names map to local display names."""
        stats = [
            {
                "localized_name": "Outworld Devourer",
                "turbo_wins": 50,
                "turbo_picks": 100,
            },
            {"localized_name": "Ring Master", "turbo_wins": 46, "turbo_picks": 100},
        ]
        winrates = opendota_client.compute_turbo_winrates(stats)
        self.assertIn("Outworld Destroyer", winrates)
        self.assertIn("Ringmaster", winrates)


class TestApplyWinrates(unittest.TestCase):
    """apply_winrates updates hero turbo_winrate via the repository."""

    def _hero_repo_with(self, heroes):
        repo = MagicMock()
        repo.load_heroes.return_value = heroes
        return repo

    def test_updates_matching_heroes(self):
        heroes = [{"id": "axe", "name": "Axe", "positions": [3]}]
        repo = self._hero_repo_with(heroes)
        updated = opendota_client.apply_winrates(repo, {"Axe": 51.2})
        self.assertEqual(updated, 1)
        saved = repo.save_heroes.call_args[0][0]
        self.assertEqual(saved[0]["turbo_winrate"], 51.2)

    def test_hero_without_api_entry_keeps_stored_winrate(self):
        """No API entry: nothing is written, stored winrate is kept."""
        heroes = [{"id": "axe", "name": "Axe", "positions": [3], "turbo_winrate": 50.0}]
        repo = self._hero_repo_with(heroes)
        updated = opendota_client.apply_winrates(repo, {"Bane": 51.0})
        self.assertEqual(updated, 0)
        repo.save_heroes.assert_not_called()

    def test_no_updates_when_no_hero_matches(self):
        repo = self._hero_repo_with([{"id": "axe", "name": "Axe", "positions": [3]}])
        updated = opendota_client.apply_winrates(repo, {"Bane": 51.0})
        self.assertEqual(updated, 0)
        repo.save_heroes.assert_not_called()

    def test_unexpected_error_is_raised(self):
        """Errors from the repository propagate to the caller (logged upstream)."""
        repo = MagicMock()
        repo.load_heroes.side_effect = RuntimeError("boom")
        with self.assertRaises(RuntimeError):
            opendota_client.apply_winrates(repo, {"Axe": 51.0})


class TestRefreshWinrates(unittest.TestCase):
    """refresh_winrates fetches from the API and applies, never raising."""

    def test_success_applies_winrates(self):
        stats = [{"localized_name": "Axe", "turbo_wins": 51, "turbo_picks": 100}]
        repo = MagicMock()
        repo.load_heroes.return_value = [{"id": "axe", "name": "Axe", "positions": [3]}]
        with mock.patch.object(
            opendota_client, "fetch_hero_stats", return_value=stats
        ) as _:
            updated = opendota_client.refresh_winrates(repo)
        self.assertEqual(updated, 1)
        repo.save_heroes.assert_called_once()

    def test_network_failure_returns_none(self):
        """API errors are swallowed: stored winrates are kept, retried later."""
        repo = MagicMock()
        with mock.patch.object(
            opendota_client,
            "fetch_hero_stats",
            side_effect=opendota_client.OpenDotaError("timeout"),
        ):
            updated = opendota_client.refresh_winrates(repo)
        self.assertIsNone(updated)
        repo.save_heroes.assert_not_called()


if __name__ == "__main__":
    unittest.main()
