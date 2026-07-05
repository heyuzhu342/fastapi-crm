"""
营销活动管理
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user, pagination_params
from app.models.user import User
from app.models.marketing import Campaign
from app.schemas.common import ResponseModel, ResponseList
from app.services.base_crud import BaseCRUD
from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal
from typing import Optional, List

router = APIRouter(prefix="/campaigns", tags=["📢 营销管理"])
crud = BaseCRUD(Campaign)


class CampaignCreate(BaseModel):
    name: str = Field(..., max_length=200)
    campaign_type: str = Field(default="offline")
    budget: Optional[float] = None
    actual_cost: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    owner_id: Optional[int] = None
    target_audience: Optional[str] = None
    expected_revenue: Optional[float] = None
    description: Optional[str] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    campaign_type: Optional[str] = None
    budget: Optional[float] = None
    actual_cost: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    description: Optional[str] = None


@router.get("", response_model=ResponseList, summary="活动列表")
async def list_campaigns(
    pagination: dict = Depends(pagination_params),
    status: str = None, campaign_type: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = {}
    if status: filters["status"] = status
    if campaign_type: filters["campaign_type"] = campaign_type
    result = await crud.get_list(db, page=pagination["page"], page_size=pagination["page_size"],
        sort_by=pagination["sort_by"], order=pagination["order"],
        search=pagination["search"], search_fields=["name"], filters=filters)
    items = [{"id": c.id, "name": c.name, "campaign_type": c.campaign_type, "budget": float(c.budget) if c.budget else None,
              "actual_cost": float(c.actual_cost) if c.actual_cost else None, "status": c.status,
              "start_date": str(c.start_date) if c.start_date else None, "end_date": str(c.end_date) if c.end_date else None,
              "expected_revenue": float(c.expected_revenue) if c.expected_revenue else None,
              "created_at": str(c.created_at)} for c in result["items"]]
    return ResponseList(data=items, meta={"page": result["page"], "page_size": result["page_size"], "total": result["total"], "total_pages": result["total_pages"]})


@router.post("", response_model=ResponseModel, summary="创建活动")
async def create_campaign(data: CampaignCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    c = Campaign(**data.model_dump())
    db.add(c); await db.flush(); await db.refresh(c)
    return ResponseModel(data={"id": c.id, "name": c.name}, message="活动创建成功")


@router.put("/{cid}", response_model=ResponseModel, summary="更新活动")
async def update_campaign(cid: int, data: CampaignUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    c = await crud.get_by_id(db, cid)
    if not c: raise HTTPException(404, "活动不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        if v is not None: setattr(c, k, v)
    await db.flush()
    return ResponseModel(message="更新成功")


@router.delete("/{cid}", response_model=ResponseModel, summary="删除活动")
async def delete_campaign(cid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ok = await crud.soft_delete(db, cid)
    if not ok: raise HTTPException(404, "活动不存在")
    return ResponseModel(message="已删除")
