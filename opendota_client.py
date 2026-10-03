"""Dota Themer - OpenDota client for runtime Turbo winrate sync.

Fetches per-hero Turbo winrates from the OpenDota API
(https://api.opendota.com/api/heroStats) and writes them into the hero
repository so theme suggestions can show current winrates.

The bot refreshes at startup and weekly. API failures are never fatal:
stored winrates are kept and the next cycle retries.

Also fetches the numeric-id hero name map and public ranked matches
(https://api.opendota.com/api/publicMatches) used to build the hero
pair winrate table for lane duo suggestions.
"""

import logging_config

logger = logging_config.get_logger(logging_config.LOGGER_CORE)

OPENDOTA_HEROSTATS_URL = "https://api.opendota.com/api/heroStats"
OPENDOTA_HEROES_URL = "https://api.opendota.com/api/heroes"
OPENDOTA_PUBLIC_MATCHES_URL = "https://api.opendota.com/api/publicMatches"
USER_AGENT = "dota-themer/1.0 (https://github.com/Jenriksen/dota-themer)"
REQUEST_TIMEOUT_SECONDS = 15

# heroStats uses legacy localized names for some heroes; map them to the
# current local display names so winrate lookups succeed.
HEROSTATS_NAME_ALIASES = {
    "Outworld Devourer": "Outworld Destroyer",
    "Ring Master": "Ringmaster",
}


class OpenDotaError(Exception):
    """The OpenDota API could not be reached or returned bad data."""


def fetch_hero_stats(url=OPENDOTA_HEROSTATS_URL):
    """Fetch the heroStats payload. Raises OpenDotaError on failure."""
    import requests

    try:
        response = requests.get(
            url, timeout=REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT}
        )
        response.raise_for_status()
        return response.json()
    except Exception as error:
        raise OpenDotaError(f"heroStats request failed: {error}") from error


def fetch_hero_names(url=OPENDOTA_HEROES_URL):
    """Fetch the OpenDota numeric hero id -> display name map.

    Raises OpenDotaError on failure. The names match the local hero
    display names (same source as the heroStats sync), so pair stats
    keyed by these names join directly onto the hero repository.
    """
    import requests

    try:
        response = requests.get(
            url, timeout=REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT}
        )
        response.raise_for_status()
        return {hero["id"]: hero["localized_name"] for hero in response.json()}
    except Exception as error:
        raise OpenDotaError(f"heroes request failed: {error}") from error


def fetch_public_matches(
    less_than_match_id=None, min_rank=None, url=OPENDOTA_PUBLIC_MATCHES_URL
):
    """Fetch one page of public ranked matches, newest first.

    Args:
        less_than_match_id: Only matches with a lower match id (pagination).
        min_rank: Minimum rank tier (10-80; 50 is roughly high Divine).

    Raises OpenDotaError on failure. Rows for very recent (still live)
    matches can have zeroed teams until they finish; the aggregation
    skips those.
    """
    import requests

    params = {}
    if less_than_match_id is not None:
        params["less_than_match_id"] = less_than_match_id
    if min_rank is not None:
        params["min_rank"] = min_rank
    try:
        response = requests.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        return response.json()
    except Exception as error:
        raise OpenDotaError(f"publicMatches request failed: {error}") from error


def compute_turbo_winrates(api_hero_stats):
    """Map local display names to Turbo winrates from a heroStats payload.

    Winrate is turbo_wins / turbo_picks as a percent rounded to one
    decimal. Heroes with no Turbo picks are omitted. API localized names
    that differ from local display names are normalized via
    HEROSTATS_NAME_ALIASES.
    """
    winrates = {}
    for hero in api_hero_stats:
        picks = hero.get("turbo_picks", 0)
        if not picks:
            continue
        name = hero["localized_name"]
        name = HEROSTATS_NAME_ALIASES.get(name, name)
        winrates[name] = round(100 * hero["turbo_wins"] / picks, 1)
    return winrates


def apply_winrates(hero_repo, winrates):
    """Write Turbo winrates into the hero repository.

    Heroes with no API entry keep their stored winrate. Returns the
    number of heroes whose winrate changed.
    """
    heroes = hero_repo.load_heroes()
    updated = 0
    for hero in heroes:
        winrate = winrates.get(hero["name"])
        if winrate is not None and hero.get("turbo_winrate") != winrate:
            hero["turbo_winrate"] = winrate
            updated += 1
    if updated:
        hero_repo.save_heroes(heroes)
    return updated


def refresh_winrates(hero_repo):
    """Fetch current Turbo winrates and apply them to the repository.

    Returns the number of heroes updated, or None when the API could not
    be reached (stored winrates are kept; the next cycle retries).
    """
    try:
        winrates = compute_turbo_winrates(fetch_hero_stats())
    except OpenDotaError as error:
        logger.warning(f"Turbo winrate refresh skipped: {error}")
        return None
    updated = apply_winrates(hero_repo, winrates)
    logger.info(f"Turbo winrates refreshed for {updated} heroes")
    return updated
