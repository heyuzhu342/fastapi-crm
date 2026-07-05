"""
用户、角色、权限、部门、操作日志 模型
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
user_role_table = Table(
    "sys_user_role",
    BaseModel.metadata,
    Column("user_id", Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), primary_key=True, comment="用户ID"),
    Column("role_id", Integer, ForeignKey("sys_role.id", ondelete="CASCADE"), primary_key=True, comment="角色ID"),
)

role_permission_table = Table(
    "sys_role_permission",
    BaseModel.metadata,
    Column("role_id", Integer, ForeignKey("sys_role.id", ondelete="CASCADE"), primary_key=True, comment="角色ID"),
    Column("permission_id", Integer, ForeignKey("sys_permission.id", ondelete="CASCADE"), primary_key=True, comment="权限ID"),
)


# ── 部门 ─────────────────────────────────────────
class Department(BaseModel):
    """部门/团队"""
    __tablename__ = "sys_department"

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="部门名称")
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sys_department.id"), nullable=True, comment="上级部门ID"
    )
    manager_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sys_user.id"), nullable=True, comment="部门负责人ID"
    )
    sort: Mapped[int] = mapped_column(Integer, default=0, server_default="0", comment="排序")
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="描述")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", comment="是否启用")

    # 自引用
    parent: Mapped[Optional["Department"]] = relationship(
        "Department", remote_side="Department.id", backref="children"
    )
    users: Mapped[List["User"]] = relationship("User", back_populates="department", foreign_keys="User.department_id")


# ── 用户 ─────────────────────────────────────────
class User(BaseModel):
    """系统用户"""
    __tablename__ = "sys_user"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="用户名"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True, comment="邮箱"
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="姓名")
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="手机号")
    avatar: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="头像URL")
    department_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sys_department.id"), nullable=True, comment="部门ID"
    )
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="职位")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", comment="是否启用")
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", comment="是否超级管理员")
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="最后登录时间")
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="最后登录IP")

    # 关联
    department: Mapped[Optional["Department"]] = relationship(
        "Department", back_populates="users", foreign_keys=[department_id]
    )
    roles: Mapped[List["Role"]] = relationship(
        "Role", secondary=user_role_table, back_populates="users"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


# ── 角色 ─────────────────────────────────────────
class Role(BaseModel):
    """角色"""
    __tablename__ = "sys_role"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="角色名称")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="角色编码")
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="描述")
    sort: Mapped[int] = mapped_column(Integer, default=0, server_default="0", comment="排序")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", comment="是否启用")

    # 关联
    users: Mapped[List["User"]] = relationship(
        "User", secondary=user_role_table, back_populates="roles"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission", secondary=role_permission_table, back_populates="roles"
    )


# ── 权限 ─────────────────────────────────────────
class Permission(BaseModel):
    """权限/菜单"""
    __tablename__ = "sys_permission"

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="权限名称")
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="权限编码")
    resource: Mapped[str] = mapped_column(String(200), nullable=False, comment="资源标识 (module:action)")
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sys_permission.id"), nullable=True, comment="上级权限ID"
    )
    menu_type: Mapped[str] = mapped_column(
        String(20), default="button", server_default="'button'", comment="类型: menu/button/api"
    )
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="图标")
    path: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="路由路径")
    sort: Mapped[int] = mapped_column(Integer, default=0, server_default="0", comment="排序")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", comment="是否启用")

    # 自引用
    children: Mapped[List["Permission"]] = relationship(
        "Permission", remote_side="Permission.id", backref="parent"
    )
    # 角色关联
    roles: Mapped[List["Role"]] = relationship(
        "Role", secondary=role_permission_table, back_populates="permissions"
    )


# ── 操作日志 ─────────────────────────────────────
class AuditLog(BaseModel):
    """操作审计日志"""
    __tablename__ = "sys_audit_log"

    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True, comment="操作用户ID"
    )
    username: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="操作用户名")
    action: Mapped[str] = mapped_column(String(50), nullable=False, comment="操作类型: create/update/delete/login/logout")
    resource: Mapped[str] = mapped_column(String(100), nullable=False, comment="操作资源")
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="资源ID")
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="操作详情 (JSON)")
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="IP地址")
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="User-Agent")
    status: Mapped[str] = mapped_column(
        String(20), default="success", server_default="'success'", comment="操作结果: success/failure"
    )
