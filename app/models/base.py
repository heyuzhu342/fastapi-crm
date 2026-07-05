"""
ORM 基础模型
提供通用字段：id、时间戳、软删除
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Integer,
    Boolean,
    DateTime,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class TimestampMixin:
    """创建时间 + 更新时间自动管理"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class SoftDeleteMixin:
    """软删除"""
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否已删除"
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="删除时间"
    )


class BaseModel(Base, TimestampMixin):
    """
    通用基类
    - 使用 BIGINT 自增主键
    - 包含 created_at / updated_at
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="主键ID"
    )
