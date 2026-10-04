"""Tests for opendota_client: runtime Turbo winrate sync from OpenDota.

The bot refreshes hero turbo winrates from
https://api.opendota.com/api/heroStats at startup and weekly (issue #56).
These tests cover the pure logic with injected payloads; no network.
"""

import unittest
from unittest import mock
from unittest.mock import MagicMock

import requests

import opendota_client


def make_response(status_code=200, payload=None, headers=None):
    """Build a fake requests response."""
    response = MagicMock()
    response.status_code = status_code
    response.headers = headers or {}
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f"{status_code} error"
        )
    response.json.return_value = payload
    return response


class TestRequestJsonRetries(unittest.TestCase):
    """_request_json retries transient failures with capped backoff."""

    def _run(self, side_effects):
        """Run _request_json with mocked HTTP and sleep; return (result, delays)."""
        delays = []
        with mock.patch("requests.get", side_effect=side_effects), mock.patch.object(
            opendota_client.time, "sleep"
        ) as sleep:
            sleep.side_effect = delays.append
            result = opendota_client._request_json("https://x", params={})
        return result, delays

    def test_success_first_try_has_no_retries(self):
        result, delays = self._run([make_response(200, {"ok": True})])
        self.assertEqual(result, {"ok": True})
        self.assertEqual(delays, [])

    def test_429_is_retried_with_backoff(self):
        result, delays = self._run(
            [make_response(429), make_response(200, {"ok": True})]
        )
        self.assertEqual(result, {"ok": True})
        self.assertEqual(delays, [opendota_client.INITIAL_BACKOFF_SECONDS])

    def test_retry_after_header_is_honored(self):
        """A server-provided Retry-After larger than the backoff wins."""
        throttled = make_response(429, headers={"Retry-After": "30"})
        _, delays = self._run([throttled, make_response(200, {"ok": True})])
        self.assertEqual(delays, [30.0])

    def test_retry_after_is_capped_at_max_backoff(self):
        """A huge Retry-After never hangs the refresh: it is capped."""
        throttled = make_response(429, headers={"Retry-After": "3600"})
        _, delays = self._run([throttled, make_response(200, {"ok": True})])
        self.assertEqual(delays, [opendota_client.MAX_BACKOFF_SECONDS])

    def test_exhausted_retries_raise_open_dota_error(self):
        """Three 429s in a row fail the request."""
        throttled = make_response(429)
        with self.assertRaises(opendota_client.OpenDotaError):
            self._run([throttled, throttled, throttled, throttled])

    def test_backoff_doubles_across_retries(self):
        throttled = make_response(429)
        with mock.patch("requests.get", return_value=throttled), mock.patch.object(
            opendota_client.time, "sleep"
        ) as sleep:
            with self.assertRaises(opendota_client.OpenDotaError):
                opendota_client._request_json("https://x")
        self.assertEqual(
            [call.args[0] for call in sleep.call_args_list],
            [5.0, 10.0, 20.0],
        )

    def test_server_error_is_retried(self):
        result, delays = self._run([make_response(503), make_response(200, [1, 2])])
        self.assertEqual(result, [1, 2])
        self.assertEqual(delays, [opendota_client.INITIAL_BACKOFF_SECONDS])

    def test_timeout_is_retried(self):
        result, delays = self._run(
            [requests.exceptions.Timeout("t"), make_response(200, {"ok": 1})]
        )
        self.assertEqual(result, {"ok": 1})
        self.assertEqual(delays, [opendota_client.INITIAL_BACKOFF_SECONDS])

    def test_client_error_is_not_retried(self):
        """404s are not transient: they fail immediately, no sleeping."""
        with mock.patch(
            "requests.get", return_value=make_response(404)
        ) as get, mock.patch.object(opendota_client.time, "sleep") as sleep:
            with self.assertRaises(opendota_client.OpenDotaError):
                opendota_client._request_json("https://x")
        self.assertEqual(get.call_count, 1)
        sleep.assert_not_called()


class TestFetcherRequestShapes(unittest.TestCase):
    """Fetchers send the expected query parameters and headers."""

    def test_public_matches_passes_pagination_params(self):
        ok = make_response(200, [])
        with mock.patch("requests.get", return_value=ok) as get:
            opendota_client.fetch_public_matches(less_than_match_id=100, min_rank=50)
        self.assertEqual(
            get.call_args.kwargs["params"],
            {"less_than_match_id": 100, "min_rank": 50},
        )

    def test_requests_identify_themselves_with_user_agent(self):
        """OpenDota rejects bare clients with 403; the UA must be sent."""
        ok = make_response(200, [])
        with mock.patch("requests.get", return_value=ok) as get:
            opendota_client.fetch_public_matches()
        self.assertEqual(
            get.call_args.kwargs["headers"]["User-Agent"], opendota_client.USER_AGENT
        )


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
