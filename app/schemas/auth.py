"""
认证相关 Schema：登录、注册、令牌
"""
from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名/邮箱")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    remember_me: bool = Field(default=False, description="记住我 (延长Token有效期)")


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    confirm_password: str = Field(..., min_length=6, max_length=128, description="确认密码")
    email: Optional[str] = Field(default=None, max_length=100, description="邮箱")
    full_name: Optional[str] = Field(default=None, max_length=100, description="姓名")
    phone: Optional[str] = Field(default=None, max_length=20, description="手机号")


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")
    confirm_password: str = Field(..., min_length=6, max_length=128, description="确认新密码")


class TokenPayload(BaseModel):
    """JWT Token 解析后的数据"""
    sub: str = Field(..., description="用户ID")
    username: Optional[str] = Field(default=None, description="用户名")
    exp: int = Field(..., description="过期时间戳")
    type: str = Field(default="access", description="令牌类型: access/refresh")
