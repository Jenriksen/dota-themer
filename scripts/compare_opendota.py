#!/usr/bin/env python3
"""Dota Themer - OpenDota Hero Data Comparison

Compares the local hero data (data/heroes.json) against the live
OpenDota hero roster (https://api.opendota.com/api) and reports drift:
heroes missing locally, heroes no longer in the API, and duplicate
local display names.

Local heroes are matched to API heroes by display name
(local ``name`` vs API ``localized_name``). Local internal ids may
legitimately differ from the API's ``npc_dota_hero_*`` script names
(e.g. local "wraith_king" vs API "skeleton_king"), so ids are not
used for matching.

Usage:
    python scripts/compare_opendota.py

Returns:
    0 - No drift: local hero data matches the OpenDota roster
    1 - Drift detected (or the API/local data could not be read)
"""

import json
import sys
from pathlib import Path

import requests

OPENDOTA_HEROES_URL = "https://api.opendota.com/api/heroes"
USER_AGENT = "dota-themer/1.0 (https://github.com/Jenriksen/dota-themer)"
REQUEST_TIMEOUT_SECONDS = 15

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_HEROES_PATH = REPO_ROOT / "data" / "heroes.json"


def fetch_api_heroes(url=OPENDOTA_HEROES_URL):
    """Fetch the OpenDota hero roster. Returns a list of hero dicts."""
    response = requests.get(
        url, timeout=REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT}
    )
    response.raise_for_status()
    return response.json()


def load_local_heroes(path=LOCAL_HEROES_PATH):
    """Load the local hero data. Returns a list of hero dicts."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def compare_heroes(local_heroes, api_heroes):
    """Compare local hero data against the API roster by display name.

    Returns a report dict with api_count, local_count, missing_locally,
    not_in_api, and duplicate_local_names. All name lists are sorted.
    """
    api_names = {hero["localized_name"] for hero in api_heroes}
    local_names = [hero["name"] for hero in local_heroes]

    missing_locally = sorted(api_names - set(local_names))
    not_in_api = sorted(set(local_names) - api_names)
    duplicate_local_names = sorted(
        {name for name in local_names if local_names.count(name) > 1}
    )

    return {
        "api_count": len(api_names),
        "local_count": len(local_names),
        "missing_locally": missing_locally,
        "not_in_api": not_in_api,
        "duplicate_local_names": duplicate_local_names,
    }


def has_drift(report):
    """Return True if the report contains any form of drift."""
    return bool(
        report["missing_locally"]
        or report["not_in_api"]
        or report["duplicate_local_names"]
    )


def format_report(report):
    """Render the comparison report as human-readable lines."""
    lines = [
        f"Heroes in OpenDota API: {report['api_count']}",
        f"Heroes in data/heroes.json: {report['local_count']}",
        "",
    ]

    if not has_drift(report):
        lines.append("No drift detected: local hero data matches the OpenDota roster.")
        return "\n".join(lines)

    if report["missing_locally"]:
        lines.append(
            f"Missing locally ({len(report['missing_locally'])}): "
            + ", ".join(report["missing_locally"])
        )
    if report["not_in_api"]:
        lines.append(
            f"Not in OpenDota API ({len(report['not_in_api'])}): "
            + ", ".join(report["not_in_api"])
        )
    if report["duplicate_local_names"]:
        lines.append(
            f"Duplicate local display names ({len(report['duplicate_local_names'])}): "
            + ", ".join(report["duplicate_local_names"])
        )
    return "\n".join(lines)


def main():
    try:
        api_heroes = fetch_api_heroes()
        local_heroes = load_local_heroes()
    except (requests.RequestException, OSError, ValueError) as error:
        print(f"ERROR: could not load hero data: {error}", file=sys.stderr)
        return 1

    report = compare_heroes(local_heroes, api_heroes)
    print(format_report(report))
    return 1 if has_drift(report) else 0


if __name__ == "__main__":
    sys.exit(main())
