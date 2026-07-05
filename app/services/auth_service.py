"""
认证服务：登录、注册、令牌管理
"""
from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User, Role


class AuthService:
    """认证服务"""

    @staticmethod
    async def authenticate(
        db: AsyncSession,
        username: str,
        password: str,
        remember_me: bool = False,
    ) -> dict:
        """
        用户登录认证
        - 支持用户名或邮箱登录
        - return: {access_token, refresh_token, token_type, expires_in}
        """
        # 查询用户（用户名 或 邮箱）
        result = await db.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(
                (User.username == username) | (User.email == username)
            )
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
            )

        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已被禁用，请联系管理员",
            )

        # 构造 Token 附加信息
        extra_claims = {
            "username": user.username,
            "is_superuser": user.is_superuser,
        }

        # 生成令牌
        access_token_expires = (
            timedelta(days=7) if remember_me
            else timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token_expires = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(
            subject=user.id,
            extra_claims=extra_claims,
            expires_delta=access_token_expires,
        )
        refresh_token = create_refresh_token(
            subject=user.id,
            expires_delta=refresh_token_expires,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds()),
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
                "avatar": user.avatar,
                "is_superuser": user.is_superuser,
            },
        }

    @staticmethod
    async def register(
        db: AsyncSession,
        username: str,
        password: str,
        confirm_password: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> User:
        """用户注册"""
        if password != confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="两次密码不一致",
            )

        # 检查用户名是否已存在
        result = await db.execute(
            select(User).where(User.username == username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在",
            )

        # 检查邮箱是否已存在
        if email:
            result = await db.execute(
                select(User).where(User.email == email)
            )
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已注册",
                )

        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name or username,
            phone=phone,
        )

        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def refresh_access_token(
        db: AsyncSession,
        refresh_token: str,
    ) -> dict:
        """使用刷新令牌获取新的访问令牌"""
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌",
            )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌",
            )

        # 确认用户存在且可用
        result = await db.execute(
            select(User).where(User.id == int(user_id))
        )
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已禁用",
            )

        extra_claims = {
            "username": user.username,
            "is_superuser": user.is_superuser,
        }

        access_token = create_access_token(
            subject=user.id,
            extra_claims=extra_claims,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user: User,
        old_password: str,
        new_password: str,
        confirm_password: str,
    ) -> bool:
        """修改密码"""
        if not verify_password(old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码错误",
            )

        if new_password != confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="两次新密码不一致",
            )

        user.hashed_password = hash_password(new_password)
        await db.flush()
        return True
