"""
数据清理定时任务
"""
from app.core.celery_app import celery_app
from datetime import datetime, timedelta


@celery_app.task(name="cleanup_old_logs")
def cleanup_old_logs():
    """
    清理旧操作日志
    每天凌晨2点执行 — 删除90天前的日志
    """
    cutoff_date = datetime.utcnow() - timedelta(days=90)
    print(f"[{datetime.now()}] 清理 {cutoff_date} 之前的日志...")
    # TODO: 执行 DELETE FROM sys_audit_log WHERE created_at < cutoff_date
    return {"status": "ok", "cutoff_date": cutoff_date.isoformat()}


@celery_app.task(name="cleanup_expired_tokens")
def cleanup_expired_tokens():
    """
    清理过期 Token（Redis）
    每天凌晨 3 点执行
    """
    import redis
    from app.core.config import settings
    r = redis.from_url(settings.REDIS_URL)
    # 扫描并删除过期的 refresh token 黑名单
    # TODO: 实现 token 黑名单机制
    return {"status": "ok"}
