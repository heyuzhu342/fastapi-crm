"""
合同管理接口
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, pagination_params
from app.models.user import User
from app.models.sales import Contract
from app.schemas.sales import ContractCreate, ContractUpdate, ContractOut
from app.schemas.common import ResponseModel, ResponseList
from app.services.base_crud import BaseCRUD

router = APIRouter(prefix="/contracts", tags=["📝 合同管理"])
contract_crud = BaseCRUD(Contract)


def generate_contract_no() -> str:
    return f"CTR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


@router.get("", response_model=ResponseList[ContractOut], summary="合同列表")
async def list_contracts(
    pagination: dict = Depends(pagination_params),
    status: str = None, customer_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = {}
    if status: filters["status"] = status
    if customer_id: filters["customer_id"] = customer_id

    result = await contract_crud.get_list(
        db, page=pagination["page"], page_size=pagination["page_size"],
        sort_by=pagination["sort_by"], order=pagination["order"],
        search=pagination["search"], search_fields=["contract_no", "name"],
        filters=filters,
    )
    items = [ContractOut.model_validate(c) for c in result["items"]]
    return ResponseList(data=items, meta={
        "page": result["page"], "page_size": result["page_size"],
        "total": result["total"], "total_pages": result["total_pages"],
    })


@router.get("/{c_id}", response_model=ResponseModel, summary="合同详情")
async def get_contract(c_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    c = await contract_crud.get_by_id(db, c_id)
    if not c: raise HTTPException(status_code=404, detail="合同不存在")
    return ResponseModel(data=ContractOut.model_validate(c))


@router.post("", response_model=ResponseModel, summary="创建合同")
async def create_contract(data: ContractCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    c = Contract(
        contract_no=generate_contract_no(),
        created_by=current_user.id,
        **data.model_dump(),
    )
    db.add(c)
    await db.flush()
    await db.refresh(c)
    return ResponseModel(data={"id": c.id, "contract_no": c.contract_no}, message="合同创建成功")


@router.put("/{c_id}", response_model=ResponseModel, summary="更新合同")
async def update_contract(c_id: int, data: ContractUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    c = await contract_crud.get_by_id(db, c_id)
    if not c: raise HTTPException(status_code=404, detail="合同不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        if v is not None: setattr(c, k, v)
    await db.flush()
    await db.refresh(c)
    return ResponseModel(data={"id": c.id, "contract_no": c.contract_no}, message="合同更新成功")


@router.delete("/{c_id}", response_model=ResponseModel, summary="删除合同")
async def delete_contract(c_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ok = await contract_crud.soft_delete(db, c_id)
    if not ok: raise HTTPException(status_code=404, detail="合同不存在")
    return ResponseModel(message="合同已删除")
