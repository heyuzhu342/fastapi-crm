"""
营销活动模型
"""
from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Integer,
    Date,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin


class Campaign(BaseModel, SoftDeleteMixin):
    """营销活动"""
    __tablename__ = "crm_campaign"

    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="活动名称")
    campaign_type: Mapped[str] = mapped_column(
        String(50), default="offline", server_default="'offline'",
        comment="类型: offline/online/email/social/other"
    )
    budget: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True, comment="预算金额"
    )
    actual_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True, comment="实际花费"
    )
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="开始日期")
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="结束日期")
    status: Mapped[str] = mapped_column(
        String(30), default="planning", server_default="'planning'",
        comment="状态: planning/active/completed/cancelled"
    )
    owner_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sys_user.id"), nullable=True, comment="负责人ID"
    )
    target_audience: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="目标受众描述"
    )
    expected_revenue: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True, comment="预期收入"
    )
    actual_revenue: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True, comment="实际收入"
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="活动描述")
