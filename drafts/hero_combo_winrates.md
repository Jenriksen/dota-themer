# Research: Hero Combination Winrates (Lane Duos)

Roadmap item (M4.2): *"Figure out how to find the hero combinations that has
the highest winrate in a lane and provide it as suggestions to a theme."*

Researched: 2026-10-03. All claims below were verified live against the
actual APIs unless noted.

## TL;DR

Two viable sources, best used together:

1. **OpenDota `publicMatches`** (primary): raw ranked matches with both
   teams' hero IDs + winner flag. Build our own pair-winrate table in
   SQLite. No API key needed. Lane attribution comes from **our own
   curated `heroes.json` positions** (safelane = pos 1+5, offlane = 3+4),
   not from the API.
2. **STRATZ GraphQL API** (secondary/validation): precomputed per-hero-pair
   `Synergy`, `MatchCount`, `WinCount` (weekly aggregation). Free
   registration token. Survives Valve API limitations because STRATZ
   ingests matches with its own infrastructure.

Avoid: OpenDota's parsed-match SQL warehouse for current-patch stats (see
"dead ends").

## Source comparison

| Source | Combo winrate? | Lane data? | Access | Freshness | Cost |
|---|---|---|---|---|---|
| OpenDota `publicMatches` | Raw (we compute) | No — use our own positions | Free, UA header, rate-limited/min | Live | Free |
| STRATZ GraphQL `heroStats` | Precomputed (`Synergy`, `MatchCount`, `WinCount`) | Pair-level only | Free API token, monthly quota | Weekly buckets | Free |
| OpenDota Explorer SQL | Compute from `player_matches` incl. `lane_role` | Yes (true lanes) | Free, GET `?sql=` | **Dead: ~379 parsed matches/30 days** | Free |
| OpenDota `/heroes/{id}/matchups` | Counters (vs), not combos | No | Free | Live | Free |
| OpenDota `/scenarios/laneRoles` | Per-hero-per-lane WR (no pairs) | Lane roles | Free | Live | Free |
| D2PT (`dota2protracker.com/combos`) | Yes (pro + immortal lane duos) | Yes | No public API (display only) | Current patch | — |
| Dotabuff combos | Yes | No | No public API (display only) | Live | — |
| Valve WebAPI | No aggregate stats | No | Match history only | — | — |

## Verified details

### OpenDota `publicMatches` (recommended primary)

- `GET https://api.opendota.com/api/publicMatches` with
  `less_than_match_id` (pagination), `min_rank` / `max_rank`
  (rank-tier scale; legacy `avg_rank_tier_greater_than` also still
  works). 100 matches per request.
- **Requires a User-Agent header** — bare requests get 403.
- Very recent matches (~minutes old) have zeroed teams; populated
  reliably within the page-2+ range.
- Proof of concept (2026-10-03): 6 requests → 579 usable matches with
  `min_rank`-style filter ≈ high-Divine/Immortal:
  - Top same-team pair: **Pudge + Sniper, 63% WR over 30 games**
  - Lane-duo heuristic (slots 0–1 / 3–4) surfaced Pudge + Sniper at 89%
    (9 games) and Juggernaut + Bristleback at 71% (7 games)
  - 4,785 of 7,140 possible pairs seen from just 579 matches
- Scaling math: ~100 matches/request; a polite nightly job fetching
  e.g. 600 pages (~10 min at 1 req/s) = 60k matches/day ≈ 1.2M pair
  samples/month at high rank. Common pairs reach 500–2,000+ games —
  enough for stable winrates with a minimum-sample guard (e.g. ≥ 20).
- Slot order in `radiant_team`/`dire_team` is player slot, not a
  guaranteed lane/position mapping. Treat it as a weak signal at best;
  prefer classifying pairs as lane duos via our curated positions.

### STRATZ GraphQL API (recommended secondary)

- Endpoint: `https://api.stratz.com/graphql`, Bearer token, free
  registration (stratz.com/api). GraphQL schema includes:
  - `heroStats` pair entries ("dryads"): `heroId1`, `heroId2`, `week`,
    `matchCount`, `winCount`, `synergy`, `winRateHeroId1`,
    `winRateHeroId2`, plus performance aggregates (kills/deaths/assists,
    net worth, duration, …)
  - `HomepageHeroSynergyType`: `mainHeroId`, `mainHeroBaseWinRate`,
    combo list with `matchCount`, `winCount`, `synergy`,
    `comparisonHeroBaseWinRate`
  - `HeroMatchupType` (`advantage`/`disadvantage` lists) — ready-made
    counter-picking data for a later M4.2 deliverable
- `synergy` = pair's actual winrate vs the expected winrate of the two
  heroes (STRATZ knowledge base: ~+4% at 50% together ≈ heroes
  overperforming as a duo).
- Caveats: pair-level (whole-match) synergy, **no lane attribution**;
  monthly request quota (check current terms); schema is large —
  introspect before writing the client. (Not live-verified: the public
  endpoint is behind a bot challenge; requires the free token.)

### OpenDota Explorer SQL (dead end for current data)

- `GET https://api.opendota.com/api/explorer?sql=<url-encoded SQL>`
  works (verified: computed pair winrates from `matches` ×
  `player_matches` self-join, same-team condition
  `floor(player_slot/128)`, win = `(player_slot < 128) = radiant_win`).
- `player_matches` has true `lane`, `lane_role`, `lane_pos` — the only
  source of genuine lane-combo data.
- **But** the warehouse only contains user-requested parsed matches:
  252k total since 2012, **379 in the last 30 days** (Valve's API
  changes ended bulk parsing). Useless for current-patch suggestions;
  fine for one-off historical queries.

## Recommended implementation sketch

1. **Fetcher**: extend `opendota_client.py` (or new `combo_stats.py`)
   with a `publicMatches` fetcher: paginated `less_than_match_id`
   walk, `min_rank` filter, UA header, 1 req/s politeness, resume from
   last stored match_id.
2. **Aggregation**: for each match, for each team, record all 10
   unordered pairs (`games += 1`, `wins += won`). Persist `(hero1,
   hero2, games, wins)` in the existing SQLite backend (`storage.py`) —
   snapshot pattern to S3 optional, same as themes.
3. **Lane classification** (our data, not the API's): a pair is a
   *safelane duo* if one hero is viable pos 1 and the other pos 5
   (`heroes.json` positions); *offlane duo* = pos 3 + pos 4. This
   matches the domain model in CONTEXT.md exactly.
4. **Suggestion integration**: when a theme is posted, take the
   theme's hero pool, form lane-compatible pairs, look up pair
   winrates, and append e.g.
   `Suggested safelane duo: Pudge + Sniper (63% over 30 games)`.
   Guardrails: minimum sample (≥ 20 games), cap of 1–2 suggestions per
   lane, omit gracefully when data is thin (same pattern as
   `turbo_winrate` being optional per hero).
5. **Refresh**: piggyback on the existing weekly
   `winrate_refresh_task`; decay/replace window stats each cycle
   (keep e.g. trailing 30–60 days).
6. **Optional STRATZ layer**: if pair coverage is too thin in some
   brackets, add a STRATZ client for precomputed `synergy` as a
   cross-check/fallback (needs free token + quota management).

## Open questions

- STRATZ exact quota and whether `heroStats` pair data covers all
  brackets or immortal-only (needs token to verify).
- Whether OpenDota anonymous monthly volume suffices for a nightly
  job, or we need their free key (opendota.com/api-keys lifts monthly
  limits).
- Patch sensitivity: combo stats from before/after a balance patch
  shift fast — window length (30 vs 60 days) needs tuning against
  sample size.
