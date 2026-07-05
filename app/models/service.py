"""
客户服务模块：工单、工单评论
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel, TimestampMixin


class Ticket(BaseModel, TimestampMixin):
    """客服工单"""
    __tablename__ = "crm_ticket"

    ticket_no: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="工单编号"
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="工单标题")
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("crm_customer.id"), nullable=True, index=True, comment="客户ID"
    )
    contact_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("crm_contact.id"), nullable=True, comment="联系人ID"
    )
    ticket_type: Mapped[str] = mapped_column(
        String(30), default="question", server_default="'question'",
        comment="类型: question/complaint/suggestion/repair/other"
    )
    priority: Mapped[str] = mapped_column(
        String(20), default="normal", server_default="'normal'",
        comment="优先级: low/normal/high/urgent"
    )
    status: Mapped[str] = mapped_column(
        String(30), default="open", server_default="'open'",
        comment="状态: open/processing/resolved/closed"
    )
    sla_deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="SLA 截止时间"
    )
    assigned_to: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sys_user.id"), nullable=True, index=True, comment="处理人ID"
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sys_user.id"), nullable=True, comment="创建人ID"
    )
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="工单描述")
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="解决方案")
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="关闭时间"
    )
    satisfaction_score: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="满意度评分 (1-5)"
    )
    attachments: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True, comment="附件 (JSON数组)"
    )

    # 关联
    comments: Mapped[List["TicketComment"]] = relationship(
        "TicketComment", back_populates="ticket", cascade="all, delete-orphan"
    )


class TicketComment(BaseModel):
    """工单评论/回复"""
    __tablename__ = "crm_ticket_comment"

    ticket_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("crm_ticket.id", ondelete="CASCADE"), nullable=False, index=True, comment="工单ID"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_user.id"), nullable=False, comment="评论人ID"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="评论内容")
    is_internal: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否内部备注 (客户不可见)"
    )

    # 关联
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="comments")
