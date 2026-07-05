"""
系统设置模型：数据字典、系统配置
"""
from typing import List, Optional
from sqlalchemy import (
    Integer,
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel, TimestampMixin


# ── 数据字典类型 ─────────────────────────────────
class DictType(BaseModel):
    """字典类型"""
    __tablename__ = "sys_dict_type"

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="字典名称")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="字典编码")
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="描述")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", comment="是否启用")

    # 关联
    items: Mapped[List["DictData"]] = relationship(
        "DictData", back_populates="dict_type", cascade="all, delete-orphan"
    )


# ── 数据字典项 ───────────────────────────────────
class DictData(BaseModel):
    """字典数据项"""
    __tablename__ = "sys_dict_data"

    dict_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_dict_type.id", ondelete="CASCADE"), nullable=False, index=True, comment="字典类型ID"
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False, comment="标签")
    value: Mapped[str] = mapped_column(String(100), nullable=False, comment="值")
    sort: Mapped[int] = mapped_column(Integer, default=0, server_default="0", comment="排序")
    css_class: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="CSS样式")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", comment="是否启用")
    remark: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="备注")

    # 关联
    dict_type: Mapped["DictType"] = relationship("DictType", back_populates="items")


# ── 系统配置 ─────────────────────────────────────
class SystemConfig(BaseModel):
    """系统参数配置"""
    __tablename__ = "sys_config"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True, comment="配置键")
    value: Mapped[str] = mapped_column(Text, nullable=False, comment="配置值")
    value_type: Mapped[str] = mapped_column(
        String(20), default="string", server_default="'string'", comment="值类型: string/int/float/bool/json"
    )
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="配置说明")
    is_system: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否系统内置 (不可删除)"
    )
