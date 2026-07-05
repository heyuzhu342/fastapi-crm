"""
客户、联系人、标签、跟进记录 Schema
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ── 客户标签 ─────────────────────────────────────
class CustomerTagBase(BaseModel):
    name: str = Field(..., max_length=50, description="标签名称")
    color: str = Field(default="#1890ff", max_length=20, description="标签颜色")


class CustomerTagCreate(CustomerTagBase):
    pass


class CustomerTagOut(CustomerTagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── 联系人 ───────────────────────────────────────
class ContactBase(BaseModel):
    name: str = Field(..., max_length=100, description="姓名")
    title: Optional[str] = Field(default=None, max_length=100, description="职位")
    gender: Optional[str] = Field(default=None, description="性别")
    phone: Optional[str] = Field(default=None, max_length=30, description="电话")
    email: Optional[str] = Field(default=None, max_length=100, description="邮箱")
    wechat: Optional[str] = Field(default=None, max_length=50, description="微信")
    qq: Optional[str] = Field(default=None, max_length=20, description="QQ")
    is_primary: bool = Field(default=False, description="是否首要联系人")
    remark: Optional[str] = Field(default=None, max_length=500)


class ContactCreate(ContactBase):
    customer_id: int = Field(..., description="客户ID")


class ContactUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    title: Optional[str] = Field(default=None, max_length=100)
    gender: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=100)
    wechat: Optional[str] = Field(default=None, max_length=50)
    qq: Optional[str] = Field(default=None, max_length=20)
    is_primary: Optional[bool] = Field(default=None)
    remark: Optional[str] = Field(default=None, max_length=500)


class ContactOut(ContactBase):
    id: int
    customer_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── 跟进记录 ─────────────────────────────────────
class FollowUpCreate(BaseModel):
    customer_id: int = Field(..., description="客户ID")
    follow_type: str = Field(default="phone", description="跟进方式")
    content: str = Field(..., description="跟进内容")
    result: Optional[str] = Field(default=None, description="跟进结果")
    next_follow_up: Optional[datetime] = Field(default=None, description="下次跟进时间")


class FollowUpOut(BaseModel):
    id: int
    customer_id: int
    user_id: int
    follow_type: str
    content: str
    result: Optional[str]
    next_follow_up: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ── 客户 ─────────────────────────────────────────
class CustomerBase(BaseModel):
    name: str = Field(..., max_length=200, description="公司名称")
    industry: Optional[str] = Field(default=None, max_length=100, description="行业")
    scale: Optional[str] = Field(default=None, description="规模")
    source: Optional[str] = Field(default=None, description="来源")
    status: str = Field(default="active", description="状态")
    country: Optional[str] = Field(default=None, max_length=100, description="国家")
    province: Optional[str] = Field(default=None, max_length=100, description="省份")
    city: Optional[str] = Field(default=None, max_length=100, description="城市")
    address: Optional[str] = Field(default=None, max_length=500, description="详细地址")
    website: Optional[str] = Field(default=None, max_length=200, description="网址")
    description: Optional[str] = Field(default=None, description="公司描述")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")


class CustomerCreate(CustomerBase):
    tag_ids: List[int] = Field(default_factory=list, description="标签ID列表")


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    industry: Optional[str] = Field(default=None, max_length=100)
    scale: Optional[str] = Field(default=None)
    source: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    country: Optional[str] = Field(default=None, max_length=100)
    province: Optional[str] = Field(default=None, max_length=100)
    city: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=500)
    website: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None)
    owner_id: Optional[int] = Field(default=None)
    is_public_pool: Optional[bool] = Field(default=None)
    tag_ids: Optional[List[int]] = Field(default=None, description="标签ID列表")


class CustomerOut(CustomerBase):
    id: int
    logo: Optional[str]
    is_public_pool: bool
    created_at: datetime
    updated_at: datetime
    contacts: List[ContactOut] = Field(default_factory=list)
    tags: List[CustomerTagOut] = Field(default_factory=list)
    owner_name: Optional[str] = None
    contact_count: int = Field(default=0)
    last_follow_up: Optional[datetime] = None

    class Config:
        from_attributes = True


class CustomerListOut(BaseModel):
    """客户列表（简化版）"""
    id: int
    name: str
    industry: Optional[str]
    scale: Optional[str]
    source: Optional[str]
    status: str
    city: Optional[str]
    owner_id: Optional[int]
    owner_name: Optional[str]
    is_public_pool: bool
    contact_count: int
    last_follow_up: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
