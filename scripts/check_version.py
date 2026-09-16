#!/usr/bin/env python3
"""
Dota Themer - Version Check Script

This script verifies that the version in __version__.py has been incremented
compared to the version in the main branch. This is used as a PR gate to prevent
version regressions.

Usage:
    python scripts/check_version.py

Returns:
    0 - Version is valid (new version >= main branch version)
    1 - Version check failed (new version < main branch version)
"""

import subprocess
import sys
from pathlib import Path


def get_current_version():
    """Get the version from __version__.py in the current working directory."""
    version_file = Path("__version__.py")
    if not version_file.exists():
        print("ERROR: __version__.py not found")
        return None

    # Read the version file
    with open(version_file, "r") as f:
        content = f.read()

    # Extract version using exec (safe since it's our own file)
    namespace = {}
    exec(content, namespace)
    return namespace.get("__version__")


def get_main_version():
    """Get the version from __version__.py in the main branch."""
    try:
        # Fetch the main branch version file
        result = subprocess.run(
            ["git", "show", "main:__version__.py"],
            capture_output=True,
            text=True,
            check=True,
        )
        content = result.stdout

        # Extract version using exec
        namespace = {}
        exec(content, namespace)
        return namespace.get("__version__")
    except subprocess.CalledProcessError:
        # main branch doesn't have __version__.py, this is the first version
        return None
    except Exception as e:
        print(f"ERROR: Failed to get main branch version: {e}")
        return None


def parse_version(version_str):
    """Parse a version string into a tuple of integers for comparison."""
    if not version_str:
        return None

    # Remove any leading v or other prefixes
    version_str = version_str.lstrip("vV")

    # Split by . and convert to integers
    parts = []
    for part in version_str.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            # Handle pre-release versions like 1.0.0-alpha
            # For now, just use the numeric parts
            break

    return tuple(parts) if parts else None


def compare_versions(current, main):
    """Compare two version tuples.

    Returns:
        True if current >= main
        False if current < main
    """
    if current is None or main is None:
        return True

    # Pad with zeros to make same length
    max_len = max(len(current), len(main))
    current_padded = current + (0,) * (max_len - len(current))
    main_padded = main + (0,) * (max_len - len(main))

    return current_padded >= main_padded


def main():
    print("Checking version increment...")

    # Get versions
    current_version_str = get_current_version()
    main_version_str = get_main_version()

    print(f"Current version: {current_version_str}")
    print(f"Main branch version: {main_version_str}")

    if current_version_str is None:
        print("ERROR: Could not determine current version")
        return 1

    if main_version_str is None:
        # This is the first version, allow it
        print("[OK] No main branch version found (first version), allowing commit")
        return 0

    # Parse versions
    current_parsed = parse_version(current_version_str)
    main_parsed = parse_version(main_version_str)

    print(f"Parsed current: {current_parsed}")
    print(f"Parsed main: {main_parsed}")

    if current_parsed is None or main_parsed is None:
        print("ERROR: Could not parse version strings")
        return 1

    # Compare
    if compare_versions(current_parsed, main_parsed):
        print(
            f"[OK] Version {current_version_str} >= {main_version_str}, allowing commit"
        )
        return 0
    else:
        print(f"[FAIL] Version {current_version_str} < {main_version_str}")
        print("ERROR: Version must be incremented compared to main branch")
        return 1


if __name__ == "__main__":
    sys.exit(main())
