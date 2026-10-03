"""Dota Themer - Hero pair winrates for lane duo suggestions.

Builds a hero-pair (games, wins) table from OpenDota public ranked
matches. Pairs are keyed by display names, matching the Turbo winrate
pipeline; lane classification uses the curated hero positions from the
hero repository (safelane = pos 1+5, offlane = pos 3+4, CONTEXT.md).

The refresh is incremental: the newest processed match id is persisted
in the stats store and each cycle only processes newer matches. Counts
decay once per cycle so stale patch data fades out.
"""

import os
import time

import logging_config
import opendota_client

logger = logging_config.get_logger(logging_config.LOGGER_CORE)

# Counts decay once per refresh cycle (daily task); 0.95 keeps roughly a
# one-month effective window of matches.
DECAY_FACTOR = 0.95
# Politeness delay between publicMatches pages, in seconds.
REQUEST_DELAY_SECONDS = 1.05
# Duos below this decayed game count are never suggested.
MIN_SUGGESTION_GAMES = 20.0
# At most one suggested duo per lane per theme suggestion.
MAX_DUOS_PER_LANE = 1
# Pair rows below one equivalent game are pruned on merge.
PRUNE_BELOW_GAMES = 1.0

# Stats-store key holding the newest processed match id.
CURSOR_KEY = "last_match_id"


def default_min_rank():
    """Minimum rank tier for sampled matches (env, default 50 = high Divine)."""
    try:
        return int(os.environ.get("DOTA_THEMER_COMBO_MIN_RANK", "50"))
    except ValueError:
        return 50


def default_pages():
    """publicMatches pages fetched per refresh cycle (env, default 120)."""
    try:
        return max(1, int(os.environ.get("DOTA_THEMER_COMBO_PAGES", "120")))
    except ValueError:
        return 120


def extract_pair_counts(matches, hero_names, known_names):
    """Aggregate same-team pair (games, wins) counts from public matches.

    Args:
        matches: publicMatches rows (dicts with radiant_team/dire_team).
        hero_names: OpenDota numeric hero id -> display name map.
        known_names: local hero display names; pairs touching anything
            else (unknown heroes, zeroed live matches) are skipped.

    Returns:
        dict: {(hero1_name, hero2_name): [games, wins]} with the pair
        names sorted. Team length must be 5 for both teams.
    """
    counts = {}
    for match in matches:
        teams = (
            ("radiant_team", bool(match.get("radiant_win"))),
            ("dire_team", not match.get("radiant_win", False)),
        )
        for team_field, won in teams:
            team = match.get(team_field) or []
            names = [hero_names.get(hero_id) for hero_id in team]
            if len(team) != 5 or any(
                name is None or name not in known_names for name in names
            ):
                continue
            for i in range(5):
                for j in range(i + 1, 5):
                    key = (min(names[i], names[j]), max(names[i], names[j]))
                    entry = counts.setdefault(key, [0, 0])
                    entry[0] += 1
                    if won:
                        entry[1] += 1
    return counts


def merge_pair_stats(existing_rows, new_counts, decay_factor=DECAY_FACTOR):
    """Merge new pair counts into existing rows, decaying old counts.

    Rows decay below PRUNE_BELOW_GAMES are dropped so the table stays
    compact. Returns the merged rows sorted by pair names.
    """
    merged = {}
    for row in existing_rows:
        merged[(row["hero1"], row["hero2"])] = [
            row["games"] * decay_factor,
            row["wins"] * decay_factor,
        ]
    for key, (games, wins) in new_counts.items():
        entry = merged.setdefault(key, [0.0, 0.0])
        entry[0] += games
        entry[1] += wins
    rows = [
        {"hero1": hero1, "hero2": hero2, "games": games, "wins": wins}
        for (hero1, hero2), (games, wins) in merged.items()
        if games >= PRUNE_BELOW_GAMES
    ]
    rows.sort(key=lambda row: (row["hero1"], row["hero2"]))
    return rows


def lane_duo_type(hero_a, hero_b):
    """Classify a hero pair as a lane duo, or None when incompatible.

    Safelane duos pair position 1 with 5; offlane duos pair 3 with 4
    (the CONTEXT.md lane model). Order does not matter.
    """
    positions_a = set(hero_a["positions"])
    positions_b = set(hero_b["positions"])
    if (1 in positions_a and 5 in positions_b) or (
        5 in positions_a and 1 in positions_b
    ):
        return "Safelane"
    if (3 in positions_a and 4 in positions_b) or (
        4 in positions_a and 3 in positions_b
    ):
        return "Offlane"
    return None


