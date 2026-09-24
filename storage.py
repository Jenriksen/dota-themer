"""SQLite storage backend and JSON migration for dota-themer.

Implements the HeroRepository/ThemeRepository contracts from core behind
SQLite, selected via DOTA_THEMER_BACKEND=json|sqlite (issue #34). The JSON
files remain the default until the sqlite backend is explicitly enabled.
"""

import json
import os
import sqlite3
from pathlib import Path

import core


def _connect(db_path):
    """Open a connection with JSON-serializing adapters registered."""
    return sqlite3.connect(str(db_path))


def _ensure_schema(conn):
    """Create the heroes/themes tables if they do not exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS heroes (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL
        )
        """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS themes (
            name TEXT PRIMARY KEY,
            data TEXT NOT NULL
        )
        """)


class SqliteHeroRepository:
    """Hero persistence backed by a SQLite table."""

    def __init__(self, db_path):
        self.db_path = Path(db_path)

    def load_heroes(self):
        """Load all heroes, ordered by id for stable output."""
        conn = _connect(self.db_path)
        try:
            _ensure_schema(conn)
            rows = conn.execute("SELECT data FROM heroes ORDER BY id").fetchall()
            return [json.loads(row[0]) for row in rows]
        finally:
            conn.close()

    def save_heroes(self, heroes):
        """Replace the hero table with the given list in one transaction."""
        conn = _connect(self.db_path)
        try:
            _ensure_schema(conn)
            conn.execute("BEGIN")
            conn.execute("DELETE FROM heroes")
            for hero in heroes:
                conn.execute(
                    "INSERT INTO heroes (id, data) VALUES (?, ?)",
                    (hero["id"], json.dumps(hero)),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


class SqliteThemeRepository:
    """Theme persistence backed by a SQLite table."""

    def __init__(self, db_path):
        self.db_path = Path(db_path)

    def load_themes(self, include_hidden=True):
        """Load themes, applying the same defaults/filtering as the JSON backend."""
        conn = _connect(self.db_path)
        try:
            _ensure_schema(conn)
            rows = conn.execute("SELECT data FROM themes ORDER BY name").fetchall()
        finally:
            conn.close()
        themes = []
        for row in rows:
            theme = json.loads(row[0])
            if "is_hidden" not in theme:
                theme["is_hidden"] = False
            if "feedback_score" not in theme:
                theme["feedback_score"] = 0
            if include_hidden or not theme.get("is_hidden", False):
                themes.append(theme)
        return themes

    def save_themes(self, themes):
        """Replace the theme table with the given list in one transaction."""
        conn = _connect(self.db_path)
        try:
            _ensure_schema(conn)
            serialized = [(t["name"], json.dumps(t)) for t in themes]
            conn.execute("BEGIN")
            conn.execute("DELETE FROM themes")
            conn.executemany(
                "INSERT INTO themes (name, data) VALUES (?, ?)",
                serialized,
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def migrate_json_to_sqlite(data_dir, db_path):
    """Import the JSON data files into the SQLite database once.

    The migration is skipped when the database file already exists, so
    restarts never overwrite live SQLite data with stale JSON.
    """
    data_dir = Path(data_dir)
    db_path = Path(db_path)
    if db_path.exists():
        return
    hero_repo = SqliteHeroRepository(db_path)
    theme_repo = SqliteThemeRepository(db_path)
    heroes_path = data_dir / "heroes.json"
    themes_path = data_dir / "themes.json"
    heroes = json.loads(heroes_path.read_text()) if heroes_path.exists() else []
    themes = json.loads(themes_path.read_text()) if themes_path.exists() else []
    hero_repo.save_heroes(heroes)
    theme_repo.save_themes(themes)


def create_repositories(data_dir):
    """Build the (hero_repo, theme_repo) pair for the configured backend.

    Backend is read from DOTA_THEMER_BACKEND: "json" (default) or "sqlite".
    """
    backend = os.environ.get("DOTA_THEMER_BACKEND", "json").lower()
    data_dir = Path(data_dir)
    if backend == "json":
        return core.FileHeroRepository(data_dir), core.FileThemeRepository(data_dir)
    if backend == "sqlite":
        db_path = data_dir / "dota.db"
        migrate_json_to_sqlite(data_dir, db_path)
        return SqliteHeroRepository(db_path), SqliteThemeRepository(db_path)
    raise ValueError(f"Unknown storage backend: {backend!r}. Use 'json' or 'sqlite'.")


class SnapshottingThemeRepository:
    """Theme repository wrapper that pushes an S3 snapshot after each save.

    The local SQLite file stays the source of truth; a failed push is
    logged and never breaks the mutation that triggered it.
    """

    def __init__(self, delegate, on_save):
        self.delegate = delegate
        self._on_save = on_save

    def load_themes(self, include_hidden=True):
        return self.delegate.load_themes(include_hidden=include_hidden)

    def save_themes(self, themes):
        result = self.delegate.save_themes(themes)
        try:
            self._on_save(themes)
        except Exception as e:
            import logging_config

            logger = logging_config.get_logger("storage")
            logger.warning(f"Snapshot push failed (local data is safe): {e}")
        return result
