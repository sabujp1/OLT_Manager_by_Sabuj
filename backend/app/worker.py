from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create the celery application instance
celery_app = Celery(
    "olt_noc_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Force auto-discover of tasks defined in app.services.polling.tasks
    imports=("app.services.polling.tasks",)
)

# Configure periodic scheduler (Celery Beat)
celery_app.conf.beat_schedule = {
    "olt-fast-poll-30s": {
        "task": "app.services.polling.tasks.fast_poll_olts",
        "schedule": float(settings.FAST_POLL_INTERVAL),
    },
    "olt-port-metrics-2m": {
        "task": "app.services.polling.tasks.metric_poll_ports",
        "schedule": float(settings.METRIC_POLL_INTERVAL),
    },
    "onu-inventory-sync-10m": {
        "task": "app.services.polling.tasks.inventory_sync_onus",
        "schedule": float(settings.INVENTORY_SYNC_INTERVAL),
    },
}
