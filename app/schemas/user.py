"""
用户、角色、权限 Schema
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


# ── 权限 ─────────────────────────────────────────
class PermissionBase(BaseModel):
    name: str = Field(..., max_length=100, description="权限名称")
    code: str = Field(..., max_length=100, description="权限编码")
    resource: str = Field(..., max_length=200, description="资源标识")
    parent_id: Optional[int] = Field(default=None, description="上级权限ID")
    menu_type: str = Field(default="button", description="类型")
    icon: Optional[str] = Field(default=None, max_length=50, description="图标")
    path: Optional[str] = Field(default=None, max_length=200, description="路由路径")
    sort: int = Field(default=0, description="排序")


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    resource: Optional[str] = Field(default=None, max_length=200)
    icon: Optional[str] = Field(default=None, max_length=50)
    path: Optional[str] = Field(default=None, max_length=200)
    sort: Optional[int] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class PermissionOut(PermissionBase):
    id: int
    is_active: bool
    created_at: datetime
    children: Optional[List["PermissionOut"]] = None

    class Config:
        from_attributes = True


# ── 角色 ─────────────────────────────────────────
class RoleBase(BaseModel):
    name: str = Field(..., max_length=100, description="角色名称")
    code: str = Field(..., max_length=50, description="角色编码")
    description: Optional[str] = Field(default=None, max_length=500)
    sort: int = Field(default=0, description="排序")


class RoleCreate(RoleBase):
    permission_ids: List[int] = Field(default_factory=list, description="权限ID列表")


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    sort: Optional[int] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)
    permission_ids: Optional[List[int]] = Field(default=None, description="权限ID列表")


class RoleOut(RoleBase):
    id: int
    is_active: bool
    created_at: datetime
    permissions: List[PermissionOut] = Field(default_factory=list)
    user_count: int = Field(default=0, description="用户数")

    class Config:
        from_attributes = True


# ── 部门 ─────────────────────────────────────────
class DepartmentBase(BaseModel):
    name: str = Field(..., max_length=100, description="部门名称")
    parent_id: Optional[int] = Field(default=None, description="上级部门ID")
    manager_id: Optional[int] = Field(default=None, description="负责人ID")
    sort: int = Field(default=0)
    description: Optional[str] = Field(default=None, max_length=500)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    parent_id: Optional[int] = Field(default=None)
    manager_id: Optional[int] = Field(default=None)
    sort: Optional[int] = Field(default=None)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = Field(default=None)


class DepartmentOut(DepartmentBase):
    id: int
    is_active: bool
    created_at: datetime
    children: Optional[List["DepartmentOut"]] = None
    user_count: int = Field(default=0)

    class Config:
        from_attributes = True


# ── 用户 ─────────────────────────────────────────
class UserBase(BaseModel):
    username: str = Field(..., max_length=50, description="用户名")
    email: Optional[str] = Field(default=None, max_length=100, description="邮箱")
    full_name: Optional[str] = Field(default=None, max_length=100, description="姓名")
    phone: Optional[str] = Field(default=None, max_length=20, description="手机号")
    department_id: Optional[int] = Field(default=None, description="部门ID")
    position: Optional[str] = Field(default=None, max_length=100, description="职位")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    role_ids: List[int] = Field(default_factory=list, description="角色ID列表")


class UserUpdate(BaseModel):
    email: Optional[str] = Field(default=None, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=100)
    english_name: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    department_id: Optional[int] = Field(default=None)
    position: Optional[str] = Field(default=None, max_length=100)
    motto: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = Field(default=None)
    role_ids: Optional[List[int]] = Field(default=None, description="角色ID列表")


class UserOut(UserBase):
    id: int
    avatar: Optional[str]
    is_active: bool
    is_superuser: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    roles: List[RoleOut] = Field(default_factory=list)
    department: Optional[DepartmentOut] = None

    class Config:
        from_attributes = True


class UserListOut(BaseModel):
    """用户列表（简化版）"""
    id: int
    username: str
    full_name: Optional[str]
    english_name: Optional[str] = None
    email: Optional[str]
    phone: Optional[str]
    avatar: Optional[str]
    motto: Optional[str] = None
    position: Optional[str]
    is_active: bool
    is_superuser: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    department_name: Optional[str] = None
    role_names: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True
