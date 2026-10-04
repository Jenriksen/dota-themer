import json
import os
import tempfile
import unittest
from pathlib import Path

import storage


def write_json_data(data_dir, heroes=None, themes=None):
    """Seed a data dir with JSON files like the repo's data/ directory."""
    data_dir = Path(data_dir)
    if heroes is not None:
        with open(data_dir / "heroes.json", "w") as f:
            json.dump(heroes, f)
    if themes is not None:
        with open(data_dir / "themes.json", "w") as f:
            json.dump(themes, f)


HERO = {
    "id": "axe",
    "name": "Axe",
    "primary_role": "Support",
    "positions": [3, 4],
    "visual_attributes": {"colors": ["red"], "features": ["beard"]},
    "aliases": [],
}

THEME = {
    "name": "Carry Duo",
    "description": "Two hard carries",
    "hero_ids": ["axe", "juggernaut"],
}


class TestSqliteHeroRepository(unittest.TestCase):
    """SqliteHeroRepository persists heroes behind the HeroRepository contract."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db_path = Path(self.tmp.name) / "dota.db"
        self.repo = storage.SqliteHeroRepository(self.db_path)

    def test_save_then_load_round_trip(self):
        """Heroes saved to SQLite come back with all fields intact."""
        self.repo.save_heroes([HERO])
        loaded = self.repo.load_heroes()
        self.assertEqual(loaded, [HERO])

    def test_load_from_empty_db_returns_empty_list(self):
        """A fresh database yields an empty hero list, not an error."""
        self.assertEqual(self.repo.load_heroes(), [])

    def test_hero_visual_attributes_survive_round_trip(self):
        """Nested visual_attributes and aliases survive serialization."""
        hero = dict(HERO, aliases=["red_axe"])
        self.repo.save_heroes([hero])
        loaded = self.repo.load_heroes()[0]
        self.assertEqual(loaded["aliases"], ["red_axe"])
        self.assertEqual(loaded["visual_attributes"]["colors"], ["red"])


class TestSqliteThemeRepository(unittest.TestCase):
    """SqliteThemeRepository persists themes behind the ThemeRepository contract."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db_path = Path(self.tmp.name) / "dota.db"
        self.repo = storage.SqliteThemeRepository(self.db_path)

    def test_save_then_load_round_trip(self):
        """Themes saved to SQLite come back with all fields intact."""
        self.repo.save_themes([THEME])
        loaded = self.repo.load_themes()
        self.assertEqual(
            loaded,
            [dict(THEME, is_hidden=False, feedback_score=0)],
        )

    def test_save_logs_db_size_in_kilobytes(self):
        """A save logs the resulting database size in KiB (#54 request)."""
        import logging

        with self.assertLogs("storage", level="INFO") as captured:
            self.repo.save_themes([THEME])
        messages = [record.getMessage() for record in captured.records]
        size_lines = [m for m in messages if "KiB" in m]
        self.assertEqual(len(size_lines), 1)
        expected_kib = self.db_path.stat().st_size / 1024
        self.assertIn(f"{expected_kib:.1f} KiB", size_lines[0])

    def test_load_applies_json_repository_defaults(self):
        """Loaded themes get is_hidden=False and feedback_score=0 defaults."""
        self.repo.save_themes([{"name": "T1"}])
        loaded = self.repo.load_themes()
        self.assertEqual(
            loaded,
            [{"name": "T1", "is_hidden": False, "feedback_score": 0}],
        )

    def test_load_filters_hidden_themes_when_requested(self):
        """include_hidden=False drops hidden themes, like FileThemeRepository."""
        themes = [
            {"name": "Visible"},
            {"name": "Hidden", "is_hidden": True},
        ]
        self.repo.save_themes(themes)
        visible = self.repo.load_themes(include_hidden=False)
        self.assertEqual(
            visible,
            [{"name": "Visible", "is_hidden": False, "feedback_score": 0}],
        )

    def test_save_is_transactional(self):
        """A failed save leaves the previously saved data untouched."""
        self.repo.save_themes([THEME])

        class BrokenTheme(dict):
            def __getitem__(self, key):
                if key == "name":
                    raise RuntimeError("boom")
                return super().__getitem__(key)

        with self.assertRaises(RuntimeError):
            self.repo.save_themes([BrokenTheme(name="X")])
        loaded = self.repo.load_themes()
        self.assertEqual(loaded, [dict(THEME, is_hidden=False, feedback_score=0)])

    def test_load_from_empty_db_returns_empty_list(self):
        """A fresh database yields an empty theme list, not an error."""
        self.assertEqual(self.repo.load_themes(), [])


