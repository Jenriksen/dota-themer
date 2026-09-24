"""S3 snapshot push/pull for the SQLite database (issue #34).

Implements the snapshot pattern: the database runs as a local SQLite file;
on save it can be uploaded to S3, and at startup a missing local copy can
be restored from S3. S3 is never mounted as a live filesystem.
"""

import os
from dataclasses import dataclass
from pathlib import Path

DB_FILENAME = "dota.db"


@dataclass
class SnapshotConfig:
    """S3 coordinates for the database snapshot."""

    bucket: str
    prefix: str
    db_path: Path

    @property
    def db_key(self):
        """Object key of the database snapshot inside the bucket."""
        return f"{self.prefix}/{DB_FILENAME}".lstrip("/")

    @classmethod
    def from_env(cls, db_path=None):
        """Build the config from DOTA_THEMER_S3_BUCKET/PREFIX variables."""
        if db_path is None:
            import core

            db_path = core.DATA_DIR / DB_FILENAME
        bucket = os.environ.get("DOTA_THEMER_S3_BUCKET")
        if not bucket:
            raise ValueError("DOTA_THEMER_S3_BUCKET is required for S3 snapshots")
        prefix = os.environ.get("DOTA_THEMER_S3_PREFIX", "").strip("/")
        return cls(bucket=bucket, prefix=prefix, db_path=Path(db_path))


def default_s3_client():
    """Create the boto3 S3 client (imported lazily)."""
    import boto3

    return boto3.client("s3")


def push_snapshot(db_path, config, s3_client=None):
    """Upload the database file to S3 as the latest snapshot."""
    s3_client = s3_client or default_s3_client()
    s3_client.upload_file(str(db_path), config.bucket, config.db_key)


def pull_snapshot(db_path, config, s3_client=None):
    """Restore the database from S3 when no local copy exists.

    An existing local file always wins: snapshots restore lost instances,
    they never overwrite live data.
    """
    db_path = Path(db_path)
    if db_path.exists():
        return
    s3_client = s3_client or default_s3_client()
    try:
        s3_client.download_file(config.bucket, config.db_key, str(db_path))
    except Exception:
        # A missing or unreachable remote snapshot leaves startup to
        # migration/local seed data instead
        if db_path.exists():
            db_path.unlink()
        return
