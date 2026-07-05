"""
产品管理接口：产品 CRUD、产品分类
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.api.deps import get_current_user, pagination_params
from app.models.user import User
from app.models.product import Product, ProductCategory
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductOut,
    ProductListOut,
    ProductCategoryCreate,
    ProductCategoryUpdate,
    ProductCategoryOut,
)
from app.schemas.common import ResponseModel, ResponseList
from app.services.base_crud import BaseCRUD

router = APIRouter(prefix="/products", tags=["📦 产品管理"])

product_crud = BaseCRUD(Product)
category_crud = BaseCRUD(ProductCategory)


# ── 产品分类 ─────────────────────────────────────

@router.get("/categories/tree", response_model=ResponseModel[list[ProductCategoryOut]], summary="分类树")
async def category_tree(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取产品分类树"""
    result = await db.execute(
        select(ProductCategory)
        .options(joinedload(ProductCategory.children))
        .where(ProductCategory.parent_id.is_(None))
        .order_by(ProductCategory.sort)
    )
    categories = result.unique().scalars().all()

    def build_tree(cats):
        data = []
        for c in cats:
            co = ProductCategoryOut.model_validate(c)
            co.children = build_tree(c.children) if c.children else []
            co.product_count = 0  # lazy load disabled for async
            data.append(co)
        return data

    return ResponseModel(data=build_tree(categories))


@router.post("/categories", response_model=ResponseModel, summary="创建分类")
async def create_category(
    data: ProductCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建产品分类"""
    cat = ProductCategory(**data.model_dump())
    db.add(cat)
    await db.flush()
    await db.refresh(cat)
    return ResponseModel(data=ProductCategoryOut.model_validate(cat), message="分类创建成功")


@router.put("/categories/{cat_id}", response_model=ResponseModel, summary="更新分类")
async def update_category(
    cat_id: int,
    data: ProductCategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新分类"""
    cat = await category_crud.get_by_id(db, cat_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        if v is not None:
            setattr(cat, k, v)
    await db.flush()
    await db.refresh(cat)
    return ResponseModel(data=ProductCategoryOut.model_validate(cat), message="分类更新成功")


@router.delete("/categories/{cat_id}", response_model=ResponseModel, summary="删除分类")
async def delete_category(
    cat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除分类（如有子分类或产品则拒绝）"""
    cat = await category_crud.get_by_id(db, cat_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    r = await db.execute(select(func.count(ProductCategory.id)).where(ProductCategory.parent_id == cat_id))
    if (r.scalar() or 0) > 0:
        raise HTTPException(status_code=400, detail="请先删除子分类")
    # Check if products exist via count query
    from sqlalchemy import select, func
    r = await db.execute(select(func.count(Product.id)).where(Product.category_id == cat_id, Product.is_deleted == False))
    if (r.scalar() or 0) > 0:
        raise HTTPException(status_code=400, detail="该分类下还有产品，无法删除")
    await db.delete(cat)
    await db.flush()
    return ResponseModel(message="分类已删除")


# ── 产品 CRUD ────────────────────────────────────

@router.get("", response_model=ResponseList[ProductListOut], summary="产品列表")
async def list_products(
    pagination: dict = Depends(pagination_params),
    category_id: int = None,
    is_active: bool = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """产品列表（支持搜索、分类筛选）"""
    filters = {}
    if category_id is not None:
        filters["category_id"] = category_id
    if is_active is not None:
        filters["is_active"] = is_active

    result = await product_crud.get_list(
        db,
        page=pagination["page"],
        page_size=pagination["page_size"],
        sort_by=pagination["sort_by"],
        order=pagination["order"],
        search=pagination["search"],
        search_fields=["name", "sku", "description"],
        filters=filters,
    )

    items = []
    for p in result["items"]:
        items.append(ProductListOut(
            id=p.id,
            name=p.name,
            sku=p.sku,
            price=p.price,
            stock=p.stock,
            unit=p.unit,
            is_active=p.is_active,
            category_name=None,  # avoid lazy load
            created_at=p.created_at,
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


@router.get("/{product_id}", response_model=ResponseModel, summary="产品详情")
async def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取产品详情"""
    result = await db.execute(
        select(Product)
        .options(joinedload(Product.category))
        .where(Product.id == product_id, Product.is_deleted == False)
    )
    p = result.unique().scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=404, detail="产品不存在")

    out = ProductOut.model_validate(p)
    out.category_name = p.category.name if p.category else None
    return ResponseModel(data=out)


@router.post("", response_model=ResponseModel, summary="创建产品")
async def create_product(
    data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建产品"""
    product = Product(**data.model_dump())
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return ResponseModel(data={"id": product.id, "name": product.name}, message="产品创建成功")


@router.put("/{product_id}", response_model=ResponseModel, summary="更新产品")
async def update_product(
    product_id: int,
    data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新产品"""
    p = await product_crud.get_by_id(db, product_id)
    if p is None:
        raise HTTPException(status_code=404, detail="产品不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        if v is not None:
            setattr(p, k, v)
    await db.flush()
    await db.refresh(p)
    return ResponseModel(data={"id": p.id, "name": p.name}, message="产品更新成功")


@router.delete("/{product_id}", response_model=ResponseModel, summary="删除产品")
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除产品（软删除）"""
    success = await product_crud.soft_delete(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="产品不存在")
    return ResponseModel(message="产品已删除")
