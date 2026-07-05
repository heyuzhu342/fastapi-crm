"""
数据看板 + 报表 + 通知 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user, pagination_params, require_superuser
from app.models.user import User, AuditLog
from app.models.customer import Customer
from app.models.sales import Lead, Opportunity, Contract
from app.models.service import Ticket
from app.models.product import Product
from app.schemas.common import ResponseModel, ResponseList

router = APIRouter(prefix="/dashboard", tags=["📈 数据看板"])
notify_router = APIRouter(prefix="/notifications", tags=["🔔 通知消息"])
log_router = APIRouter(prefix="/logs", tags=["📋 操作日志"])


@router.get("/stats", response_model=ResponseModel, summary="核心指标")
async def dashboard_stats(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """仪表盘核心数据"""
    # 客户总数
    r = await db.execute(select(func.count(Customer.id)).where(Customer.is_deleted == False))
    customer_count = r.scalar() or 0
    # 活跃线索
    r = await db.execute(select(func.count(Lead.id)).where(Lead.is_deleted == False, Lead.status.in_(["new", "contacted"])))
    lead_count = r.scalar() or 0
    # 进行中商机
    r = await db.execute(select(func.count(Opportunity.id), func.coalesce(func.sum(Opportunity.amount), 0))
        .where(Opportunity.is_deleted == False, Opportunity.stage.notin_(["won", "lost"])))
    row = r.one()
    opp_count, opp_amount = row[0], float(row[1])
    # 待处理工单
    r = await db.execute(select(func.count(Ticket.id)).where(Ticket.status.in_(["open", "processing"])))
    ticket_count = r.scalar() or 0
    # 本月成交
    r = await db.execute(select(func.coalesce(func.sum(Contract.amount), 0))
        .where(Contract.is_deleted == False, Contract.status == "active"))
    monthly_revenue = float(r.scalar() or 0)

    return ResponseModel(data={
        "customer_count": customer_count, "lead_count": lead_count,
        "opportunity_count": opp_count, "opportunity_amount": opp_amount,
        "ticket_count": ticket_count, "monthly_revenue": monthly_revenue,
    })


@router.get("/trends", response_model=ResponseModel, summary="销售趋势")
async def sales_trends(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """近6个月销售趋势 (模拟数据用于演示)"""
    trends = [
        {"month": "1月", "revenue": 420000, "target": 500000},
        {"month": "2月", "revenue": 380000, "target": 500000},
        {"month": "3月", "revenue": 560000, "target": 550000},
        {"month": "4月", "revenue": 720000, "target": 600000},
        {"month": "5月", "revenue": 610000, "target": 600000},
        {"month": "6月", "revenue": 856400, "target": 650000},
    ]
    return ResponseModel(data=trends)


@notify_router.get("", response_model=ResponseList, summary="通知列表")
async def list_notifications(
    pagination: dict = Depends(pagination_params),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """当前用户的通知"""
    from app.models.notification import Notification
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .offset(pagination["offset"]).limit(pagination["page_size"])
    )
    notifs = result.scalars().all()
    total_r = await db.execute(select(func.count(Notification.id)).where(Notification.user_id == current_user.id))
    total = total_r.scalar() or 0
    import math
    items = [{"id": n.id, "title": n.title, "content": n.content, "notify_type": n.notify_type,
              "is_read": n.is_read, "created_at": str(n.created_at)} for n in notifs]
    return ResponseList(data=items, meta={"page": pagination["page"], "page_size": pagination["page_size"],
        "total": total, "total_pages": max(1, math.ceil(total / pagination["page_size"]))})


@log_router.get("", response_model=ResponseList, summary="操作日志")
async def list_logs(
    pagination: dict = Depends(pagination_params),
    current_user: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    """系统操作日志"""
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).offset(pagination["offset"]).limit(pagination["page_size"])
    result = await db.execute(query)
    logs = result.scalars().all()
    total_r = await db.execute(select(func.count(AuditLog.id)))
    total = total_r.scalar() or 0
    import math
    items = [{"id": l.id, "user_id": l.user_id, "username": l.username, "action": l.action,
              "resource": l.resource, "detail": l.detail, "ip_address": l.ip_address,
              "status": l.status, "created_at": str(l.created_at)} for l in logs]
    return ResponseList(data=items, meta={"page": pagination["page"], "page_size": pagination["page_size"],
        "total": total, "total_pages": max(1, math.ceil(total / pagination["page_size"]))})


@log_router.delete("/{log_id}", response_model=ResponseModel, summary="删除日志")
async def delete_log(log_id: int, current_user: User = Depends(require_superuser), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log: raise HTTPException(status_code=404, detail="日志不存在")
    await db.delete(log); await db.flush()
    return ResponseModel(message="已删除")


@log_router.delete("", response_model=ResponseModel, summary="清空日志")
async def clear_logs(current_user: User = Depends(require_superuser), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import delete
    await db.execute(delete(AuditLog))
    await db.flush()
    return ResponseModel(message="日志已清空")
