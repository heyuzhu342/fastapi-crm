"""
用户管理接口：CRUD、角色分配、部门管理
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.api.deps import get_current_user, pagination_params, require_superuser
from app.models.user import User, Role, Department
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserOut,
    UserListOut,
    RoleCreate,
    RoleUpdate,
    RoleOut,
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentOut,
)
from app.schemas.common import ResponseModel, ResponseList
from app.services.base_crud import BaseCRUD

router = APIRouter(prefix="/users", tags=["👤 用户管理"])

user_crud = BaseCRUD(User)
role_crud = BaseCRUD(Role)
dept_crud = BaseCRUD(Department)


# ── 用户 CRUD ────────────────────────────────────

@router.get("", response_model=ResponseList[UserListOut], summary="用户列表")
async def list_users(
    pagination: dict = Depends(pagination_params),
    is_active: bool = None,
    department_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户列表（支持搜索、筛选、分页）"""
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active
    if department_id is not None:
        filters["department_id"] = department_id

    result = await user_crud.get_list(
        db,
        page=pagination["page"],
        page_size=pagination["page_size"],
        sort_by=pagination["sort_by"],
        order=pagination["order"],
        search=pagination["search"],
        search_fields=["username", "full_name", "email", "phone"],
        filters=filters,
    )

    # 格式化输出
    items = []
    for user in result["items"]:
        items.append(UserListOut(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            avatar=user.avatar,
            position=user.position,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            department_name=None,  # avoid lazy load
            role_names=[]  # avoid lazy load,
        ))

    return ResponseList(
        data=items,
        meta={
            "page": result["page"],
            "page_size": result["page_size"],
            "total": result["total"],
            "total_pages": result["total_pages"],
        },
    )


@router.get("/{user_id}", response_model=ResponseModel, summary="用户详情")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取指定用户的详细信息"""
    result = await db.execute(
        select(User)
        .options(
            joinedload(User.roles).joinedload(Role.permissions),
            joinedload(User.department),
        )
        .where(User.id == user_id)
    )
    user = result.unique().scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return ResponseModel(data={
        "id": user.id, "username": user.username, "email": user.email,
        "full_name": user.full_name, "phone": user.phone, "avatar": user.avatar,
        "position": user.position, "is_active": user.is_active, "is_superuser": user.is_superuser,
        "department_id": user.department_id, "department_name": user.department.name if user.department else None,
        "roles": [{"id": r.id, "name": r.name, "code": r.code} for r in user.roles],
        "last_login_at": str(user.last_login_at) if user.last_login_at else None,
        "created_at": str(user.created_at), "updated_at": str(user.updated_at),
    })


@router.post("", response_model=ResponseModel, summary="创建用户")
async def create_user(
    data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新用户"""
    from app.core.security import hash_password

    # 检查用户名唯一性
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user_data = data.model_dump(exclude={"role_ids", "password"})
    user_data["hashed_password"] = hash_password(data.password)

    # 分配角色
    role_ids = data.role_ids
    roles = []
    if role_ids:
        result = await db.execute(select(Role).where(Role.id.in_(role_ids)))
        roles = result.unique().scalars().all()

    user = User(**user_data)
    user.roles = roles
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return ResponseModel(data={"id": user.id, "username": user.username}, message="用户创建成功")


@router.put("/{user_id}", response_model=ResponseModel, summary="更新用户")
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新用户信息"""
    result = await db.execute(
        select(User).options(joinedload(User.roles)).where(User.id == user_id)
    )
    user = result.unique().scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = data.model_dump(exclude_unset=True, exclude={"role_ids"})

    # 更新角色
    if data.role_ids is not None:
        roles_result = await db.execute(
            select(Role).where(Role.id.in_(data.role_ids))
        )
        user.roles = roles_result.unique().scalars().all()

    for key, value in update_data.items():
        if value is not None:
            setattr(user, key, value)

    await db.flush()
    await db.refresh(user)

    return ResponseModel(data={"id": user.id, "username": user.username}, message="用户更新成功")


@router.delete("/{user_id}", response_model=ResponseModel, summary="删除用户")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    """删除用户（需要超级管理员权限）"""
    success = await user_crud.soft_delete(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    return ResponseModel(message="用户已删除")


# ── 角色 CRUD ────────────────────────────────────

@router.get("/roles/all", response_model=ResponseModel[list[RoleOut]], summary="角色列表")
async def list_roles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有角色"""
    result = await db.execute(
        select(Role)
        .options(joinedload(Role.permissions), joinedload(Role.users))
        .order_by(Role.sort)
    )
    roles = result.unique().scalars().all()
    data = []
    for r in roles:
        ro = RoleOut.model_validate(r)
        ro.user_count = len(r.users)
        data.append(ro)
    return ResponseModel(data=data)


@router.post("/roles", response_model=ResponseModel, summary="创建角色")
async def create_role(
    data: RoleCreate,
    current_user: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    """创建新角色并分配权限"""
    from app.models.user import Permission
    role_data = data.model_dump(exclude={"permission_ids"})
    role = Role(**role_data)

    if data.permission_ids:
        result = await db.execute(
            select(Permission).where(Permission.id.in_(data.permission_ids))
        )
        role.permissions = result.unique().scalars().all()

    db.add(role)
    await db.flush()
    await db.refresh(role)
    return ResponseModel(data=RoleOut.model_validate(role), message="角色创建成功")


@router.put("/roles/{role_id}", response_model=ResponseModel, summary="更新角色")
async def update_role(
    role_id: int,
    data: RoleUpdate,
    current_user: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    """更新角色"""
    from app.models.user import Permission
    result = await db.execute(
        select(Role).options(joinedload(Role.permissions)).where(Role.id == role_id)
    )
    role = result.unique().scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=404, detail="角色不存在")

    update_data = data.model_dump(exclude_unset=True, exclude={"permission_ids"})

    if data.permission_ids is not None:
        perm_result = await db.execute(
            select(Permission).where(Permission.id.in_(data.permission_ids))
        )
        role.permissions = perm_result.unique().scalars().all()

    for key, value in update_data.items():
        if value is not None:
            setattr(role, key, value)

    await db.flush()
    await db.refresh(role)
    return ResponseModel(data=RoleOut.model_validate(role), message="角色更新成功")


# ── 部门 CRUD ────────────────────────────────────

@router.get("/departments/tree", response_model=ResponseModel[list[DepartmentOut]], summary="部门树")
async def department_tree(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取部门树形结构"""
    result = await db.execute(
        select(Department).options(joinedload(Department.children)).where(Department.parent_id.is_(None)).order_by(Department.sort)
    )
    departments = result.unique().scalars().all()

    def build_tree(depts):
        data = []
        for d in depts:
            do = DepartmentOut.model_validate(d)
            do.children = build_tree(d.children) if d.children else []
            do.user_count = 0  # avoid lazy load
            data.append(do)
        return data

    return ResponseModel(data=build_tree(departments))


@router.post("/departments", response_model=ResponseModel, summary="创建部门")
async def create_department(
    data: DepartmentCreate,
    current_user: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    """创建部门"""
    dept = Department(**data.model_dump())
    db.add(dept)
    await db.flush()
    await db.refresh(dept)
    return ResponseModel(data={"id": dept.id, "name": dept.name}, message="部门创建成功")
