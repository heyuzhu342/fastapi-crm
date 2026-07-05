"""
客户服务工单管理
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.core.database import get_db
from app.api.deps import get_current_user, pagination_params
from app.models.user import User
from app.models.service import Ticket, TicketComment
from app.schemas.common import ResponseModel, ResponseList
from app.services.base_crud import BaseCRUD
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(prefix="/tickets", tags=["🎫 工单管理"])
crud = BaseCRUD(Ticket)


def gen_ticket_no() -> str:
    return f"TK-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


class TicketCreate(BaseModel):
    title: str = Field(..., max_length=200)
    customer_id: Optional[int] = None
    ticket_type: str = Field(default="question")
    priority: str = Field(default="normal")
    description: str


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    ticket_type: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[int] = None
    resolution: Optional[str] = None
    satisfaction_score: Optional[int] = Field(default=None, ge=1, le=5)


class CommentCreate(BaseModel):
    content: str
    is_internal: bool = False


@router.get("", response_model=ResponseList, summary="工单列表")
async def list_tickets(
    pagination: dict = Depends(pagination_params),
    status: str = None, priority: str = None, assigned_to: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = {}
    if status: filters["status"] = status
    if priority: filters["priority"] = priority
    if assigned_to: filters["assigned_to"] = assigned_to
    result = await crud.get_list(db, page=pagination["page"], page_size=pagination["page_size"],
        sort_by=pagination["sort_by"], order=pagination["order"],
        search=pagination["search"], search_fields=["title", "ticket_no"], filters=filters)
    items = [{"id": t.id, "ticket_no": t.ticket_no, "title": t.title, "ticket_type": t.ticket_type,
              "priority": t.priority, "status": t.status, "assigned_to": t.assigned_to,
              "satisfaction_score": t.satisfaction_score, "created_at": str(t.created_at)} for t in result["items"]]
    return ResponseList(data=items, meta={"page": result["page"], "page_size": result["page_size"], "total": result["total"], "total_pages": result["total_pages"]})


@router.get("/{tid}", response_model=ResponseModel, summary="工单详情")
async def get_ticket(tid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).options(joinedload(Ticket.comments)).where(Ticket.id == tid))
    t = result.unique().scalar_one_or_none()
    if not t: raise HTTPException(404, "工单不存在")
    return ResponseModel(data={"id": t.id, "ticket_no": t.ticket_no, "title": t.title, "ticket_type": t.ticket_type,
        "priority": t.priority, "status": t.status, "description": t.description, "resolution": t.resolution,
        "satisfaction_score": t.satisfaction_score, "customer_id": t.customer_id,
        "assigned_to": t.assigned_to, "created_at": str(t.created_at), "closed_at": str(t.closed_at) if t.closed_at else None,
        "comments": [{"id": c.id, "user_id": c.user_id, "content": c.content, "is_internal": c.is_internal, "created_at": str(c.created_at)} for c in t.comments]})


@router.post("", response_model=ResponseModel, summary="创建工单")
async def create_ticket(data: TicketCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    t = Ticket(ticket_no=gen_ticket_no(), created_by=current_user.id, **data.model_dump())
    db.add(t); await db.flush(); await db.refresh(t)
    return ResponseModel(data={"id": t.id, "ticket_no": t.ticket_no}, message="工单创建成功")


@router.put("/{tid}", response_model=ResponseModel, summary="更新工单")
async def update_ticket(tid: int, data: TicketUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    t = await crud.get_by_id(db, tid)
    if not t: raise HTTPException(404, "工单不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        if v is not None: setattr(t, k, v)
    if data.status == "closed" and not t.closed_at:
        t.closed_at = datetime.utcnow()
    await db.flush()
    return ResponseModel(message="更新成功")


@router.post("/{tid}/comments", response_model=ResponseModel, summary="添加回复")
async def add_comment(tid: int, data: CommentCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    t = await crud.get_by_id(db, tid)
    if not t: raise HTTPException(404, "工单不存在")
    c = TicketComment(ticket_id=tid, user_id=current_user.id, content=data.content, is_internal=data.is_internal)
    db.add(c); await db.flush()
    return ResponseModel(data={"id": c.id}, message="回复成功")
