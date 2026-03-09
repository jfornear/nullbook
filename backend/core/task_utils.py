"""Utility for dispatching Celery tasks with a thread fallback."""

import logging
import threading

logger = logging.getLogger(__name__)


def run_task(celery_task, *args, **kwargs):
    """Dispatch a Celery task. Falls back to a background thread if broker is unavailable."""
    try:
        celery_task.delay(*args, **kwargs)
    except Exception:
        logger.info("Celery unavailable, running %s in background thread", celery_task.name)
        threading.Thread(target=celery_task, args=args, kwargs=kwargs, daemon=True).start()
