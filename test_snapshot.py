import tempfile
import unittest
from pathlib import Path

import core
import snapshot


class FakeS3Client:
    """In-memory stand-in for a boto3 S3 client."""

    def __init__(self, fail_on_upload=False):
        self.objects = {}
        self.fail_on_upload = fail_on_upload
        self.upload_calls = []
        self.download_calls = []

    def upload_file(self, filename, bucket, key):
        self.upload_calls.append((filename, bucket, key))
        if self.fail_on_upload:
            raise RuntimeError("s3 unavailable")
        self.objects[(bucket, key)] = Path(filename).read_bytes()

    def download_file(self, bucket, key, filename):
        self.download_calls.append((bucket, key, filename))
        if (bucket, key) not in self.objects:
            from botocore.exceptions import ClientError

            raise ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}}, "DownloadFile"
            )
        Path(filename).write_bytes(self.objects[(bucket, key)])

    def head_object(self, Bucket, Key):
        if (Bucket, Key) not in self.objects:
            from botocore.exceptions import ClientError

            raise ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
            )
        return {"ContentLength": len(self.objects[(Bucket, Key)])}


class TestSnapshotConfig(unittest.TestCase):
    """SnapshotConfig parses S3 coordinates from the environment."""

    def test_from_env_reads_all_values(self):
        """Bucket and prefix are read from DOTA_THEMER_S3_* variables."""
        import os

        env = {
            "DOTA_THEMER_S3_BUCKET": "my-bucket",
            "DOTA_THEMER_S3_PREFIX": "backups",
        }
        original = {k: os.environ.get(k) for k in env}
        try:
            os.environ.update(env)
            config = snapshot.SnapshotConfig.from_env()
            self.assertEqual(config.bucket, "my-bucket")
            self.assertEqual(config.prefix, "backups")
            self.assertEqual(config.db_key, "backups/dota.db")
        finally:
            for k, v in original.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_from_env_requires_bucket(self):
        """A missing bucket is a configuration error."""
        import os

        original = os.environ.pop("DOTA_THEMER_S3_BUCKET", None)
        try:
            with self.assertRaises(ValueError):
                snapshot.SnapshotConfig.from_env()
        finally:
            if original is not None:
                os.environ["DOTA_THEMER_S3_BUCKET"] = original


class TestSnapshotPush(unittest.TestCase):
    """push_snapshot uploads the database file to S3."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db_path = Path(self.tmp.name) / "dota.db"
        self.db_path.write_bytes(b"database bytes")
        self.s3 = FakeS3Client()
        self.config = snapshot.SnapshotConfig(
            bucket="bucket", prefix="pref", db_path=self.db_path
        )

    def test_push_uploads_to_configured_key(self):
        """push uploads db_path to bucket/prefix/dota.db."""
        snapshot.push_snapshot(self.db_path, self.config, s3_client=self.s3)
        self.assertEqual(self.s3.objects[("bucket", "pref/dota.db")], b"database bytes")

    def test_push_failure_raises(self):
        """An S3 failure propagates so callers can retry/alert."""
        self.s3.fail_on_upload = True
        with self.assertRaises(RuntimeError):
            snapshot.push_snapshot(self.db_path, self.config, s3_client=self.s3)


class TestSnapshotPull(unittest.TestCase):
    """pull_snapshot restores the database file from S3 when present."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.db_path = self.dir / "dota.db"
        self.s3 = FakeS3Client()
        self.s3.objects[("bucket", "pref/dota.db")] = b"remote bytes"
        self.config = snapshot.SnapshotConfig(
            bucket="bucket", prefix="pref", db_path=self.db_path
        )

    def test_pull_restores_missing_local_db(self):
        """A missing local database is downloaded from S3."""
        snapshot.pull_snapshot(self.db_path, self.config, s3_client=self.s3)
        self.assertEqual(self.db_path.read_bytes(), b"remote bytes")

    def test_pull_does_not_overwrite_existing_local_db(self):
        """An existing local database wins; S3 is not downloaded."""
        self.db_path.write_bytes(b"local bytes")
        snapshot.pull_snapshot(self.db_path, self.config, s3_client=self.s3)
        self.assertEqual(self.db_path.read_bytes(), b"local bytes")
        self.assertEqual(self.s3.download_calls, [])

    def test_pull_without_remote_copy_is_a_noop(self):
        """No remote snapshot and no local db leaves nothing behind."""
        empty_s3 = FakeS3Client()
        snapshot.pull_snapshot(self.db_path, self.config, s3_client=empty_s3)
        self.assertFalse(self.db_path.exists())


