"""
销售模块模型：线索、商机、报价单、合同
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    Integer,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin


# ── 线索 ─────────────────────────────────────────
class Lead(BaseModel, SoftDeleteMixin):
    """销售线索"""
    __tablename__ = "crm_lead"

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="线索名称/联系人")
    company_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="公司名称")
    contact_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, comment="联系电话")
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="邮箱")
    source: Mapped[str] = mapped_column(
        String(50), default="website", server_default="'website'",
        comment="来源: website/referral/exhibition/cold_call/ad/social_media/other"
    )
    status: Mapped[str] = mapped_column(
        String(30), default="new", server_default="'new'",
        comment="状态: new/contacted/qualified/lost/converted"
    )
    qualification: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="意向描述"
    )
    owner_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sys_user.id"), nullable=True, index=True, comment="负责人ID"
    )
    campaign_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("crm_campaign.id"), nullable=True, comment="来源活动ID"
    )
    converted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="转化时间"
    )
    converted_customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("crm_customer.id"), nullable=True, comment="转化客户ID"
    )
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")


# ── 商机 ─────────────────────────────────────────
class Opportunity(BaseModel, SoftDeleteMixin):
    """销售商机"""
    __tablename__ = "crm_opportunity"

    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="商机名称")
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("crm_customer.id"), nullable=True, index=True, comment="客户ID"
    )
    contact_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("crm_contact.id"), nullable=True, comment="联系人ID"
    )
    amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True, comment="预计金额"
    )
    stage: Mapped[str] = mapped_column(
        String(50), default="initial_contact", server_default="'initial_contact'",
        comment="阶段: initial_contact/needs_analysis/quotation/negotiation/won/lost"
    )
    probability: Mapped[int] = mapped_column(
        Integer, default=10, server_default="10", comment="成交概率 (%): 10-100"
    )
    expected_close_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="预计成交日期"
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="实际成交/丢单日期"
    )
    lost_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="丢单原因")
    owner_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sys_user.id"), nullable=True, index=True, comment="负责人ID"
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="商机描述")
    competitors: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="竞争对手信息")


# ── 报价单 ───────────────────────────────────────
class Quotation(BaseModel, SoftDeleteMixin):
    """报价单"""
    __tablename__ = "crm_quotation"

    quotation_no: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="报价单号"
    )
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("crm_customer.id"), nullable=False, index=True, comment="客户ID"
    )
    opportunity_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("crm_opportunity.id"), nullable=True, comment="关联商机ID"
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=0, server_default="0", comment="报价总金额"
    )
    discount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True, comment="折扣 (%)"
    )
    final_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=0, server_default="0", comment="折后金额"
    )
    status: Mapped[str] = mapped_column(
        String(30), default="draft", server_default="'draft'",
        comment="状态: draft/sent/approved/rejected/expired"
    )
    valid_until: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="有效期至"
    )
    terms: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="条款说明")
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_user.id"), nullable=False, comment="创建人ID"
    )
    approved_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sys_user.id"), nullable=True, comment="审批人ID"
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="审批时间"
    )
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")

    # 关联
    items: Mapped[List["QuotationItem"]] = relationship(
        "QuotationItem", back_populates="quotation", cascade="all, delete-orphan"
    )


# ── 报价单明细 ───────────────────────────────────
class QuotationItem(BaseModel):
    """报价单项"""
    __tablename__ = "crm_quotation_item"

    quotation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("crm_quotation.id", ondelete="CASCADE"), nullable=False, index=True, comment="报价单ID"
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("crm_product.id"), nullable=True, comment="产品ID"
    )
    product_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="产品名称")
    specification: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="规格")
    quantity: Mapped[int] = mapped_column(Integer, default=1, server_default="1", comment="数量")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, comment="单价")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="小计")

    # 关联
    quotation: Mapped["Quotation"] = relationship("Quotation", back_populates="items")


# ── 合同 ─────────────────────────────────────────
class Contract(BaseModel, SoftDeleteMixin):
    """合同"""
    __tablename__ = "crm_contract"

    contract_no: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="合同编号"
    )
    opportunity_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("crm_opportunity.id"), nullable=True, comment="关联商机ID"
    )
    quotation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("crm_quotation.id"), nullable=True, comment="关联报价单ID"
    )
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("crm_customer.id"), nullable=False, index=True, comment="客户ID"
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="合同名称")
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, comment="合同金额")
    status: Mapped[str] = mapped_column(
        String(30), default="draft", server_default="'draft'",
        comment="状态: draft/pending_approval/active/completed/terminated/expired"
    )
    signed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="签署日期")
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="开始日期")
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="结束日期")
    file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="合同文件URL")
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_user.id"), nullable=False, comment="创建人ID"
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="合同描述")
