"""
客户、联系人、标签、跟进记录 模型
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Integer,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin


# ── 多对多关联表 ──────────────────────────────────
customer_tag_table = Table(
    "crm_customer_tag_rel",
    BaseModel.metadata,
    Column("customer_id", Integer, ForeignKey("crm_customer.id", ondelete="CASCADE"), primary_key=True, comment="客户ID"),
    Column("tag_id", Integer, ForeignKey("crm_customer_tag.id", ondelete="CASCADE"), primary_key=True, comment="标签ID"),
)


# ── 客户标签 ─────────────────────────────────────
class CustomerTag(BaseModel):
    """客户标签"""
    __tablename__ = "crm_customer_tag"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="标签名称")
    color: Mapped[str] = mapped_column(
        String(20), default="#1890ff", server_default="'#1890ff'", comment="标签颜色"
    )

    customers: Mapped[List["Customer"]] = relationship(
        "Customer", secondary=customer_tag_table, back_populates="tags"
    )


# ── 客户 ─────────────────────────────────────────
class Customer(BaseModel, SoftDeleteMixin):
    """客户公司"""
    __tablename__ = "crm_customer"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True, comment="公司名称")
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="行业")
    scale: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="规模: micro/small/medium/large/enterprise"
    )
    source: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="来源: website/referral/exhibition/cold_call/ad/other"
    )
    status: Mapped[str] = mapped_column(
        String(50), default="active", server_default="'active'",
        comment="状态: active/inactive/blacklist"
    )
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="国家")
    province: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="省份")
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="城市")
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="详细地址")
    website: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="网址")
    logo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="Logo URL")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="公司描述")
    owner_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sys_user.id"), nullable=True, index=True, comment="负责人ID"
    )
    is_public_pool: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否在公海池"
    )

    # 关联
    contacts: Mapped[List["Contact"]] = relationship(
        "Contact", back_populates="customer", cascade="all, delete-orphan"
    )
    tags: Mapped[List["CustomerTag"]] = relationship(
        "CustomerTag", secondary=customer_tag_table, back_populates="customers"
    )
    follow_ups: Mapped[List["FollowUpRecord"]] = relationship(
        "FollowUpRecord", back_populates="customer", cascade="all, delete-orphan"
    )


# ── 联系人 ───────────────────────────────────────
class Contact(BaseModel, SoftDeleteMixin):
    """联系人"""
    __tablename__ = "crm_contact"

    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("crm_customer.id", ondelete="CASCADE"), nullable=False, index=True, comment="客户ID"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="姓名")
    title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="职位")
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, comment="性别: male/female")
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, comment="电话")
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="邮箱")
    wechat: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="微信号")
    qq: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="QQ号")
    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否首要联系人"
    )
    remark: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="备注")

    # 关联
    customer: Mapped["Customer"] = relationship("Customer", back_populates="contacts")


# ── 跟进记录 ─────────────────────────────────────
class FollowUpRecord(BaseModel):
    """客户跟进记录"""
    __tablename__ = "crm_follow_up"

    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("crm_customer.id", ondelete="CASCADE"), nullable=False, index=True, comment="客户ID"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_user.id"), nullable=False, comment="跟进人ID"
    )
    follow_type: Mapped[str] = mapped_column(
        String(30), default="phone", server_default="'phone'",
        comment="跟进方式: phone/email/visit/meeting/wechat/other"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="跟进内容")
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="跟进结果")
    next_follow_up: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="下次跟进时间"
    )
    attachments: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True, comment="附件 (JSON数组URL)"
    )

    # 关联
    customer: Mapped["Customer"] = relationship("Customer", back_populates="follow_ups")
