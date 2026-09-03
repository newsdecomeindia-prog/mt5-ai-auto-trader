import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, List
from config import settings
from core import get_logger

logger = get_logger("general")

BACKUP_DIR = Path("database/backups")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


class DatabaseBackupManager:
    """
    Manages SQLite database backup and restore operations.
    """

    @staticmethod
    def backup_database() -> Tuple[bool, str]:
        """Creates a timestamped backup copy of the SQLite database."""
        db_url = settings.DATABASE_URL
        if not db_url.startswith("sqlite:///"):
            return False, "Backup is currently supported for SQLite databases only."

        db_file = db_url.replace("sqlite:///", "")
        if not os.path.exists(db_file):
            return False, f"Database file {db_file} not found."

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"mt5_backup_{timestamp}.db"
        backup_path = BACKUP_DIR / backup_filename

        try:
            src_conn = sqlite3.connect(db_file)
            dst_conn = sqlite3.connect(backup_path)
            with dst_conn:
                src_conn.backup(dst_conn)
            src_conn.close()
            dst_conn.close()

            logger.info(f"Database backed up successfully to {backup_path}")
            return True, str(backup_path)
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False, str(e)

    @staticmethod
    def list_backups() -> List[str]:
        """Returns list of available database backups."""
        if not BACKUP_DIR.exists():
            return []
        return sorted([f.name for f in BACKUP_DIR.glob("*.db")], reverse=True)

    @staticmethod
    def restore_database(backup_filename: str) -> Tuple[bool, str]:
        """Restores database from specified backup file."""
        backup_path = BACKUP_DIR / backup_filename
        if not backup_path.exists():
            return False, f"Backup file {backup_filename} does not exist."

        db_url = settings.DATABASE_URL
        db_file = db_url.replace("sqlite:///", "")

        try:
            shutil.copy2(backup_path, db_file)
            logger.info(f"Database restored successfully from {backup_path}")
            return True, "Database restored successfully."
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False, str(e)


db_backup_manager = DatabaseBackupManager()