class TestSqlitePairStatsStore(unittest.TestCase):
    """SqlitePairStatsStore persists pair stats and refresh state."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db_path = Path(self.tmp.name) / "dota.db"
        self.store = storage.SqlitePairStatsStore(self.db_path)

    def test_save_then_load_round_trip(self):
        """Pair rows saved to SQLite come back with all fields intact."""
        rows = [{"hero1": "Axe", "hero2": "Bane", "games": 10.5, "wins": 5.25}]
        self.store.save_pair_stats(rows)
        self.assertEqual(self.store.load_pair_stats(), rows)

    def test_save_replaces_existing_rows(self):
        """Saving is a full replace, mirroring the hero/theme repositories."""
        self.store.save_pair_stats(
            [{"hero1": "Axe", "hero2": "Bane", "games": 1.0, "wins": 1.0}]
        )
        self.store.save_pair_stats(
            [{"hero1": "Chen", "hero2": "Juggernaut", "games": 2.0, "wins": 1.0}]
        )
        self.assertEqual(len(self.store.load_pair_stats()), 1)
        self.assertEqual(self.store.load_pair_stats()[0]["hero1"], "Chen")

    def test_load_from_empty_db_returns_empty_list(self):
        """A fresh database yields no pair rows, not an error."""
        self.assertEqual(self.store.load_pair_stats(), [])

    def test_get_state_missing_returns_default(self):
        self.assertIsNone(self.store.get_state("last_match_id"))
        self.assertEqual(self.store.get_state("last_match_id", "0"), "0")

    def test_set_state_round_trip(self):
        """Refresh state (the match cursor) survives persistence."""
        self.store.set_state("last_match_id", 12345)
        self.assertEqual(self.store.get_state("last_match_id"), "12345")

    def test_set_state_overwrites_previous_value(self):
        self.store.set_state("last_match_id", "1")
        self.store.set_state("last_match_id", "2")
        self.assertEqual(self.store.get_state("last_match_id"), "2")


class TestJsonToSqliteMigration(unittest.TestCase):
    """migrate_json_to_sqlite imports the JSON files in one transaction."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data_dir = Path(self.tmp.name)
        self.db_path = self.data_dir / "dota.db"

    def test_migration_copies_heroes_and_themes(self):
        """Migration copies all heroes and themes into the database."""
        write_json_data(
            self.data_dir,
            heroes=[HERO],
            themes=[THEME],
        )
        storage.migrate_json_to_sqlite(self.data_dir, self.db_path)
        hero_repo = storage.SqliteHeroRepository(self.db_path)
        theme_repo = storage.SqliteThemeRepository(self.db_path)
        self.assertEqual(hero_repo.load_heroes(), [HERO])
        self.assertEqual(
            theme_repo.load_themes(),
            [dict(THEME, is_hidden=False, feedback_score=0)],
        )

    def test_migration_is_idempotent(self):
        """Running migration twice does not duplicate rows."""
        write_json_data(self.data_dir, heroes=[HERO], themes=[THEME])
        storage.migrate_json_to_sqlite(self.data_dir, self.db_path)
        storage.migrate_json_to_sqlite(self.data_dir, self.db_path)
        theme_repo = storage.SqliteThemeRepository(self.db_path)
        self.assertEqual(len(theme_repo.load_themes()), 1)

    def test_migration_skipped_when_db_exists(self):
        """Migration is a no-op when the database file already exists."""
        write_json_data(self.data_dir, heroes=[HERO], themes=[THEME])
        self.db_path.write_bytes(b"existing db sentinel")
        storage.migrate_json_to_sqlite(self.data_dir, self.db_path)
        self.assertEqual(self.db_path.read_bytes(), b"existing db sentinel")


