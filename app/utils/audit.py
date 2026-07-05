"""
审计日志工具 — 自动记录所有 API 操作
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import AuditLog
from app.core.security import decode_token


# 资源名映射（API路径 → 中文资源名 + 操作类型）
RESOURCE_MAP = {
    # key: (method, path_start) => (resource_name, action)
    ("POST", "/api/v1/auth/login"): ("用户登录", "login"),
    ("POST", "/api/v1/auth/register"): ("用户注册", "register"),
    ("GET", "/api/v1/customers"): ("客户管理", "list"),
    ("POST", "/api/v1/customers"): ("客户管理", "create"),
    ("PUT", "/api/v1/customers"): ("客户管理", "update"),
    ("DELETE", "/api/v1/customers"): ("客户管理", "delete"),
    ("POST", "/api/v1/leads"): ("线索管理", "create"),
    ("PUT", "/api/v1/leads"): ("线索管理", "update"),
    ("DELETE", "/api/v1/leads"): ("线索管理", "delete"),
    ("POST", "/api/v1/opportunities"): ("商机管理", "create"),
    ("PUT", "/api/v1/opportunities"): ("商机管理", "update"),
    ("POST", "/api/v1/quotations"): ("报价管理", "create"),
    ("PUT", "/api/v1/quotations"): ("报价管理", "update"),
    ("DELETE", "/api/v1/quotations"): ("报价管理", "delete"),
    ("POST", "/api/v1/contracts"): ("合同管理", "create"),
    ("PUT", "/api/v1/contracts"): ("合同管理", "update"),
    ("DELETE", "/api/v1/contracts"): ("合同管理", "delete"),
    ("POST", "/api/v1/products"): ("产品管理", "create"),
    ("PUT", "/api/v1/products"): ("产品管理", "update"),
    ("DELETE", "/api/v1/products"): ("产品管理", "delete"),
    ("POST", "/api/v1/campaigns"): ("营销管理", "create"),
    ("PUT", "/api/v1/campaigns"): ("营销管理", "update"),
    ("DELETE", "/api/v1/campaigns"): ("营销管理", "delete"),
    ("POST", "/api/v1/tickets"): ("工单管理", "create"),
    ("PUT", "/api/v1/tickets"): ("工单管理", "update"),
    ("POST", "/api/v1/users"): ("用户管理", "create"),
    ("PUT", "/api/v1/users"): ("用户管理", "update"),
    ("DELETE", "/api/v1/users"): ("用户管理", "delete"),
    ("POST", "/api/v1/system"): ("系统设置", "update"),
    ("PUT", "/api/v1/system"): ("系统设置", "update"),
    ("DELETE", "/api/v1/system"): ("系统设置", "delete"),
}


def resolve_resource(method: str, path: str) -> tuple[str, str]:
    """根据请求方法和路径匹配资源和操作"""
    # 去版本化
    clean_path = path
    if "/api/v1/" in clean_path:
        clean_path = clean_path.replace("/api/v1", "")

    for (m, prefix), (res, action) in RESOURCE_MAP.items():
        if method == m and clean_path.startswith(prefix):
            # 对于PUT/DELETE带ID的路径同样匹配
            return res, action

    # 默认
    if method == "GET":
        return "数据查询", "list"
    elif method == "POST":
        return "数据操作", "create"
    elif method == "PUT":
        return "数据操作", "update"
    elif method == "DELETE":
        return "数据操作", "delete"
    return "系统", "other"


async def write_audit_log(
    db: AsyncSession,
    request,
    status: str = "success",
    detail: Optional[str] = None,
):
    """
    写入审计日志
    自动从 Authorization header 解析用户信息
    """
    # 跳过健康检查、静态文件、页面请求
    path = request.url.path
    if path in ("/health", "/", "/login", "/register", "/docs", "/redoc", "/openapi.json"):
        return
    if path.startswith("/static/") or path.startswith("/favicon"):
        return

    method = request.method
    if method == "GET":
        return  # 查询操作不记日志，减少数据量

    # 解析资源名
    resource, action = resolve_resource(method, path)

    # 解析用户
    user_id = None
    username = None
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        payload = decode_token(auth[7:])
        if payload:
            user_id = payload.get("sub")
            username = payload.get("username")

    log = AuditLog(
        user_id=int(user_id) if user_id else None,
        username=username or "匿名用户",
        action=action,
        resource=resource,
        resource_id=None,
        detail=detail or f"{method} {path}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent", "")[:500],
        status=status,
    )
    db.add(log)
    await db.flush()
