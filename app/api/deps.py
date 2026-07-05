"""
API 依赖注入：认证、权限、分页、数据库会话
"""
from typing import Optional
from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, Role


# ── OAuth2 方案 ──────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    description="输入 Bearer Token",
)


# ── 获取当前用户 ─────────────────────────────────
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 JWT Token 解析当前登录用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证失败，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请使用访问令牌，非刷新令牌",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # 加载用户和角色（避免后续 lazy load 产生 greenlet 错误）
    result = await db.execute(
        select(User)
        .options(joinedload(User.roles))
        .where(User.id == int(user_id))
    )
    user = result.unique().scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用，请联系管理员",
        )

    return user


# ── 获取当前用户（可选，用于非强制登录接口）───────
async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """可选的用户认证，不强制要求登录"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return None

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    return result.scalar_one_or_none()


# ── 超级管理员检查 ───────────────────────────────
async def require_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """要求超级管理员权限"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限",
        )
    return current_user


# ── RBAC 权限检查工厂 ───────────────────────────
def require_permission(permission_code: str):
    """
    权限检查依赖工厂
    用法: Depends(require_permission("customer:create"))
    """
    async def check_permission(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        if current_user.is_superuser:
            return current_user

        # 显式加载角色和权限（用于权限判断）
        result = await db.execute(
            select(User)
            .options(
                joinedload(User.roles).joinedload(Role.permissions)
            )
            .where(User.id == current_user.id)
        )
        user = result.unique().scalar_one()

        for role in user.roles:
            if not role.is_active:
                continue
            for perm in role.permissions:
                if perm.is_active and perm.code == permission_code:
                    return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"缺少权限: {permission_code}",
        )
    return check_permission


# ── 分页参数 ─────────────────────────────────────
async def pagination_params(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, alias="page_size", description="每页数量"),
    sort_by: Optional[str] = Query(default="created_at", description="排序字段"),
    order: str = Query(default="desc", description="排序方向"),
    search: Optional[str] = Query(default=None, description="搜索关键词"),
) -> dict:
    """通用分页参数依赖"""
    return {
        "page": page,
        "page_size": page_size,
        "sort_by": sort_by,
        "order": order.lower(),
        "search": search,
        "offset": (page - 1) * page_size,
    }
