"""Tests for combo_stats: lane duo pair winrates from publicMatches.

The pair pipeline aggregates same-team hero pairs from OpenDota
publicMatches rows, classifies lane duos via the curated hero
positions, and refreshes incrementally behind a persisted cursor.
All tests are hermetic: fetchers are injected, no network.
"""

import unittest
from unittest.mock import patch

import combo_stats
import opendota_client


def make_match(match_id, radiant, dire, radiant_win=True):
    """One publicMatches row."""
    return {
        "match_id": match_id,
        "radiant_team": list(radiant),
        "dire_team": list(dire),
        "radiant_win": radiant_win,
    }


# OpenDota numeric ids used by the fixtures: two disjoint teams.
NAMES = {
    1: "Axe",
    2: "Bane",
    3: "Chen",
    5: "Crystal Maiden",
    8: "Juggernaut",
    42: "Phoenix",
    44: "Wraith King",
    74: "Invoker",
    75: "Zeus",
    76: "Vengefulspirit",
}
KNOWN_NAMES = set(NAMES.values())
TEAM_A = [1, 2, 3, 5, 8]
TEAM_B = [42, 44, 74, 75, 76]


def hero(name, positions):
    """One local hero dict (name/positions are all the pipeline needs)."""
    return {"name": name, "positions": positions}


class TestExtractPairCounts(unittest.TestCase):
    """extract_pair_counts aggregates same-team pairs from matches."""

    def test_radiant_win_counts_radiant_pairs(self):
        m = make_match(100, TEAM_A, TEAM_B, radiant_win=True)
        counts = combo_stats.extract_pair_counts([m], NAMES, KNOWN_NAMES)
        self.assertEqual(counts[("Axe", "Bane")], [1, 1])

    def test_dire_win_counts_dire_pairs(self):
        m = make_match(100, TEAM_A, TEAM_B, radiant_win=False)
        counts = combo_stats.extract_pair_counts([m], NAMES, KNOWN_NAMES)
        self.assertEqual(counts[("Phoenix", "Wraith King")], [1, 1])

    def test_radiant_loss_does_not_credit_radiant_pairs(self):
        m = make_match(100, TEAM_A, TEAM_B, radiant_win=False)
        counts = combo_stats.extract_pair_counts([m], NAMES, KNOWN_NAMES)
        self.assertEqual(counts[("Axe", "Bane")], [1, 0])

    def test_pair_key_is_name_sorted(self):
        team = [2, 1, 3, 5, 8]  # Bane before Axe: pair key still sorted
        m = make_match(100, team, TEAM_B, radiant_win=True)
        counts = combo_stats.extract_pair_counts([m], NAMES, KNOWN_NAMES)
        self.assertIn(("Axe", "Bane"), counts)

    def test_zeroed_live_match_teams_are_skipped(self):
        """Still-live matches have zeroed teams; nothing is counted."""
        m = make_match(100, [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], radiant_win=True)
        counts = combo_stats.extract_pair_counts([m], NAMES, KNOWN_NAMES)
        self.assertEqual(counts, {})

    def test_unknown_hero_id_skips_that_team(self):
        """A team containing an unmapped id is skipped entirely."""
        m = make_match(100, [1, 2, 3, 5, 999], TEAM_B, radiant_win=False)
        counts = combo_stats.extract_pair_counts([m], NAMES, KNOWN_NAMES)
        # Only the dire team's pairs are counted (they won, so 1 win).
        self.assertEqual(counts[("Phoenix", "Wraith King")], [1, 1])
        self.assertEqual(len(counts), 10)

    def test_unknown_local_name_skips_team(self):
        """Heroes not in the local repository are not interesting pairs."""
        m = make_match(100, TEAM_A, TEAM_B, radiant_win=True)
        counts = combo_stats.extract_pair_counts([m], NAMES, KNOWN_NAMES - {"Chen"})
        # TEAM_A contains Chen: skipped. TEAM_B has no Chen: counted.
        self.assertNotIn(("Axe", "Bane"), counts)
        self.assertIn(("Phoenix", "Wraith King"), counts)

    def test_short_team_is_skipped(self):
        m = make_match(100, [1, 2, 3], TEAM_B, radiant_win=True)
        counts = combo_stats.extract_pair_counts([m], NAMES, KNOWN_NAMES)
        self.assertNotIn(("Axe", "Bane"), counts)
        self.assertIn(("Phoenix", "Wraith King"), counts)

    def test_counts_accumulate_across_matches(self):
        matches = [
            make_match(100, TEAM_A, TEAM_B, radiant_win=True),
            make_match(101, TEAM_A, TEAM_B, radiant_win=False),
        ]
        counts = combo_stats.extract_pair_counts(matches, NAMES, KNOWN_NAMES)
        self.assertEqual(counts[("Axe", "Bane")], [2, 1])


