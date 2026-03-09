"""Create a timestamped backup of the SQLite database and media files."""

import sqlite3
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a backup of the database and media files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            default=str(Path.home() / "nullbook-backups"),
            help="Directory to store backups (default: ~/nullbook-backups/)",
        )

    def handle(self, *args, **options):
        output_dir = Path(options["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"nullbook-backup-{timestamp}.tar.gz"
        archive_path = output_dir / archive_name

        db_path = Path(settings.DATABASES["default"]["NAME"])
        media_path = Path(settings.MEDIA_ROOT)

        with tarfile.open(archive_path, "w:gz") as tar:
            if db_path.exists():
                # Use SQLite backup API for a consistent snapshot
                with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp:
                    tmp_path = Path(tmp.name)
                src = sqlite3.connect(str(db_path))
                dst = sqlite3.connect(str(tmp_path))
                src.backup(dst)
                dst.close()
                src.close()
                tar.add(tmp_path, arcname="db.sqlite3")
                tmp_path.unlink()
                self.stdout.write(f"  Added database: {db_path}")

            if media_path.exists() and any(media_path.iterdir()):
                tar.add(media_path, arcname="media")
                self.stdout.write(f"  Added media: {media_path}")

        size_mb = archive_path.stat().st_size / (1024 * 1024)
        self.stdout.write(
            self.style.SUCCESS(f"Backup created: {archive_path} ({size_mb:.1f} MB)")
        )
