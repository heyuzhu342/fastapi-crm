"""
线索管理接口
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, pagination_params
from app.models.user import User
from app.models.sales import Lead
from app.models.customer import Customer
from app.schemas.sales import LeadCreate, LeadUpdate, LeadOut
from app.schemas.common import ResponseModel, ResponseList
from app.services.base_crud import BaseCRUD

router = APIRouter(prefix="/leads", tags=["🎯 线索管理"])
lead_crud = BaseCRUD(Lead)


@router.get("", response_model=ResponseList[LeadOut], summary="线索列表")
async def list_leads(
    pagination: dict = Depends(pagination_params),
    status: str = None,
    source: str = None,
    owner_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """线索列表"""
    filters = {}
    if status: filters["status"] = status
    if source: filters["source"] = source
    if owner_id: filters["owner_id"] = owner_id

    result = await lead_crud.get_list(
        db, page=pagination["page"], page_size=pagination["page_size"],
        sort_by=pagination["sort_by"], order=pagination["order"],
        search=pagination["search"],
        search_fields=["name", "company_name", "contact_phone", "email"],
        filters=filters,
    )

    items = [LeadOut.model_validate(l) for l in result["items"]]
    return ResponseList(data=items, meta={
        "page": result["page"], "page_size": result["page_size"],
        "total": result["total"], "total_pages": result["total_pages"],
    })


@router.get("/{lead_id}", response_model=ResponseModel, summary="线索详情")
async def get_lead(lead_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    lead = await lead_crud.get_by_id(db, lead_id)
    if not lead: raise HTTPException(status_code=404, detail="线索不存在")
    return ResponseModel(data=LeadOut.model_validate(lead))


@router.post("", response_model=ResponseModel, summary="创建线索")
async def create_lead(data: LeadCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    lead = Lead(**data.model_dump())
    db.add(lead)
    await db.flush()
    await db.refresh(lead)
    return ResponseModel(data={"id": lead.id, "name": lead.name}, message="线索创建成功")


@router.put("/{lead_id}", response_model=ResponseModel, summary="更新线索")
async def update_lead(lead_id: int, data: LeadUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    lead = await lead_crud.get_by_id(db, lead_id)
    if not lead: raise HTTPException(status_code=404, detail="线索不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        if v is not None: setattr(lead, k, v)
    await db.flush()
    await db.refresh(lead)
    return ResponseModel(data={"id": lead.id, "name": lead.name}, message="线索更新成功")


@router.delete("/{lead_id}", response_model=ResponseModel, summary="删除线索")
async def delete_lead(lead_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ok = await lead_crud.soft_delete(db, lead_id)
    if not ok: raise HTTPException(status_code=404, detail="线索不存在")
    return ResponseModel(message="线索已删除")


@router.post("/{lead_id}/convert", response_model=ResponseModel, summary="线索转化为客户")
async def convert_lead(lead_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """将线索转化为正式客户"""
    lead = await lead_crud.get_by_id(db, lead_id)
    if not lead: raise HTTPException(status_code=404, detail="线索不存在")
    if lead.status == "converted":
        raise HTTPException(status_code=400, detail="该线索已转化")

    # 创建客户
    customer = Customer(
        name=lead.company_name or lead.name,
        source=lead.source,
        owner_id=lead.owner_id,
    )
    db.add(customer)
    await db.flush()

    # 更新线索状态
    lead.status = "converted"
    lead.converted_at = datetime.utcnow()
    lead.converted_customer_id = customer.id
    await db.flush()

    return ResponseModel(
        data={"customer_id": customer.id, "customer_name": customer.name},
        message="线索已成功转化为客户",
    )
