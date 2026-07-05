"""
FastAPI CRM 应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse, JSONResponse
from app.core.config import settings
from app.api.v1 import api_router


# ── 应用生命周期 ─────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动/关闭时的处理"""
    # 启动时
    from app.core.database import engine
    # TODO: 生产环境应使用 Alembic 迁移，此处仅为开发便利
    yield
    # 关闭时
    await engine.dispose()


# ── 创建应用 ─────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 🚀 FastAPI CRM 企业级客户关系管理系统

### 功能模块
- 🔐 **认证管理** — 登录、注册、JWT Token
- 👤 **用户管理** — 用户 CRUD、角色权限 RBAC
- 🏢 **客户管理** — 客户、联系人、标签、跟进记录
- 📦 **产品管理** — 产品分类、库存、价格
- 📊 **销售管理** — 线索→商机→报价→合同
- 📋 **营销管理** — 营销活动追踪
- 🎫 **客户服务** — 工单系统、SLA管理
- 📈 **报表分析** — 销售漏斗、业绩报表
- 🔔 **通知消息** — 站内通知、邮件提醒
- ⚙️ **系统设置** — 数据字典、参数配置

### 技术栈
| 组件 | 技术 |
|------|------|
| 框架 | FastAPI (异步) |
| 数据库 | MySQL 5.7 + asyncmy |
| ORM | SQLAlchemy 2.0 |
| 认证 | JWT + OAuth2 |
| 异步任务 | Celery + Redis |
| 文件存储 | 本地 / 七牛云 |
| 前端模板 | Jinja2 + Tabler |
    """,
    # Swagger 使用国内 CDN（jsdelivr 被墙）
    swagger_js_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.11.0/swagger-ui-bundle.js",
    swagger_css_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.11.0/swagger-ui.css",
    redoc_url=None,  # Redoc CDN 也被墙，先禁用
    lifespan=lifespan,
)

# ── CORS 中间件 ──────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 审计中间件 ──────────────────────────────────
from app.middleware import AuditMiddleware
app.add_middleware(AuditMiddleware)

# ── 静态文件 & 模板 ──────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
templates.env.globals["settings"] = settings


# ── 注册 API 路由 ────────────────────────────────
app.include_router(api_router)


# ── 全局异常处理 ─────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常捕获"""
    from loguru import logger
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": str(exc) if settings.DEBUG else None,
        },
    )



# ── 健康检查 ─────────────────────────────────────
@app.get("/health", tags=["系统"], summary="健康检查")
async def health_check():
    """系统健康检查接口"""
    return {"status": "ok", "version": settings.APP_VERSION}