class TestBackendSelection(unittest.TestCase):
    """create_repositories always builds the SQLite repositories (#52)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data_dir = Path(self.tmp.name)

    def test_always_returns_sqlite_repositories(self):
        """SQLite is the only backend; JSON data is imported once."""
        write_json_data(self.data_dir, heroes=[HERO], themes=[THEME])
        hero_repo, theme_repo = storage.create_repositories(self.data_dir)
        self.assertIsInstance(hero_repo, storage.SqliteHeroRepository)
        self.assertIsInstance(theme_repo, storage.SqliteThemeRepository)
        # First use migrates the JSON data into the new database
        self.assertEqual(hero_repo.load_heroes(), [HERO])
        self.assertEqual(len(theme_repo.load_themes()), 1)

    def test_no_json_repository_classes_remain(self):
        """The File repositories are removed from the codebase (#52)."""
        import core

        self.assertFalse(hasattr(core, "FileHeroRepository"))
        self.assertFalse(hasattr(core, "FileThemeRepository"))


class TestSqliteRepositoriesSatisfyProtocols(unittest.TestCase):
    """The SQLite repositories pass core's runtime-checkable Protocols."""

    def test_repositories_are_protocol_instances(self):
        import core

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db_path = Path(tmp.name) / "dota.db"
        self.assertTrue(
            isinstance(storage.SqliteHeroRepository(db_path), core.HeroRepository)
        )
        self.assertTrue(
            isinstance(storage.SqliteThemeRepository(db_path), core.ThemeRepository)
        )


if __name__ == "__main__":
    unittest.main()


class TestSnapshottingThemeRepository(unittest.TestCase):
    """SnapshottingThemeRepository pushes to S3 after every save (#34)."""

    def setUp(self):
        self.pushed = []

    def test_save_pushes_snapshot(self):
        """Every save_themes call triggers a snapshot push."""

        class RecordingRepo:
            def __init__(self):
                self.saved = []

            def load_themes(self, include_hidden=True):
                return self.saved

            def save_themes(self, themes):
                self.saved = themes

        inner = RecordingRepo()
        wrapper = storage.SnapshottingThemeRepository(
            inner, on_save=lambda themes: self.pushed.append(list(themes))
        )
        wrapper.save_themes([{"name": "T"}])
        self.assertEqual(inner.saved, [{"name": "T"}])
        self.assertEqual(self.pushed, [[{"name": "T"}]])

    def test_wrapper_satisfies_theme_repository_protocol(self):
        """The wrapper passes core's runtime-checkable ThemeRepository."""
        import core

        class DummyRepo:
            def load_themes(self, include_hidden=True):
                return []

            def save_themes(self, themes):
                pass

        wrapper = storage.SnapshottingThemeRepository(
            DummyRepo(), on_save=lambda themes: None
        )
        self.assertTrue(isinstance(wrapper, core.ThemeRepository))

    def test_push_failure_does_not_break_save(self):
        """A failing push is logged, not raised: local SQLite is the source of truth."""

        class FailingPushRepo:
            def load_themes(self, include_hidden=True):
                return []

            def save_themes(self, themes):
                pass

        def broken_push(themes):
            raise RuntimeError("s3 down")

        wrapper = storage.SnapshottingThemeRepository(
            FailingPushRepo(), on_save=broken_push
        )
        try:
            wrapper.save_themes([{"name": "T"}])
        except RuntimeError:
            self.fail("push failure must not propagate")


class TestSnapshottingPairStatsStore(unittest.TestCase):
    """SnapshottingPairStatsStore pushes to S3 after every write."""

    def setUp(self):
        self.pushed = []

    def _wrapper(self, delegate=None, on_write=None):
        delegate = delegate or self._recording_store()
        return storage.SnapshottingPairStatsStore(
            delegate, on_write=on_write or (lambda: self.pushed.append(True))
        )

    def _recording_store(self):
        class RecordingStore:
            def __init__(self):
                self.rows = []
                self.state = {}

            def load_pair_stats(self):
                return list(self.rows)

            def save_pair_stats(self, rows):
                self.rows = list(rows)

            def get_state(self, key, default=None):
                return self.state.get(key, default)

            def set_state(self, key, value):
                self.state[key] = str(value)

        return RecordingStore()

    def test_save_pushes_snapshot(self):
        """Every save_pair_stats call triggers a snapshot push."""
        store = self._recording_store()
        wrapper = self._wrapper(store)
        wrapper.save_pair_stats(
            [{"hero1": "Axe", "hero2": "Bane", "games": 1, "wins": 1}]
        )
        self.assertEqual(store.rows[0]["hero2"], "Bane")
        self.assertEqual(self.pushed, [True])

    def test_state_update_pushes_snapshot(self):
        """Cursor updates push too, so restores resume from the cursor."""
        store = self._recording_store()
        wrapper = self._wrapper(store)
        wrapper.set_state("last_match_id", 42)
        self.assertEqual(store.state["last_match_id"], "42")
        self.assertEqual(self.pushed, [True])

    def test_reads_do_not_push(self):
        """Loads and state reads never upload snapshots."""
        wrapper = self._wrapper()
        wrapper.load_pair_stats()
        wrapper.get_state("last_match_id")
        self.assertEqual(self.pushed, [])

    def test_push_failure_does_not_break_write(self):
        """A failing push is logged, not raised: local SQLite is the truth."""

        class FailingPushStore:
            def load_pair_stats(self):
                return []

            def save_pair_stats(self, rows):
                pass

            def get_state(self, key, default=None):
                return default

            def set_state(self, key, value):
                pass

        def broken_push():
            raise RuntimeError("s3 down")

        wrapper = self._wrapper(FailingPushStore(), on_write=broken_push)
        try:
            wrapper.save_pair_stats([])
            wrapper.set_state("last_match_id", 1)
        except RuntimeError:
            self.fail("push failure must not propagate")
