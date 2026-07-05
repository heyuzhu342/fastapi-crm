"""
产品管理 Schema
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


# ── 产品分类 ─────────────────────────────────────
class ProductCategoryBase(BaseModel):
    name: str = Field(..., max_length=100, description="分类名称")
    parent_id: Optional[int] = Field(default=None, description="上级分类ID")
    sort: int = Field(default=0, description="排序")
    description: Optional[str] = Field(default=None, max_length=500)


class ProductCategoryCreate(ProductCategoryBase):
    pass


class ProductCategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    parent_id: Optional[int] = Field(default=None)
    sort: Optional[int] = Field(default=None)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = Field(default=None)


class ProductCategoryOut(ProductCategoryBase):
    id: int
    is_active: bool
    created_at: datetime
    children: Optional[List["ProductCategoryOut"]] = None
    product_count: int = Field(default=0)

    class Config:
        from_attributes = True


# ── 产品 ─────────────────────────────────────────
class ProductBase(BaseModel):
    name: str = Field(..., max_length=200, description="产品名称")
    sku: Optional[str] = Field(default=None, max_length=50, description="SKU编码")
    category_id: Optional[int] = Field(default=None, description="分类ID")
    price: Decimal = Field(default=0, max_digits=10, decimal_places=2, description="标准售价")
    cost: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2, description="成本价")
    stock: int = Field(default=0, description="库存数量")
    unit: str = Field(default="pcs", description="单位")
    description: Optional[str] = Field(default=None, description="产品描述")
    specification: Optional[str] = Field(default=None, description="规格参数")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    sku: Optional[str] = Field(default=None, max_length=50)
    category_id: Optional[int] = Field(default=None)
    price: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    cost: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    stock: Optional[int] = Field(default=None)
    unit: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    specification: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class ProductOut(ProductBase):
    id: int
    image: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category_name: Optional[str] = None

    class Config:
        from_attributes = True


class ProductListOut(BaseModel):
    id: int
    name: str
    sku: Optional[str]
    price: Decimal
    stock: int
    unit: str
    is_active: bool
    category_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
