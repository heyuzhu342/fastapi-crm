"""
Celery 异步任务 + 定时任务 (Celery Beat)
开发环境没有 Redis 时自动降级为空实现
"""
from app.core.config import settings

try:
    from celery import Celery
    from celery.schedules import crontab

    celery_app = Celery(
        "fastapi_crm",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=[
            "app.tasks.email_tasks",
            "app.tasks.report_tasks",
            "app.tasks.cleanup_tasks",
        ],
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Shanghai",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_soft_time_limit=600,
        task_time_limit=900,
    )

    celery_app.conf.beat_schedule = {
        "cleanup-old-logs-every-night": {
            "task": "app.tasks.cleanup_tasks.cleanup_old_logs",
            "schedule": crontab(hour=2, minute=0),
        },
        "send-weekly-report": {
            "task": "app.tasks.report_tasks.send_weekly_report",
            "schedule": crontab(hour=8, minute=0, day_of_week=1),
        },
        "check-sla-tickets": {
            "task": "app.tasks.report_tasks.check_sla_overdue_tickets",
            "schedule": crontab(minute="*/30"),
        },
    }

except ImportError:
    # 开发环境：Celery / Redis 未安装，提供空实现
    class _FakeCelery:
        def task(self, *args, **kwargs):
            def decorator(fn):
                def wrapper(*a, **kw):
                    fn(*a, **kw)
                wrapper.delay = lambda *a, **kw: None
                return wrapper
            return decorator

    celery_app = _FakeCelery()