class TestMergePairStats(unittest.TestCase):
    """merge_pair_stats decays old counts and adds new ones."""

    def test_existing_rows_are_decayed(self):
        rows = [{"hero1": "Axe", "hero2": "Bane", "games": 10.0, "wins": 5.0}]
        merged = combo_stats.merge_pair_stats(rows, {}, decay_factor=0.5)
        self.assertAlmostEqual(merged[0]["games"], 5.0)
        self.assertAlmostEqual(merged[0]["wins"], 2.5)

    def test_new_counts_are_added_on_top_of_decay(self):
        rows = [{"hero1": "Axe", "hero2": "Bane", "games": 10.0, "wins": 5.0}]
        new = {("Axe", "Bane"): [3, 3]}
        merged = combo_stats.merge_pair_stats(rows, new, decay_factor=0.5)
        self.assertAlmostEqual(merged[0]["games"], 8.0)
        self.assertAlmostEqual(merged[0]["wins"], 5.5)

    def test_decayed_rows_below_prune_threshold_are_dropped(self):
        rows = [{"hero1": "Axe", "hero2": "Bane", "games": 10.0, "wins": 5.0}]
        merged = combo_stats.merge_pair_stats(rows, {}, decay_factor=0.05)
        self.assertEqual(merged, [])

    def test_new_only_counts_appear(self):
        new = {("Axe", "Bane"): [4, 2]}
        merged = combo_stats.merge_pair_stats([], new)
        self.assertEqual(
            merged, [{"hero1": "Axe", "hero2": "Bane", "games": 4, "wins": 2}]
        )

    def test_rows_are_sorted_by_pair_names(self):
        new = {("Axe", "Juggernaut"): [2, 1], ("Axe", "Bane"): [2, 1]}
        merged = combo_stats.merge_pair_stats([], new)
        self.assertEqual([row["hero1"] for row in merged], ["Axe", "Axe"])
        self.assertEqual(merged[0]["hero2"], "Bane")
        self.assertEqual(merged[1]["hero2"], "Juggernaut")


class TestLaneDuoType(unittest.TestCase):
    """lane_duo_type classifies pairs via the CONTEXT.md lane model."""

    def test_carry_plus_hard_support_is_safelane(self):
        self.assertEqual(
            combo_stats.lane_duo_type(hero("Juggernaut", [1]), hero("CM", [5])),
            "Safelane",
        )

    def test_lane_duo_order_does_not_matter(self):
        self.assertEqual(
            combo_stats.lane_duo_type(hero("CM", [5]), hero("Juggernaut", [1])),
            "Safelane",
        )

    def test_offlaner_plus_soft_support_is_offlane(self):
        self.assertEqual(
            combo_stats.lane_duo_type(hero("Axe", [3]), hero("Chen", [4])),
            "Offlane",
        )

    def test_multi_position_heroes_match_by_any_viable_position(self):
        self.assertEqual(
            combo_stats.lane_duo_type(hero("Axe", [1, 3]), hero("CM", [4, 5])),
            "Safelane",
        )

    def test_mid_only_pairs_are_not_lane_duos(self):
        self.assertIsNone(
            combo_stats.lane_duo_type(hero("Pudge", [2]), hero("Zeus", [2]))
        )

    def test_same_position_pairs_are_not_lane_duos(self):
        self.assertIsNone(combo_stats.lane_duo_type(hero("A", [1]), hero("B", [1])))

    def test_incompatible_positions_are_not_lane_duos(self):
        self.assertIsNone(combo_stats.lane_duo_type(hero("A", [1]), hero("B", [3])))