def suggest_lane_duos(
    heroes,
    pair_rows,
    min_games=MIN_SUGGESTION_GAMES,
    max_per_lane=MAX_DUOS_PER_LANE,
):
    """Suggest the best lane duos from a hero pool given pair stats.

    Args:
        heroes: Hero dicts (with name/positions) from a theme's pool.
        pair_rows: Pair stat rows ({hero1, hero2, games, wins}).
        min_games: Decay-adjusted minimum sample for a suggestion.
        max_per_lane: Cap on suggestions per lane.

    Returns:
        list of {"lane", "hero1", "hero2", "games", "winrate"} dicts,
        best winrate first within each lane.
    """
    stats = {(row["hero1"], row["hero2"]): row for row in pair_rows}
    candidates = []
    for i, hero_a in enumerate(heroes):
        for hero_b in heroes[i + 1 :]:
            lane = lane_duo_type(hero_a, hero_b)
            if lane is None:
                continue
            key = (
                min(hero_a["name"], hero_b["name"]),
                max(hero_a["name"], hero_b["name"]),
            )
            row = stats.get(key)
            if row is None or row["games"] < min_games:
                continue
            candidates.append(
                {
                    "lane": lane,
                    "hero1": key[0],
                    "hero2": key[1],
                    "games": row["games"],
                    "winrate": round(100.0 * row["wins"] / row["games"], 1),
                }
            )
    candidates.sort(key=lambda duo: (duo["lane"], -duo["winrate"]))
    selected = []
    counts_by_lane = {}
    for duo in candidates:
        if counts_by_lane.get(duo["lane"], 0) >= max_per_lane:
            continue
        counts_by_lane[duo["lane"]] = counts_by_lane.get(duo["lane"], 0) + 1
        selected.append(duo)
    return selected


def _read_cursor(stats_store):
    """Read the newest processed match id, or None when never refreshed."""
    value = stats_store.get_state(CURSOR_KEY)
    return int(value) if value is not None else None


def refresh_combo_stats(
    stats_store,
    hero_repo,
    pages=None,
    min_rank=None,
    fetch_matches=None,
    fetch_names=None,
    sleep_fn=time.sleep,
):
    """Grow the pair-winrate table from public matches newer than the cursor.

    Walks the publicMatches feed newest-first, skipping matches the
    cursor already covers, then merges the new pair counts into the
    stored table (decaying old counts).

    Args:
        stats_store: Pair stats store (load_pair_stats/save_pair_stats/
            get_state/set_state).
        hero_repo: Hero repository (display names + positions).
        pages: Pages to fetch this cycle (default from the environment).
        min_rank: Minimum rank tier filter (default from the environment).
        fetch_matches: Page fetcher (injected for tests).
        fetch_names: Hero name map fetcher (injected for tests).
        sleep_fn: Politeness delay function (injected for tests).

    Returns:
        int: Number of matches processed this cycle, or None when the
        API could not be reached at all (stored stats are kept; the
        next cycle retries).
    """
    fetch_matches = fetch_matches or opendota_client.fetch_public_matches
    fetch_names = fetch_names or opendota_client.fetch_hero_names
    pages = pages if pages is not None else default_pages()
    min_rank = min_rank if min_rank is not None else default_min_rank()

    try:
        hero_names = fetch_names()
        known_names = {hero["name"] for hero in hero_repo.load_heroes()}
    except Exception as error:
        logger.warning(f"Combo stats refresh skipped: {error}")
        return None

    cursor = _read_cursor(stats_store)
    page_before = None
    newest = None
    processed = 0
    page_counts = {}
    counted_games = 0
    for _ in range(pages):
        try:
            rows = fetch_matches(less_than_match_id=page_before, min_rank=min_rank)
        except opendota_client.OpenDotaError as error:
            logger.warning(f"Combo stats page fetch failed: {error}")
            break
        if not rows:
            break
        kept = [
            row
            for row in rows
            if row.get("match_id") and (cursor is None or row["match_id"] > cursor)
        ]
        page_before = min(row["match_id"] for row in rows)
        if not kept:
            break
        counts = extract_pair_counts(kept, hero_names, known_names)
        for key, (games, wins) in counts.items():
            entry = page_counts.setdefault(key, [0, 0])
            entry[0] += games
            entry[1] += wins
        counted_games += sum(games for games, _ in counts.values())
        processed += len(kept)
        page_newest = max(row["match_id"] for row in kept)
        newest = page_newest if newest is None else max(newest, page_newest)
        sleep_fn(REQUEST_DELAY_SECONDS)

    if processed == 0:
        return 0
    stats_store.set_state(CURSOR_KEY, newest)
    if counted_games > 0:
        rows = merge_pair_stats(stats_store.load_pair_stats(), page_counts)
        stats_store.save_pair_stats(rows)
        logger.info(
            f"Combo stats refreshed: {processed} matches processed,"
            f" {len(rows)} pairs tracked"
        )
    return processed
