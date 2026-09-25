"""SQLite storage for dota-themer (#52).

SQLite is the only storage backend: heroes, themes, and the bot session
(message/thread tracking) all persist to a single database file. The JSON
data files are read once by the one-shot JSON migration when the database
does not exist yet.
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import core
import snapshot


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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS suggestion_messages (
            message_id INTEGER PRIMARY KEY,
            theme_name TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            locked BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS modification_threads (
            thread_id INTEGER PRIMARY KEY,
            theme_name TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (message_id)
                REFERENCES suggestion_messages(message_id)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_with_threads
        ON modification_threads(message_id)
    """)


def _log_save_size(theme_count, size_kib):
    """Log the database size after a save (single source for the message)."""
    import logging_config

    logger = logging_config.get_logger("storage")
    logger.info(f"Saved {theme_count} themes; database size: {size_kib:.1f} KiB")


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
        size_kib = self.db_path.stat().st_size / 1024
        _log_save_size(len(themes), size_kib)


def _parse_dt(value):
    """Parse an ISO 8601 timestamp from the database into an aware datetime."""
    return datetime.fromisoformat(value)


def _format_dt(value):
    """Serialize a datetime to ISO 8601, assuming naive values are UTC."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


class SqliteSessionStore:
    """Message/thread session tracking backed by SQLite tables (#52)."""

    def __init__(self, db_path):
        self.db_path = Path(db_path)

    def load_suggestions(self):
        """Return {message_id: {theme_name, timestamp, locked}} from the db."""
        conn = _connect(self.db_path)
        try:
            _ensure_schema(conn)
            rows = conn.execute(
                "SELECT message_id, theme_name, timestamp, locked"
                " FROM suggestion_messages"
            ).fetchall()
        finally:
            conn.close()
        return {
            int(row[0]): {
                "theme_name": row[1],
                "timestamp": _parse_dt(row[2]),
                "locked": bool(row[3]),
            }
            for row in rows
        }

    def load_threads(self):
        """Return {thread_id: {theme_name, user_id, message_id, created_at}}."""
        conn = _connect(self.db_path)
        try:
            _ensure_schema(conn)
            rows = conn.execute(
                "SELECT thread_id, theme_name, user_id, message_id, created_at"
                " FROM modification_threads"
            ).fetchall()
        finally:
            conn.close()
        return {
            int(row[0]): {
                "theme_name": row[1],
                "user_id": int(row[2]),
                "message_id": int(row[3]),
                "created_at": _parse_dt(row[4]),
            }
            for row in rows
        }

    def save_suggestion(self, message_id, info):
        """Insert or replace one suggestion row."""
        conn = _connect(self.db_path)
        try:
            _ensure_schema(conn)
            conn.execute(
                "INSERT OR REPLACE INTO suggestion_messages"
                " (message_id, theme_name, timestamp, locked)"
                " VALUES (?, ?, ?, ?)",
                (
                    message_id,
                    info["theme_name"],
                    _format_dt(info["timestamp"]),
                    bool(info["locked"]),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def delete_suggestion(self, message_id):
        """Remove one suggestion row (threads keep their message_id value)."""
        conn = _connect(self.db_path)
        try:
            _ensure_schema(conn)
            conn.execute(
                "DELETE FROM suggestion_messages WHERE message_id = ?",
                (message_id,),
            )
            conn.commit()
        finally:
            conn.close()

    def save_thread(self, thread_id, info):
        """Insert or replace one thread row."""
        conn = _connect(self.db_path)
        try:
            _ensure_schema(conn)
            conn.execute(
                "INSERT OR REPLACE INTO modification_threads"
                " (thread_id, theme_name, user_id, message_id, created_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    thread_id,
                    info["theme_name"],
                    info["user_id"],
                    info["message_id"],
                    _format_dt(info["created_at"]),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def delete_thread(self, thread_id):
        """Remove one thread row."""
        conn = _connect(self.db_path)
        try:
            _ensure_schema(conn)
            conn.execute(
                "DELETE FROM modification_threads WHERE thread_id = ?",
                (thread_id,),
            )
            conn.commit()
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
    """Build the (hero_repo, theme_repo) pair: always SQLite (#52).

    The JSON data files are imported once on first use, when the database
    file does not exist yet.
    """
    data_dir = Path(data_dir)
    db_path = data_dir / snapshot.DB_FILENAME
    migrate_json_to_sqlite(data_dir, db_path)
    return SqliteHeroRepository(db_path), SqliteThemeRepository(db_path)


def build_snapshot_config():
    """Return the S3 snapshot config, or None when S3 is not configured.

    All configuration comes from the environment so deployments can be
    rendered as IaC; an unconfigured environment keeps local debugging
    fully functional (json backend, no S3 traffic).
    """
    if not os.environ.get("DOTA_THEMER_S3_BUCKET"):
        return None
    return snapshot.SnapshotConfig.from_env(
        core.resolve_data_dir() / snapshot.DB_FILENAME
    )


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
