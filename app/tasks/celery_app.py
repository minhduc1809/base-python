from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "aisoft_tasks",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.SERVER_TIMEZONE,
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour limit for heavy batch import tasks
    beat_schedule={
        # Clear audit logs older than 2 years every 12 hours
        "clear-old-audit-logs": {
            "task": "audit_log.clear_old_logs",
            "schedule": 43200.0,  # 12 hours in seconds
            "args": (2,),  # years=2
        },
    },
)
