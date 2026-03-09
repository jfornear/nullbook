"""Restore a backup archive created by the backup command."""

import shutil
import tarfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Restore database and media files from a backup archive"

    def add_arguments(self, parser):
        parser.add_argument("archive", help="Path to the backup .tar.gz archive")

    def handle(self, *args, **options):
        archive_path = Path(options["archive"])
        if not archive_path.exists():
            raise CommandError(f"Archive not found: {archive_path}")

        db_path = Path(settings.DATABASES["default"]["NAME"])
        media_path = Path(settings.MEDIA_ROOT)

        with tarfile.open(archive_path, "r:gz") as tar:
            # Validate all members for path traversal before extracting
            for member in tar.getmembers():
                member_path = Path(member.name)
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise CommandError(
                        f"Refusing to extract unsafe path: {member.name}"
                    )

            members = tar.getnames()

            if "db.sqlite3" in members:
                tar.extract("db.sqlite3", path=db_path.parent)
                extracted = db_path.parent / "db.sqlite3"
                if extracted != db_path:
                    shutil.move(str(extracted), str(db_path))
                self.stdout.write(f"  Restored database to {db_path}")

            media_members = [
                tar.getmember(m) for m in members
                if m.startswith("media/")
            ]
            if media_members:
                media_path.mkdir(parents=True, exist_ok=True)
                tar.extractall(path=media_path.parent, members=media_members)
                self.stdout.write(f"  Restored media to {media_path}")

        self.stdout.write(self.style.SUCCESS(f"Restore complete from {archive_path}"))
