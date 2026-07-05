"""
报表 & 定时任务
"""
from app.core.celery_app import celery_app
from datetime import datetime


@celery_app.task(name="send_weekly_report")
def send_weekly_report():
    """
    发送周报
    每周一早上8点执行 (Celery Beat 调度)
    """
    # TODO: 生成上周销售数据摘要
    # TODO: 发送给管理员/销售经理
    print(f"[{datetime.now()}] 周报任务执行中...")
    return {"status": "ok", "message": "周报已发送"}


@celery_app.task(name="check_sla_overdue_tickets")
def check_sla_overdue_tickets():
    """
    检查 SLA 超时工单
    每30分钟执行一次
    """
    # TODO: 查询超时工单并发送通知
    print(f"[{datetime.now()}] SLA 超时检查中...")
    return {"status": "ok", "overdue_count": 0}


@celery_app.task(name="generate_monthly_report")
def generate_monthly_report(month: str = None):
    """
    生成月度报表
    """
    month = month or datetime.now().strftime("%Y-%m")
    # TODO: 聚合月度数据、生成 Excel 文件
    print(f"[{datetime.now()}] 月度报表生成中: {month}")
    return {"status": "ok", "month": month}
