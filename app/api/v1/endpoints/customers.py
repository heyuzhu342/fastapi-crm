"""
客户管理接口：客户 CRUD、联系人、标签、跟进记录
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.api.deps import get_current_user, pagination_params
from app.models.user import User
from app.models.customer import Customer, Contact, CustomerTag, FollowUpRecord
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerOut,
    CustomerListOut,
    ContactCreate,
    ContactUpdate,
    ContactOut,
    CustomerTagCreate,
    CustomerTagOut,
    FollowUpCreate,
    FollowUpOut,
)
from app.schemas.common import ResponseModel, ResponseList
from app.services.base_crud import BaseCRUD

router = APIRouter(prefix="/customers", tags=["🏢 客户管理"])

customer_crud = BaseCRUD(Customer)
contact_crud = BaseCRUD(Contact)
tag_crud = BaseCRUD(CustomerTag)


# ── 客户 CRUD ────────────────────────────────────

@router.get("", response_model=ResponseList[CustomerListOut], summary="客户列表")
async def list_customers(
    pagination: dict = Depends(pagination_params),
    industry: str = None,
    status: str = None,
    owner_id: int = None,
    is_public_pool: bool = None,
    tag_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """客户列表（支持搜索、行业/状态/负责人筛选）"""
    filters = {}
    if industry:
        filters["industry"] = industry
    if status:
        filters["status"] = status
    if owner_id:
        filters["owner_id"] = owner_id
    if is_public_pool is not None:
        filters["is_public_pool"] = is_public_pool

    result = await customer_crud.get_list(
        db,
        page=pagination["page"],
        page_size=pagination["page_size"],
        sort_by=pagination["sort_by"],
        order=pagination["order"],
        search=pagination["search"],
        search_fields=["name", "address", "website"],
        filters=filters,
    )

    items = []
    for c in result["items"]:
        items.append(CustomerListOut(
            id=c.id,
            name=c.name,
            industry=c.industry,
            scale=c.scale,
            source=c.source,
            status=c.status,
            city=c.city,
            owner_id=c.owner_id,
            owner_name=None,  # TODO: join owner
            is_public_pool=c.is_public_pool,
            contact_count=0,  # lazy load disabled for async
            last_follow_up=None,
            created_at=c.created_at,
        ))

    return ResponseList(
        data=items,
        meta={
            "page": result["page"],
            "page_size": result["page_size"],
            "total": result["total"],
            "total_pages": result["total_pages"],
        },
    )


@router.get("/{customer_id}", response_model=ResponseModel, summary="客户详情")
async def get_customer(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取客户详细信息（含联系人和标签）"""
    result = await db.execute(
        select(Customer)
        .options(
            joinedload(Customer.contacts),
            joinedload(Customer.tags),
        )
        .where(Customer.id == customer_id, Customer.is_deleted == False)
    )
    customer = result.unique().scalar_one_or_none()
    if customer is None:
        raise HTTPException(status_code=404, detail="客户不存在")

    return ResponseModel(data=CustomerOut.model_validate(customer))


