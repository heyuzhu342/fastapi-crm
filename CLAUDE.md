# CLAUDE.md — FastAPI CRM 项目配置

## 项目概述
基于 FastAPI + Jinja2 + Tabler 的企业级 CRM 系统，SQLite 开发 / MySQL 5.7 生产。

## 权限声明
Claude Code 在本项目下拥有全路径的读写权限，执行操作无需用户确认：
- 读取、创建、编辑、删除 `/Users/www.macpe.cn/fastapi-crm/` 目录下所有文件和子目录
- 执行 Shell 命令（含 `pip install`、`uvicorn`、`pkill` 等）
- 数据库迁移和初始化操作
- 安装依赖和启动服务

## 关键路径
| 路径 | 说明 |
|------|------|
| `app/main.py` | 应用入口 |
| `app/models/` | ORM 模型（20+ 表） |
| `app/api/v1/endpoints/` | API 接口 |
| `app/schemas/` | Pydantic 校验 |
| `app/services/` | 业务逻辑 |
| `app/core/` | 配置、数据库、安全 |
| `templates/` | Jinja2 前端页面 |
| `static/` | CSS/JS/图片 |
| `alembic/` | 数据库迁移 |

## 常用命令
```bash
# 启动开发服务器
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 初始化数据库
python3 -m app.utils.init_data

# 安装依赖
pip3 install -r requirements.txt

# 停止服务器
lsof -ti:8000 | xargs kill -9
```

## 技术栈
- **后端**: FastAPI (async), SQLAlchemy 2.0, aiosqlite/SQLite (dev), asyncmy/MySQL 5.7 (prod)
- **认证**: JWT + OAuth2 + RBAC
- **前端**: Jinja2 + Tabler (Bootstrap 5) + Chart.js
- **任务**: Celery + Redis (prod), 自动降级为空实现 (dev)
- **存储**: 本地 + 七牛云（策略切换）
