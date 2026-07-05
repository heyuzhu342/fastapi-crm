"""
报价单管理接口
"""
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.api.deps import get_current_user, pagination_params
from app.models.user import User
from app.models.sales import Quotation, QuotationItem
from app.schemas.sales import QuotationCreate, QuotationUpdate, QuotationOut
from app.schemas.common import ResponseModel, ResponseList
from app.services.base_crud import BaseCRUD

router = APIRouter(prefix="/quotations", tags=["📋 报价管理"])
q_crud = BaseCRUD(Quotation)


def generate_quotation_no() -> str:
    from datetime import datetime
    return f"QTN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


@router.get("", response_model=ResponseList[QuotationOut], summary="报价单列表")
async def list_quotations(
    pagination: dict = Depends(pagination_params),
    status: str = None, customer_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = {}
    if status: filters["status"] = status
    if customer_id: filters["customer_id"] = customer_id

    result = await q_crud.get_list(
        db, page=pagination["page"], page_size=pagination["page_size"],
        sort_by=pagination["sort_by"], order=pagination["order"],
        search=pagination["search"], search_fields=["quotation_no"],
        filters=filters,
    )
    items = [QuotationOut.model_validate(q) for q in result["items"]]
    return ResponseList(data=items, meta={
        "page": result["page"], "page_size": result["page_size"],
        "total": result["total"], "total_pages": result["total_pages"],
    })


@router.get("/{q_id}", response_model=ResponseModel, summary="报价单详情")
async def get_quotation(q_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Quotation).options(joinedload(Quotation.items))
        .where(Quotation.id == q_id, Quotation.is_deleted == False)
    )
    q = result.unique().scalar_one_or_none()
    if not q: raise HTTPException(status_code=404, detail="报价单不存在")
    return ResponseModel(data=QuotationOut.model_validate(q))


@router.post("", response_model=ResponseModel, summary="创建报价单")
async def create_quotation(data: QuotationCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # 计算总金额
    items_data = data.model_dump(exclude={"customer_id", "opportunity_id", "discount", "valid_until", "terms", "remark", "items"})
    total = Decimal("0")
    for item in data.items:
        subtotal = Decimal(str(item.quantity)) * item.unit_price
        total += subtotal

    final = total
    if data.discount:
        final = total * (Decimal("1") - data.discount / Decimal("100"))

    q = Quotation(
        quotation_no=generate_quotation_no(),
        customer_id=data.customer_id,
        opportunity_id=data.opportunity_id,
        total_amount=total,
        discount=data.discount,
        final_amount=final,
        valid_until=data.valid_until,
        terms=data.terms,
        remark=data.remark,
        created_by=current_user.id,
    )
    db.add(q)
    await db.flush()

    for item in data.items:
        qi = QuotationItem(
            quotation_id=q.id,
            product_id=item.product_id,
            product_name=item.product_name,
            specification=item.specification,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=Decimal(str(item.quantity)) * item.unit_price,
        )
        db.add(qi)

    await db.flush()
    await db.refresh(q)
    return ResponseModel(data={"id": q.id, "quotation_no": q.quotation_no, "final_amount": str(q.final_amount)}, message="报价单创建成功")


@router.put("/{q_id}", response_model=ResponseModel, summary="更新报价单")
async def update_quotation(q_id: int, data: QuotationUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = await q_crud.get_by_id(db, q_id)
    if not q: raise HTTPException(status_code=404, detail="报价单不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        if v is not None: setattr(q, k, v)
    await db.flush()
    await db.refresh(q)
    return ResponseModel(data={"id": q.id, "quotation_no": q.quotation_no}, message="报价单更新成功")


@router.delete("/{q_id}", response_model=ResponseModel, summary="删除报价单")
async def delete_quotation(q_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ok = await q_crud.soft_delete(db, q_id)
    if not ok: raise HTTPException(status_code=404, detail="报价单不存在")
    return ResponseModel(message="报价单已删除")
