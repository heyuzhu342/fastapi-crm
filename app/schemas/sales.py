"""
销售模块 Schema：线索、商机、报价、合同
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


# ── 线索 ─────────────────────────────────────────
class LeadBase(BaseModel):
    name: str = Field(..., max_length=100, description="线索名称")
    company_name: Optional[str] = Field(default=None, max_length=200)
    contact_phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=100)
    source: str = Field(default="website", description="来源")
    qualification: Optional[str] = Field(default=None, max_length=200)
    campaign_id: Optional[int] = Field(default=None)
    remark: Optional[str] = Field(default=None)


class LeadCreate(LeadBase):
    owner_id: Optional[int] = Field(default=None, description="负责人ID")


class LeadUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    company_name: Optional[str] = Field(default=None, max_length=200)
    contact_phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=100)
    source: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    qualification: Optional[str] = Field(default=None, max_length=200)
    owner_id: Optional[int] = Field(default=None)
    remark: Optional[str] = Field(default=None)


class LeadOut(LeadBase):
    id: int
    status: str
    owner_id: Optional[int]
    owner_name: Optional[str] = None
    converted_at: Optional[datetime]
    converted_customer_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── 商机 ─────────────────────────────────────────
class OpportunityBase(BaseModel):
    name: str = Field(..., max_length=200, description="商机名称")
    customer_id: Optional[int] = Field(default=None, description="客户ID")
    contact_id: Optional[int] = Field(default=None, description="联系人ID")
    amount: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    stage: str = Field(default="initial_contact", description="阶段")
    probability: int = Field(default=10, ge=0, le=100, description="成交概率")
    expected_close_date: Optional[date] = Field(default=None, description="预计成交日期")
    description: Optional[str] = Field(default=None)
    competitors: Optional[str] = Field(default=None)


class OpportunityCreate(OpportunityBase):
    owner_id: Optional[int] = Field(default=None)


class OpportunityUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    customer_id: Optional[int] = Field(default=None)
    contact_id: Optional[int] = Field(default=None)
    amount: Optional[Decimal] = Field(default=None)
    stage: Optional[str] = Field(default=None)
    probability: Optional[int] = Field(default=None)
    expected_close_date: Optional[date] = Field(default=None)
    lost_reason: Optional[str] = Field(default=None)
    owner_id: Optional[int] = Field(default=None)
    description: Optional[str] = Field(default=None)


class OpportunityOut(OpportunityBase):
    id: int
    owner_id: Optional[int]
    owner_name: Optional[str] = None
    customer_name: Optional[str] = None
    closed_at: Optional[datetime]
    lost_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── 报价单明细 ───────────────────────────────────
class QuotationItemCreate(BaseModel):
    product_id: Optional[int] = Field(default=None)
    product_name: str = Field(..., max_length=200)
    specification: Optional[str] = Field(default=None, max_length=200)
    quantity: int = Field(default=1, ge=1)
    unit_price: Decimal = Field(default=0, max_digits=10, decimal_places=2)


class QuotationItemOut(QuotationItemCreate):
    id: int
    subtotal: Decimal

    class Config:
        from_attributes = True


# ── 报价单 ───────────────────────────────────────
class QuotationBase(BaseModel):
    customer_id: int = Field(..., description="客户ID")
    opportunity_id: Optional[int] = Field(default=None)
    discount: Optional[Decimal] = Field(default=None, max_digits=5, decimal_places=2)
    valid_until: Optional[date] = Field(default=None)
    terms: Optional[str] = Field(default=None)
    remark: Optional[str] = Field(default=None)


class QuotationCreate(QuotationBase):
    items: List[QuotationItemCreate] = Field(..., min_length=1, description="报价明细")


class QuotationUpdate(BaseModel):
    customer_id: Optional[int] = Field(default=None)
    discount: Optional[Decimal] = Field(default=None)
    valid_until: Optional[date] = Field(default=None)
    terms: Optional[str] = Field(default=None)
    remark: Optional[str] = Field(default=None)


class QuotationOut(QuotationBase):
    id: int
    quotation_no: str
    total_amount: Decimal
    final_amount: Decimal
    status: str
    created_by: int
    created_by_name: Optional[str] = None
    customer_name: Optional[str] = None
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    items: List[QuotationItemOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── 合同 ─────────────────────────────────────────
class ContractBase(BaseModel):
    opportunity_id: Optional[int] = Field(default=None)
    quotation_id: Optional[int] = Field(default=None)
    customer_id: int = Field(..., description="客户ID")
    name: str = Field(..., max_length=200, description="合同名称")
    amount: Decimal = Field(..., max_digits=12, decimal_places=2, description="合同金额")
    signed_date: Optional[date] = Field(default=None)
    start_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)
    description: Optional[str] = Field(default=None)


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    amount: Optional[Decimal] = Field(default=None)
    status: Optional[str] = Field(default=None)
    signed_date: Optional[date] = Field(default=None)
    start_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)
    file_url: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None)


class ContractOut(ContractBase):
    id: int
    contract_no: str
    status: str
    file_url: Optional[str]
    created_by: int
    created_by_name: Optional[str] = None
    customer_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
