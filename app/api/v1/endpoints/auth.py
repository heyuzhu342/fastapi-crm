"""
认证接口：登录、注册、刷新令牌、修改密码
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, oauth2_scheme
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ChangePasswordRequest,
)
from app.schemas.common import ResponseModel
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["🔐 认证管理"])


@router.post("/token", summary="OAuth2 登录（Swagger 认证用）")
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    OAuth2 标准登录接口 — Swagger UI 的 Authorize 按钮使用此接口
    返回标准 OAuth2 格式，token 在顶层
    """
    result = await AuthService.authenticate(
        db=db,
        username=form_data.username,
        password=form_data.password,
    )
    # OAuth2 规范：token 必须在响应顶层
    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": result["token_type"],
        "expires_in": result["expires_in"],
    }


@router.post("/login", response_model=ResponseModel[dict], summary="用户登录")
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登录接口

    - 支持 **用户名** 或 **邮箱** 登录
    - `remember_me=true` 时，访问令牌有效期延长至 7 天
    - 返回 `access_token`（访问令牌）和 `refresh_token`（刷新令牌）
    """
    result = await AuthService.authenticate(
        db=db,
        username=request.username,
        password=request.password,
        remember_me=request.remember_me,
    )
    return ResponseModel(data=result, message="登录成功")


@router.post("/register", response_model=ResponseModel[dict], summary="用户注册")
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    新用户注册

    - `confirm_password` 必须与 `password` 一致
    - 用户名和邮箱需唯一
    """
    user = await AuthService.register(
        db=db,
        username=request.username,
        password=request.password,
        confirm_password=request.confirm_password,
        email=request.email,
        full_name=request.full_name,
        phone=request.phone,
    )
    return ResponseModel(
        data={"id": user.id, "username": user.username},
        message="注册成功",
    )


@router.post("/refresh", response_model=ResponseModel[dict], summary="刷新令牌")
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    使用刷新令牌获取新的访问令牌

    - 访问令牌过期后，使用此接口获取新令牌
    - 无需重新登录
    """
    result = await AuthService.refresh_access_token(
        db=db,
        refresh_token=request.refresh_token,
    )
    return ResponseModel(data=result, message="令牌刷新成功")


@router.post("/change-password", response_model=ResponseModel, summary="修改密码")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """修改当前登录用户的密码"""
    await AuthService.change_password(
        db=db,
        user=current_user,
        old_password=request.old_password,
        new_password=request.new_password,
        confirm_password=request.confirm_password,
    )
    return ResponseModel(message="密码修改成功")


@router.put("/me", response_model=ResponseModel, summary="更新个人资料")
async def update_profile(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新当前用户个人资料（邮箱、手机、姓名等）"""
    allowed = {"email", "phone", "full_name", "position"}
    for k, v in data.items():
        if k in allowed and v is not None:
            setattr(current_user, k, v)
    await db.flush()
    return ResponseModel(data={"id": current_user.id, "username": current_user.username}, message="个人资料已更新")


@router.get("/me", response_model=ResponseModel[dict], summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """获取当前登录用户的详细信息"""
    return ResponseModel(
        data={
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "phone": current_user.phone,
            "avatar": current_user.avatar,
            "position": current_user.position,
            "is_superuser": current_user.is_superuser,
            "is_active": current_user.is_active,
            "department_id": current_user.department_id,
            "department_name": current_user.department.name if current_user.department else None,
            "roles": [
                {"id": r.id, "name": r.name, "code": r.code}
                for r in current_user.roles
            ],
            "last_login_at": current_user.last_login_at,
            "created_at": current_user.created_at,
        }
    )
