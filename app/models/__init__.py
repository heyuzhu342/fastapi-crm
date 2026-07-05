"""
统一导出所有 ORM 模型
Alembic 需要从此处导入才能检测到所有表
"""
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin
from app.models.user import (
    User,
    Role,
    Permission,
    Department,
    AuditLog,
    user_role_table,
    role_permission_table,
)
from app.models.customer import Customer, Contact, CustomerTag, FollowUpRecord
from app.models.sales import Lead, Opportunity, Quotation, QuotationItem, Contract
from app.models.product import Product, ProductCategory
from app.models.marketing import Campaign
from app.models.service import Ticket, TicketComment
from app.models.notification import Notification
from app.models.system import DictType, DictData, SystemConfig

__all__ = [
    # Base
    "BaseModel",
    "TimestampMixin",
    "SoftDeleteMixin",
    # User & Auth
    "User",
    "Role",
    "Permission",
    "Department",
    "AuditLog",
    # Customer
    "Customer",
    "Contact",
    "CustomerTag",
    "FollowUpRecord",
    # Sales
    "Lead",
    "Opportunity",
    "Quotation",
    "QuotationItem",
    "Contract",
    # Product
    "Product",
    "ProductCategory",
    # Marketing
    "Campaign",
    # Service
    "Ticket",
    "TicketComment",
    # Notification
    "Notification",
    # System
    "DictType",
    "DictData",
    "SystemConfig",
]