# ── 前端页面路由 ─────────────────────────────────
@app.get("/", response_class=HTMLResponse, tags=["页面"], summary="首页")
async def index(request: Request):
    """CRM 首页仪表盘"""
    return templates.TemplateResponse("pages/index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse, tags=["页面"], summary="登录页")
async def login_page(request: Request):
    """登录页面"""
    return templates.TemplateResponse("pages/auth/login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse, tags=["页面"], summary="注册页")
async def register_page(request: Request):
    """注册页面"""
    return templates.TemplateResponse("pages/auth/register.html", {"request": request})


# ── 个人资料 ──────────────────────────────────────
@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    return templates.TemplateResponse("pages/profile/index.html", {"request": request})


@app.get("/profile/change-password", response_class=HTMLResponse)
async def change_password_page(request: Request):
    return templates.TemplateResponse("pages/profile/change-password.html", {"request": request})


# ── 客户管理页面 ─────────────────────────────────
@app.get("/customers", response_class=HTMLResponse, tags=["页面"], summary="客户列表")
async def customers_list(request: Request):
    return templates.TemplateResponse("pages/customers/list.html", {"request": request})


@app.get("/customers/create", response_class=HTMLResponse, tags=["页面"], summary="添加客户")
async def customer_create(request: Request):
    return templates.TemplateResponse("pages/customers/form.html", {"request": request, "is_edit": False})


@app.get("/customers/pool", response_class=HTMLResponse)
async def customers_pool(request: Request):
    return templates.TemplateResponse("pages/customers/pool.html", {"request": request})

@app.get("/customers/tags", response_class=HTMLResponse)
async def customers_tags(request: Request):
    return templates.TemplateResponse("pages/customers/tags.html", {"request": request})

@app.get("/customers/{customer_id}", response_class=HTMLResponse, tags=["页面"], summary="客户详情")
async def customer_detail(request: Request, customer_id: int):
    return templates.TemplateResponse("pages/customers/detail.html", {"request": request})


@app.get("/customers/{customer_id}/edit", response_class=HTMLResponse, tags=["页面"], summary="编辑客户")
async def customer_edit(request: Request, customer_id: int):
    return templates.TemplateResponse("pages/customers/form.html", {"request": request, "is_edit": True})


# ── 产品管理页面 ─────────────────────────────────
@app.get("/products", response_class=HTMLResponse, tags=["页面"], summary="产品列表")
async def products_list(request: Request):
    return templates.TemplateResponse("pages/products/list.html", {"request": request})


@app.get("/products/create", response_class=HTMLResponse, tags=["页面"], summary="添加产品")
async def product_create(request: Request):
    return templates.TemplateResponse("pages/products/form.html", {"request": request})

@app.get("/products/categories", response_class=HTMLResponse)
async def products_categories(request: Request):
    return templates.TemplateResponse("pages/products/categories.html", {"request": request})

@app.get("/products/{product_id}", response_class=HTMLResponse, tags=["页面"], summary="产品详情")
async def product_detail(request: Request, product_id: int):
    return templates.TemplateResponse("pages/products/list.html", {"request": request})


@app.get("/products/{product_id}/edit", response_class=HTMLResponse, tags=["页面"], summary="编辑产品")
async def product_edit(request: Request, product_id: int):
    return templates.TemplateResponse("pages/products/form.html", {"request": request})


# ── 销售管理页面 ─────────────────────────────────
@app.get("/leads", response_class=HTMLResponse)
async def leads_page(request: Request):
    return templates.TemplateResponse("pages/leads/list.html", {"request": request})

@app.get("/leads/create", response_class=HTMLResponse)
async def lead_create_page(request: Request):
    return templates.TemplateResponse("pages/leads/form.html", {"request": request})

@app.get("/leads/{lead_id}", response_class=HTMLResponse)
async def lead_detail_page(request: Request, lead_id: int):
    return templates.TemplateResponse("pages/leads/list.html", {"request": request})

@app.get("/leads/{lead_id}/edit", response_class=HTMLResponse)
async def lead_edit_page(request: Request, lead_id: int):
    return templates.TemplateResponse("pages/leads/form.html", {"request": request})

@app.get("/opportunities", response_class=HTMLResponse)
async def opportunities_page(request: Request):
    return templates.TemplateResponse("pages/opportunities/list.html", {"request": request})

@app.get("/opportunities/create", response_class=HTMLResponse)
async def opp_create_page(request: Request):
    return templates.TemplateResponse("pages/opportunities/form.html", {"request": request})

@app.get("/opportunities/{opp_id}", response_class=HTMLResponse)
async def opp_detail_page(request: Request, opp_id: int):
    return templates.TemplateResponse("pages/opportunities/list.html", {"request": request})

@app.get("/opportunities/{opp_id}/edit", response_class=HTMLResponse)
async def opp_edit_page(request: Request, opp_id: int):
    return templates.TemplateResponse("pages/opportunities/form.html", {"request": request})

@app.get("/quotations", response_class=HTMLResponse)
async def quotations_page(request: Request):
    return templates.TemplateResponse("pages/quotations/list.html", {"request": request})

@app.get("/contracts", response_class=HTMLResponse)
async def contracts_page(request: Request):
    return templates.TemplateResponse("pages/contracts/list.html", {"request": request})


# ── 营销 + 工单 + 系统 + 补全页面 ──────────────────
@app.get("/campaigns", response_class=HTMLResponse)
async def campaigns_page(request: Request):
    return templates.TemplateResponse("pages/campaigns/list.html", {"request": request})

@app.get("/campaigns/create", response_class=HTMLResponse)
async def campaign_create_page(request: Request):
    return templates.TemplateResponse("pages/campaigns/form.html", {"request": request})

@app.get("/tickets", response_class=HTMLResponse)
async def tickets_page(request: Request):
    return templates.TemplateResponse("pages/tickets/list.html", {"request": request})

@app.get("/tickets/create", response_class=HTMLResponse)
async def ticket_create_page(request: Request):
    return templates.TemplateResponse("pages/tickets/form.html", {"request": request})

@app.get("/contracts/create", response_class=HTMLResponse)
async def contract_create_page(request: Request):
    return templates.TemplateResponse("pages/contracts/form.html", {"request": request})

@app.get("/quotations/create", response_class=HTMLResponse)
async def quotation_create_page(request: Request):
    return templates.TemplateResponse("pages/quotations/list.html", {"request": request})

@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    return templates.TemplateResponse("pages/index.html", {"request": request})

# ── 用户管理页面 ──────────────────────────────────
@app.get("/users", response_class=HTMLResponse)
async def users_list_page(request: Request):
    return templates.TemplateResponse("pages/users/list.html", {"request": request})

@app.get("/users/create", response_class=HTMLResponse)
async def users_create_page(request: Request):
    return templates.TemplateResponse("pages/users/form.html", {"request": request})

@app.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def users_edit_page(request: Request, user_id: int):
    return templates.TemplateResponse("pages/users/form.html", {"request": request})

@app.get("/users/roles", response_class=HTMLResponse)
async def users_roles(request: Request):
    return templates.TemplateResponse("pages/users/roles.html", {"request": request})

@app.get("/users/departments", response_class=HTMLResponse)
async def users_departments(request: Request):
    return templates.TemplateResponse("pages/users/departments.html", {"request": request})

# ── 系统设置页面 ──────────────────────────────────
@app.get("/system/config", response_class=HTMLResponse)
async def system_config_page(request: Request):
    return templates.TemplateResponse("pages/system/config.html", {"request": request})

@app.get("/system/dict", response_class=HTMLResponse)
async def system_dict(request: Request):
    return templates.TemplateResponse("pages/system/dict.html", {"request": request})

@app.get("/system/logs", response_class=HTMLResponse)
async def system_logs(request: Request):
    return templates.TemplateResponse("pages/system/config.html", {"request": request})
