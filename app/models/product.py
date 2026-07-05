"""
产品管理模型
"""
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    Integer,
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin


# ── 产品分类 ─────────────────────────────────────
class ProductCategory(BaseModel):
    """产品分类"""
    __tablename__ = "crm_product_category"

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="分类名称")
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("crm_product_category.id"), nullable=True, comment="上级分类ID"
    )
    sort: Mapped[int] = mapped_column(Integer, default=0, server_default="0", comment="排序")
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="描述")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", comment="是否启用")

    # 自引用
    children: Mapped[List["ProductCategory"]] = relationship(
        "ProductCategory", remote_side="ProductCategory.id", backref="parent"
    )
    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")


# ── 产品 ─────────────────────────────────────────
class Product(BaseModel, SoftDeleteMixin):
    """产品"""
    __tablename__ = "crm_product"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True, comment="产品名称")
    sku: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, comment="SKU编码")
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("crm_product_category.id"), nullable=True, index=True, comment="分类ID"
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, server_default="0", comment="标准售价"
    )
    cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True, comment="成本价"
    )
    stock: Mapped[int] = mapped_column(Integer, default=0, server_default="0", comment="库存数量")
    unit: Mapped[str] = mapped_column(
        String(20), default="pcs", server_default="'pcs'", comment="单位: pcs/kg/set/etc"
    )
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="产品图片URL")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="产品描述")
    specification: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="规格参数")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", comment="是否上架")

    # 关联
    category: Mapped[Optional["ProductCategory"]] = relationship(
        "ProductCategory", back_populates="products"
    )
