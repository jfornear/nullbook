"""Celery tasks for file import automation."""

import logging
import os

from celery import shared_task

logger = logging.getLogger(__name__)

WATCHED_EXTENSIONS = {".csv", ".ofx", ".qfx", ".qif"}


@shared_task
def watch_downloads_folder():
    """Scan ~/Downloads for new bank statement files and queue them for import.

    This is an optional convenience task. Files are detected but not
    auto-imported — they create ImportBatch records in 'pending' status
    for user review.
    """
    from django.contrib.auth import get_user_model

    from imports.models import ImportBatch
    from imports.parsers import parse_file

    User = get_user_model()
    downloads_dir = os.path.expanduser("~/Downloads")

    if not os.path.isdir(downloads_dir):
        logger.info("Downloads directory not found: %s", downloads_dir)
        return "Downloads directory not found"

    # Get the local user (single-user app)
    user = User.objects.first()
    if not user:
        return "No user found"

    # Track already-processed files
    processed_files = set(
        ImportBatch.objects.values_list("file_name", flat=True)
    )

    new_files = 0
    for filename in os.listdir(downloads_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in WATCHED_EXTENSIONS:
            continue
        if filename in processed_files:
            continue

        filepath = os.path.join(downloads_dir, filename)
        if not os.path.isfile(filepath):
            continue

        try:
            with open(filepath, encoding="utf-8-sig") as f:
                content = f.read()

            parsed = parse_file(content, filename)
            if parsed["row_count"] == 0:
                continue

            ImportBatch.objects.create(
                user=user,
                account_id=None,
                file_name=filename,
                status="pending",
                row_count=parsed["row_count"],
                column_mapping=parsed.get("detected_mapping", {}),
            )
            new_files += 1
            logger.info("Detected new financial file: %s (%d rows)", filename, parsed["row_count"])

        except Exception:
            logger.exception("Error processing file: %s", filename)

    return f"Found {new_files} new files in Downloads"
