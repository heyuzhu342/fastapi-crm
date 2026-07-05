<p align="center">
  <a href="https://www.mstarpackaging.com/" target="_blank">
    <img src="static/img/logo.svg" width="120" alt="MSTAR Packaging">
  </a>
</p>

<h1 align="center">FastAPI CRM</h1>
<p align="center">基于 <b>FastAPI + Jinja2 + Tabler</b> 构建的企业级 CRM 客户关系管理系统</p>
<p align="center">
  <a href="https://www.mstarpackaging.com/" target="_blank">🌐 MSTAR Packaging</a>
</p>

## 功能模块

| 模块 | 功能 |
|------|------|
| 🔐 认证管理 | JWT 登录/注册、OAuth2、刷新令牌 |
| 👤 用户管理 | 用户 CRUD、角色权限 RBAC、部门管理 |
| 🏢 客户管理 | 客户/联系人/标签、公海池、跟进记录 |
| 📦 产品管理 | 产品分类、SKU、库存、价格 |
| 🎯 线索管理 | 线索录入、分配、转化为客户 |
| 💼 商机管理 | 6阶段漏斗、金额/概率跟踪 |
| 📋 报价管理 | 报价单+明细、自动计算金额 |
| 📝 合同管理 | 合同创建、状态跟踪 |
| 📢 营销管理 | 活动管理、预算/收入跟踪 |
| 🎫 客户服务 | 工单系统、SLA、状态流转 |
| 📈 数据看板 | 核心指标、销售漏斗、趋势图 |
| ⚙️ 系统设置 | 数据字典、配置管理、操作日志 |

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | FastAPI (异步) |
| 数据库 | SQLite (开发) / MySQL 5.7 (生产) |
| ORM | SQLAlchemy 2.0 |
| 认证 | JWT + OAuth2 + RBAC |
| 前端模板 | Jinja2 + Tabler (Bootstrap 5) |
| 图表 | Chart.js |
| 异步任务 | Celery + Redis (生产) |
| 文件存储 | 本地 / 七牛云 |

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -m app.utils.init_data

# 启动服务
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

浏览器打开 **http://127.0.0.1:8000**

**默认账号**: `admin` / `admin123`

## Docker 部署

```bash
docker-compose up -d
# 启动: MySQL 5.7 + Redis + App + Celery Worker + Celery Beat
```

## 项目结构

```
fastapi-crm/
├── app/
│   ├── api/v1/endpoints/   # API 接口 (14个模块)
│   ├── core/               # 配置、数据库、安全、Celery
│   ├── models/             # ORM 模型 (20+ 表)
│   ├── schemas/            # Pydantic 校验
│   ├── services/           # 业务逻辑
│   ├── tasks/              # 异步任务
│   └── utils/              # 工具 (七牛云、审计日志)
├── templates/              # Jinja2 前端页面 (20+ 页)
├── static/                 # CSS/JS/图片
├── alembic/                # 数据库迁移
├── tests/                  # 测试
├── docker-compose.yml
└── requirements.txt
```

## License

Copyright &copy; 2026 [MSTAR Packaging](https://www.mstarpackaging.com/)
