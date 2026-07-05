"""
审计中间件 — 自动记录所有非 GET API 操作
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request
from app.utils.audit import write_audit_log
from app.core.database import async_session_factory


class AuditMiddleware(BaseHTTPMiddleware):
    """自动审计日志中间件"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # 先执行请求
        response = await call_next(request)

        # 只记录非 GET 的 API 操作，排除登录和健康检查
        if request.method == "GET":
            return response
        if not request.url.path.startswith("/api/"):
            return response
        if "/auth/token" in request.url.path or "/auth/refresh" in request.url.path:
            return response
        if "/health" in request.url.path:
            return response

        # 记录日志
        status = "success" if 200 <= response.status_code < 400 else "failure"
        try:
            async with async_session_factory() as db:
                await write_audit_log(db, request, status=status)
                await db.commit()
        except Exception:
            pass  # 日志写入失败不影响主流程

        return response