class TestSuggestLaneDuos(unittest.TestCase):
    """suggest_lane_duos picks the best sample-backed duo per lane."""

    POOL = [
        hero("Juggernaut", [1]),
        hero("Crystal Maiden", [5]),
        hero("Axe", [3]),
        hero("Chen", [4]),
    ]

    def _row(self, hero1, hero2, games, wins):
        return {"hero1": hero1, "hero2": hero2, "games": games, "wins": wins}

    def test_best_duo_per_lane_is_suggested(self):
        rows = [
            self._row("Crystal Maiden", "Juggernaut", 30, 20),  # 66.7%
            self._row("Axe", "Chen", 25, 10),  # 40.0%
        ]
        duos = combo_stats.suggest_lane_duos(self.POOL, rows)
        self.assertEqual(len(duos), 2)
        by_lane = {duo["lane"]: duo for duo in duos}
        self.assertAlmostEqual(by_lane["Safelane"]["winrate"], 66.7)
        self.assertEqual(
            (by_lane["Safelane"]["hero1"], by_lane["Safelane"]["hero2"]),
            ("Crystal Maiden", "Juggernaut"),
        )
        self.assertAlmostEqual(by_lane["Offlane"]["winrate"], 40.0)

    def test_pairs_below_minimum_games_are_excluded(self):
        rows = [self._row("Crystal Maiden", "Juggernaut", 10, 9)]
        self.assertEqual(combo_stats.suggest_lane_duos(self.POOL, rows), [])

    def test_empty_stats_suggest_nothing(self):
        self.assertEqual(combo_stats.suggest_lane_duos(self.POOL, []), [])

    def test_only_one_duo_per_lane_is_suggested(self):
        pool = self.POOL + [hero("Drow Ranger", [1])]
        rows = [
            self._row("Crystal Maiden", "Juggernaut", 30, 20),  # 66.7%
            self._row("Crystal Maiden", "Drow Ranger", 20, 14),  # 70.0%
        ]
        duos = combo_stats.suggest_lane_duos(pool, rows)
        safelane = [d for d in duos if d["lane"] == "Safelane"]
        self.assertEqual(len(safelane), 1)
        self.assertEqual(safelane[0]["hero2"], "Drow Ranger")

    def test_incompatible_pairs_are_ignored_even_with_stats(self):
        rows = [self._row("Axe", "Juggernaut", 40, 30)]  # pos 3 + pos 1: no lane
        self.assertEqual(combo_stats.suggest_lane_duos(self.POOL, rows), [])


class FakeStatsStore:
    """In-memory pair stats store with the storage interface."""

    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.state = {}

    def load_pair_stats(self):
        return list(self.rows)

    def save_pair_stats(self, rows):
        self.rows = list(rows)

    def get_state(self, key, default=None):
        return self.state.get(key, default)

    def set_state(self, key, value):
        self.state[key] = str(value)


class FakeHeroRepo:
    """In-memory hero repository exposing display names."""

    def __init__(self, names):
        self.names = list(names)

    def load_heroes(self):
        return [{"name": name, "positions": [3]} for name in self.names]


class FakePublicMatches:
    """publicMatches simulator: newest first, 100 rows per page."""

    PAGE_SIZE = 100

    def __init__(self, matches):
        self.matches = sorted(matches, key=lambda m: -m["match_id"])
        self.calls = []

    def __call__(self, less_than_match_id=None, min_rank=None):
        self.calls.append({"less_than": less_than_match_id, "min_rank": min_rank})
        rows = self.matches
        if less_than_match_id is not None:
            rows = [m for m in rows if m["match_id"] < less_than_match_id]
        return rows[: self.PAGE_SIZE]


def refresh(store, matches, pages=10, min_rank=50):
    """Run one combo refresh against the given matches."""
    return combo_stats.refresh_combo_stats(
        store,
        FakeHeroRepo(KNOWN_NAMES),
        pages=pages,
        min_rank=min_rank,
        fetch_matches=FakePublicMatches(matches),
        fetch_names=lambda: NAMES,
        sleep_fn=lambda seconds: None,
    )