@router.post("", response_model=ResponseModel, summary="创建客户")
async def create_customer(
    data: CustomerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新客户"""
    customer_data = data.model_dump(exclude={"tag_ids"})
    customer = Customer(**customer_data)

    if data.tag_ids:
        result = await db.execute(
            select(CustomerTag).where(CustomerTag.id.in_(data.tag_ids))
        )
        customer.tags = result.unique().scalars().all()

    db.add(customer)
    await db.flush()
    await db.refresh(customer)
    return ResponseModel(data={"id": customer.id, "name": customer.name}, message="客户创建成功")


@router.put("/{customer_id}", response_model=ResponseModel, summary="更新客户")
async def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新客户信息"""
    result = await db.execute(
        select(Customer).options(joinedload(Customer.tags)).where(
            Customer.id == customer_id, Customer.is_deleted == False
        )
    )
    customer = result.unique().scalar_one_or_none()
    if customer is None:
        raise HTTPException(status_code=404, detail="客户不存在")

    update_data = data.model_dump(exclude_unset=True, exclude={"tag_ids"})

    if data.tag_ids is not None:
        tags_result = await db.execute(
            select(CustomerTag).where(CustomerTag.id.in_(data.tag_ids))
        )
        customer.tags = tags_result.unique().scalars().all()

    for key, value in update_data.items():
        if value is not None:
            setattr(customer, key, value)

    await db.flush()
    await db.refresh(customer)
    return ResponseModel(data={"id": customer.id, "name": customer.name}, message="客户更新成功")


@router.delete("/{customer_id}", response_model=ResponseModel, summary="删除客户")
async def delete_customer(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除客户（软删除）"""
    success = await customer_crud.soft_delete(db, customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="客户不存在")
    return ResponseModel(message="客户已删除")


# ── 联系人 ───────────────────────────────────────

@router.get("/{customer_id}/contacts", response_model=ResponseModel[list[ContactOut]], summary="联系人列表")
async def list_contacts(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取某客户的所有联系人"""
    result = await db.execute(
        select(Contact).where(
            Contact.customer_id == customer_id,
            Contact.is_deleted == False,
        ).order_by(Contact.is_primary.desc(), Contact.created_at.desc())
    )
    contacts = result.unique().scalars().all()
    return ResponseModel(data=[ContactOut.model_validate(c) for c in contacts])


@router.post("/{customer_id}/contacts", response_model=ResponseModel, summary="添加联系人")
async def create_contact(
    customer_id: int,
    data: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """为客户添加联系人"""
    contact = Contact(**data.model_dump())
    db.add(contact)
    await db.flush()
    await db.refresh(contact)
    return ResponseModel(data={"id": contact.id, "name": contact.name}, message="联系人添加成功")


@router.put("/contacts/{contact_id}", response_model=ResponseModel, summary="更新联系人")
async def update_contact(
    contact_id: int,
    data: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新联系人信息"""
    contact = await contact_crud.get_by_id(db, contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="联系人不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(contact, key, value)

    await db.flush()
    await db.refresh(contact)
    return ResponseModel(data={"id": contact.id, "name": contact.name}, message="联系人更新成功")


@router.delete("/contacts/{contact_id}", response_model=ResponseModel, summary="删除联系人")
async def delete_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除联系人"""
    success = await contact_crud.soft_delete(db, contact_id)
    if not success:
        raise HTTPException(status_code=404, detail="联系人不存在")
    return ResponseModel(message="联系人已删除")


# ── 标签 ─────────────────────────────────────────

@router.get("/tags/all", response_model=ResponseModel[list[CustomerTagOut]], summary="标签列表")
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有客户标签"""
    result = await db.execute(select(CustomerTag).order_by(CustomerTag.created_at.desc()))
    tags = result.unique().scalars().all()
    return ResponseModel(data=[CustomerTagOut.model_validate(t) for t in tags])


@router.post("/tags", response_model=ResponseModel, summary="创建标签")
async def create_tag(
    data: CustomerTagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建客户标签"""
    tag = CustomerTag(**data.model_dump())
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return ResponseModel(data={"id": tag.id, "name": tag.name}, message="标签创建成功")


# ── 跟进记录 ─────────────────────────────────────

@router.get("/{customer_id}/follow-ups", response_model=ResponseModel[list[FollowUpOut]], summary="跟进记录")
async def list_follow_ups(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取某客户的跟进记录"""
    result = await db.execute(
        select(FollowUpRecord)
        .where(FollowUpRecord.customer_id == customer_id)
        .order_by(FollowUpRecord.created_at.desc())
    )
    records = result.unique().scalars().all()
    return ResponseModel(data=[FollowUpOut.model_validate(r) for r in records])


@router.post("/{customer_id}/follow-ups", response_model=ResponseModel, summary="添加跟进记录")
async def create_follow_up(
    customer_id: int,
    data: FollowUpCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """添加客户跟进记录"""
    record = FollowUpRecord(
        customer_id=customer_id,
        user_id=current_user.id,
        **data.model_dump(exclude={"customer_id"}),
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return ResponseModel(data=FollowUpOut.model_validate(record), message="跟进记录添加成功")
