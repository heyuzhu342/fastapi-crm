"""
商机管理接口
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, pagination_params
from app.models.user import User
from app.models.sales import Opportunity
from app.schemas.sales import OpportunityCreate, OpportunityUpdate, OpportunityOut
from app.schemas.common import ResponseModel, ResponseList
from app.services.base_crud import BaseCRUD

router = APIRouter(prefix="/opportunities", tags=["💼 商机管理"])
opp_crud = BaseCRUD(Opportunity)

STAGES = [
    ("initial_contact", "初步接触"), ("needs_analysis", "需求分析"),
    ("quotation", "报价"), ("negotiation", "谈判"),
    ("won", "已成交"), ("lost", "已丢单"),
]


@router.get("", response_model=ResponseList[OpportunityOut], summary="商机列表")
async def list_opportunities(
    pagination: dict = Depends(pagination_params),
    stage: str = None, owner_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """商机列表（支持阶段筛选）"""
    filters = {}
    if stage: filters["stage"] = stage
    if owner_id: filters["owner_id"] = owner_id

    # 排除已关闭的（won/lost），除非明确筛选
    if not stage:
        result = await opp_crud.get_list(
            db, page=pagination["page"], page_size=pagination["page_size"],
            sort_by=pagination["sort_by"], order=pagination["order"],
            search=pagination["search"], search_fields=["name"],
            filters=filters,
        )
    else:
        result = await opp_crud.get_list(
            db, page=pagination["page"], page_size=pagination["page_size"],
            sort_by=pagination["sort_by"], order=pagination["order"],
            search=pagination["search"], search_fields=["name"],
            filters=filters,
        )

    items = [OpportunityOut.model_validate(o) for o in result["items"]]
    return ResponseList(data=items, meta={
        "page": result["page"], "page_size": result["page_size"],
        "total": result["total"], "total_pages": result["total_pages"],
    })


@router.get("/stages", response_model=ResponseModel, summary="商机阶段列表")
async def list_stages():
    """获取所有商机阶段"""
    return ResponseModel(data=[{"key": k, "label": v} for k, v in STAGES])


@router.get("/funnel", response_model=ResponseModel, summary="销售漏斗")
async def sales_funnel(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """销售漏斗数据"""
    funnel = []
    for stage_key, stage_label in STAGES:
        result = await db.execute(
            select(func.count(Opportunity.id), func.coalesce(func.sum(Opportunity.amount), 0))
            .where(Opportunity.stage == stage_key, Opportunity.is_deleted == False)
        )
        count, total = result.one()
        funnel.append({"stage": stage_label, "stage_key": stage_key, "count": count, "amount": float(total)})
    return ResponseModel(data=funnel)


@router.get("/{opp_id}", response_model=ResponseModel, summary="商机详情")
async def get_opportunity(opp_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    opp = await opp_crud.get_by_id(db, opp_id)
    if not opp: raise HTTPException(status_code=404, detail="商机不存在")
    return ResponseModel(data=OpportunityOut.model_validate(opp))


@router.post("", response_model=ResponseModel, summary="创建商机")
async def create_opportunity(data: OpportunityCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    opp = Opportunity(**data.model_dump())
    db.add(opp)
    await db.flush()
    await db.refresh(opp)
    return ResponseModel(data={"id": opp.id, "name": opp.name}, message="商机创建成功")


@router.put("/{opp_id}", response_model=ResponseModel, summary="更新商机")
async def update_opportunity(opp_id: int, data: OpportunityUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    opp = await opp_crud.get_by_id(db, opp_id)
    if not opp: raise HTTPException(status_code=404, detail="商机不存在")

    for k, v in data.model_dump(exclude_unset=True).items():
        if v is not None: setattr(opp, k, v)

    if data.stage in ("won", "lost") and not opp.closed_at:
        opp.closed_at = datetime.utcnow()

    await db.flush()
    await db.refresh(opp)
    return ResponseModel(data={"id": opp.id, "name": opp.name}, message="商机更新成功")