class TestRefreshComboStats(unittest.TestCase):
    """refresh_combo_stats walks newer matches behind the cursor."""

    def test_first_refresh_processes_all_matches(self):
        matches = [make_match(i, TEAM_A, TEAM_A) for i in range(1000, 1250)]
        store = FakeStatsStore()
        processed = refresh(store, matches)
        self.assertEqual(processed, 250)
        self.assertEqual(store.state[combo_stats.CURSOR_KEY], "1249")

    def test_cursor_prevents_reprocessing(self):
        matches = [make_match(i, TEAM_A, TEAM_A) for i in range(1000, 1100)]
        store = FakeStatsStore()
        refresh(store, matches)
        before_rows = store.rows
        processed = refresh(store, matches)
        self.assertEqual(processed, 0)
        self.assertEqual(store.rows, before_rows)

    def test_refresh_without_new_matches_does_not_decay_stats(self):
        """A no-op refresh must not erode stored counts."""
        matches = [make_match(i, TEAM_A, TEAM_A) for i in range(1000, 1100)]
        store = FakeStatsStore()
        refresh(store, matches)
        games_before = store.rows[0]["games"]
        refresh(store, matches)
        self.assertAlmostEqual(store.rows[0]["games"], games_before)

    def test_new_matches_decay_existing_counts(self):
        matches = [make_match(i, TEAM_A, TEAM_A) for i in range(1000, 1100)]
        store = FakeStatsStore()
        refresh(store, matches)
        key = ("Axe", "Bane")
        games_before = next(
            row["games"] for row in store.rows if (row["hero1"], row["hero2"]) == key
        )
        matches.append(make_match(1100, TEAM_A, TEAM_A))
        processed = refresh(store, matches)
        self.assertEqual(processed, 1)
        row = next(row for row in store.rows if (row["hero1"], row["hero2"]) == key)
        # Existing games decayed once (0.95); the new match adds one
        # pair game per team, so +2.
        self.assertAlmostEqual(row["games"], games_before * 0.95 + 2)

    def test_zeroed_live_matches_advance_cursor_without_counts(self):
        matches = [make_match(i, TEAM_A, TEAM_A) for i in range(1000, 1100)]
        store = FakeStatsStore()
        refresh(store, matches)
        matches.append(make_match(1101, [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]))
        processed = refresh(store, matches)
        self.assertEqual(processed, 1)
        self.assertEqual(store.state[combo_stats.CURSOR_KEY], "1101")

    def test_names_fetch_failure_returns_none_and_keeps_stats(self):
        def failing_names():
            raise opendota_client.OpenDotaError("down")

        matches = [make_match(i, TEAM_A, TEAM_A) for i in range(1000, 1100)]
        store = FakeStatsStore()
        combo_stats.refresh_combo_stats(
            store,
            FakeHeroRepo(KNOWN_NAMES),
            fetch_matches=FakePublicMatches(matches),
            fetch_names=failing_names,
            sleep_fn=lambda seconds: None,
        )
        self.assertEqual(store.rows, [])
        self.assertNotIn(combo_stats.CURSOR_KEY, store.state)

    def test_page_fetch_failure_saves_partial_results(self):
        matches = [make_match(i, TEAM_A, TEAM_A) for i in range(1000, 1100)]

        class FailingAfterFirstPage:
            def __init__(self):
                self.fetcher = FakePublicMatches(matches)
                self.first = True

            def __call__(self, less_than_match_id=None, min_rank=None):
                if not self.first:
                    raise opendota_client.OpenDotaError("timeout")
                self.first = False
                return self.fetcher(less_than_match_id, min_rank)

        store = FakeStatsStore()
        processed = combo_stats.refresh_combo_stats(
            store,
            FakeHeroRepo(KNOWN_NAMES),
            pages=10,
            min_rank=50,
            fetch_matches=FailingAfterFirstPage(),
            fetch_names=lambda: NAMES,
            sleep_fn=lambda seconds: None,
        )
        self.assertEqual(processed, 100)
        self.assertNotEqual(store.rows, [])
        self.assertEqual(store.state[combo_stats.CURSOR_KEY], "1099")

    def test_min_rank_is_passed_to_the_fetcher(self):
        matches = [make_match(i, TEAM_A, TEAM_A) for i in range(1000, 1100)]
        fetcher = FakePublicMatches(matches)
        combo_stats.refresh_combo_stats(
            FakeStatsStore(),
            FakeHeroRepo(KNOWN_NAMES),
            pages=1,
            min_rank=60,
            fetch_matches=fetcher,
            fetch_names=lambda: NAMES,
            sleep_fn=lambda seconds: None,
        )
        self.assertEqual(fetcher.calls[0]["min_rank"], 60)


class TestDefaultsFromEnvironment(unittest.TestCase):
    """Env configuration falls back to defaults on bad values."""

    def test_min_rank_default(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(combo_stats.default_min_rank(), 50)

    def test_invalid_min_rank_falls_back(self):
        with patch.dict("os.environ", {"DOTA_THEMER_COMBO_MIN_RANK": "yes"}):
            self.assertEqual(combo_stats.default_min_rank(), 50)

    def test_pages_minimum_is_one(self):
        with patch.dict("os.environ", {"DOTA_THEMER_COMBO_PAGES": "0"}):
            self.assertEqual(combo_stats.default_pages(), 1)

    def test_pages_from_environment(self):
        with patch.dict("os.environ", {"DOTA_THEMER_COMBO_PAGES": "7"}):
            self.assertEqual(combo_stats.default_pages(), 7)


if __name__ == "__main__":
    unittest.main()
