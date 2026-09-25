import logging

from celery.exceptions import CeleryError
from django.conf import settings
from django.db import transaction
from kombu.exceptions import OperationalError as KombuOperationalError
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)


def _is_expected_infrastructure_failure(error):
    if isinstance(
        error,
        (CeleryError, KombuOperationalError, RedisError, ConnectionError, OSError),
    ):
        return True

    # Celery's Redis result backend raises this RuntimeError after exhausting
    # its own reconnect policy; CELERY_TASK_PUBLISH_RETRY does not govern it.
    return isinstance(error, RuntimeError) and (
        "retry limit exceeded" in str(error).lower()
        and "celery result store backend" in str(error).lower()
    )


def enqueue_after_commit(task, **kwargs):
    """Publish a non-critical Celery task only after database commit."""

    def publish():
        task_name = getattr(task, "name", repr(task))

        if not settings.BACKGROUND_JOBS_ENABLED:
            logger.info("Background jobs disabled; skipped task %s.", task_name)
            return

        try:
            task.delay(**kwargs)
        except Exception as error:
            if not _is_expected_infrastructure_failure(error):
                raise
            logger.error("Unable to publish background task %s: %s", task_name, error)

    transaction.on_commit(publish)