if __name__ == "__main__":
    unittest.main()


if __name__ == "__main__":
    unittest.main()


class TestDataDirResolution(unittest.TestCase):
    """DOTA_THEMER_DATA_DIR relocates the database consistently (#54)."""

    def setUp(self):
        import os

        self.env = os.environ.copy()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def tearDown(self):
        import os

        os.environ.clear()
        os.environ.update(self.env)

    def test_resolve_data_dir_honors_env(self):
        """core.resolve_data_dir prefers DOTA_THEMER_DATA_DIR over the default."""
        import os

        os.environ["DOTA_THEMER_DATA_DIR"] = self.tmp.name
        self.assertEqual(core.resolve_data_dir(), Path(self.tmp.name))

    def test_resolve_data_dir_defaults_to_packaged_data(self):
        """Without the env var the packaged data directory is used."""
        import os

        os.environ.pop("DOTA_THEMER_DATA_DIR", None)
        self.assertEqual(core.resolve_data_dir(), core.DATA_DIR)

    def test_snapshot_config_uses_env_data_dir(self):
        """build_snapshot_config resolves db_path through the env data dir."""
        import os

        import storage

        os.environ["DOTA_THEMER_S3_BUCKET"] = "my-bucket"
        os.environ["DOTA_THEMER_DATA_DIR"] = self.tmp.name
        try:
            config = storage.build_snapshot_config()
            self.assertEqual(config.db_path, Path(self.tmp.name) / snapshot.DB_FILENAME)
        finally:
            os.environ.pop("DOTA_THEMER_S3_BUCKET", None)

    def test_bot_uses_env_resolved_data_dir(self):
        """bot.py never hardcodes core.DATA_DIR for its storage wiring."""
        content = Path(__file__).parent.joinpath("bot.py").read_text()
        self.assertIn("storage.create_repositories(_data_dir)", content)
        self.assertIn("SqliteSessionStore(_db_path)", content)
        self.assertNotIn("storage.create_repositories(core.DATA_DIR)", content)
        self.assertNotIn("SqliteSessionStore(core.DATA_DIR", content)


class TestLocalDebugDefaults(unittest.TestCase):
    """Local debugging needs zero configuration (#34 follow-up)."""

    def setUp(self):
        import os

        self.env = os.environ.copy()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def tearDown(self):
        import os

        os.environ.clear()
        os.environ.update(self.env)

    def _clear_env(self):
        import os

        for var in (
            "DOTA_THEMER_S3_BUCKET",
            "DOTA_THEMER_S3_PREFIX",
        ):
            os.environ.pop(var, None)

    def test_no_env_means_sqlite_backend_no_s3(self):
        """Bare environment: sqlite repositories, no snapshot config."""
        import storage

        self._clear_env()
        hero_repo, theme_repo = storage.create_repositories(Path(self.tmp.name))
        self.assertIsInstance(hero_repo, storage.SqliteHeroRepository)
        self.assertIsInstance(theme_repo, storage.SqliteThemeRepository)
        self.assertIsNone(storage.build_snapshot_config())

    def test_backend_env_variable_is_ignored(self):
        """DOTA_THEMER_BACKEND no longer selects a backend (#52)."""
        import os

        import storage

        self._clear_env()
        os.environ["DOTA_THEMER_BACKEND"] = "sqllite"
        hero_repo, theme_repo = storage.create_repositories(Path(self.tmp.name))
        self.assertIsInstance(hero_repo, storage.SqliteHeroRepository)
        self.assertIsInstance(theme_repo, storage.SqliteThemeRepository)
