"""
通知消息模型
"""
from typing import Optional
from sqlalchemy import (
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel, TimestampMixin


class Notification(BaseModel):
    """站内通知"""
    __tablename__ = "sys_notification"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, index=True, comment="接收人ID"
    )
    notify_type: Mapped[str] = mapped_column(
        String(30), default="system", server_default="'system'",
        comment="类型: system/reminder/approval/alert"
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="通知标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="通知内容")
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否已读"
    )
    read_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime, nullable=True, comment="阅读时间"
    )
    related_resource: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="关联资源类型 (如 crm_ticket)"
    )
    related_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="关联资源ID"
    )
    link: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="跳转链接"
    )
