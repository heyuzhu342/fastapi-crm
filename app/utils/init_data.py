"""
初始化数据：默认角色、权限、管理员账号
运行方式: python -m app.utils.init_data
"""
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_factory
from app.core.security import hash_password
from app.models.user import User, Role, Permission, Department


# ── 默认权限集 ───────────────────────────────────
DEFAULT_PERMISSIONS = [
    # 客户管理
    {"name": "查看客户", "code": "customer:list", "resource": "customer:list", "menu_type": "button"},
    {"name": "创建客户", "code": "customer:create", "resource": "customer:create", "menu_type": "button"},
    {"name": "编辑客户", "code": "customer:update", "resource": "customer:update", "menu_type": "button"},
    {"name": "删除客户", "code": "customer:delete", "resource": "customer:delete", "menu_type": "button"},
    {"name": "导出客户", "code": "customer:export", "resource": "customer:export", "menu_type": "button"},
    # 销售管理
    {"name": "查看线索", "code": "lead:list", "resource": "lead:list", "menu_type": "button"},
    {"name": "管理线索", "code": "lead:manage", "resource": "lead:manage", "menu_type": "button"},
    {"name": "查看商机", "code": "opportunity:list", "resource": "opportunity:list", "menu_type": "button"},
    {"name": "管理商机", "code": "opportunity:manage", "resource": "opportunity:manage", "menu_type": "button"},
    {"name": "查看报价", "code": "quotation:list", "resource": "quotation:list", "menu_type": "button"},
    {"name": "管理报价", "code": "quotation:manage", "resource": "quotation:manage", "menu_type": "button"},
    {"name": "查看合同", "code": "contract:list", "resource": "contract:list", "menu_type": "button"},
    {"name": "管理合同", "code": "contract:manage", "resource": "contract:manage", "menu_type": "button"},
    # 产品管理
    {"name": "查看产品", "code": "product:list", "resource": "product:list", "menu_type": "button"},
    {"name": "管理产品", "code": "product:manage", "resource": "product:manage", "menu_type": "button"},
    # 营销管理
    {"name": "查看活动", "code": "campaign:list", "resource": "campaign:list", "menu_type": "button"},
    {"name": "管理活动", "code": "campaign:manage", "resource": "campaign:manage", "menu_type": "button"},
    # 客户服务
    {"name": "查看工单", "code": "ticket:list", "resource": "ticket:list", "menu_type": "button"},
    {"name": "管理工单", "code": "ticket:manage", "resource": "ticket:manage", "menu_type": "button"},
    # 报表分析
    {"name": "查看报表", "code": "report:list", "resource": "report:list", "menu_type": "button"},
    {"name": "导出报表", "code": "report:export", "resource": "report:export", "menu_type": "button"},
    # 用户管理
    {"name": "查看用户", "code": "user:list", "resource": "user:list", "menu_type": "button"},
    {"name": "管理用户", "code": "user:manage", "resource": "user:manage", "menu_type": "button"},
    {"name": "管理角色", "code": "role:manage", "resource": "role:manage", "menu_type": "button"},
    # 系统设置
    {"name": "系统配置", "code": "system:config", "resource": "system:config", "menu_type": "button"},
    {"name": "查看日志", "code": "system:log", "resource": "system:log", "menu_type": "button"},
]

# ── 默认角色 ─────────────────────────────────────
DEFAULT_ROLES = [
    {
        "name": "超级管理员",
        "code": "super_admin",
        "description": "拥有系统所有权限",
        "sort": 1,
    },
    {
        "name": "销售经理",
        "code": "sales_manager",
        "description": "管理部门销售、查看报表",
        "sort": 2,
    },
    {
        "name": "销售员",
        "code": "salesperson",
        "description": "管理自己的客户和销售流程",
        "sort": 3,
    },
    {
        "name": "客服专员",
        "code": "support_agent",
        "description": "处理工单和客户服务",
        "sort": 4,
    },
    {
        "name": "只读用户",
        "code": "viewer",
        "description": "只能查看数据，不可编辑",
        "sort": 5,
    },
]

# ── 角色权限映射 ────────────────────────────────
ROLE_PERMISSION_MAP = {
    "super_admin": [
        "customer:list", "customer:create", "customer:update", "customer:delete", "customer:export",
        "lead:list", "lead:manage", "opportunity:list", "opportunity:manage",
        "quotation:list", "quotation:manage", "contract:list", "contract:manage",
        "product:list", "product:manage",
        "campaign:list", "campaign:manage",
        "ticket:list", "ticket:manage",
        "report:list", "report:export",
        "user:list", "user:manage", "role:manage",
        "system:config", "system:log",
    ],
    "sales_manager": [
        "customer:list", "customer:create", "customer:update", "customer:export",
        "lead:list", "lead:manage", "opportunity:list", "opportunity:manage",
        "quotation:list", "quotation:manage", "contract:list", "contract:manage",
        "product:list",
        "report:list", "report:export",
        "user:list",
    ],
    "salesperson": [
        "customer:list", "customer:create", "customer:update",
        "lead:list", "lead:manage",
        "opportunity:list", "opportunity:manage",
        "quotation:list", "quotation:manage",
        "product:list",
    ],
    "support_agent": [
        "customer:list",
        "ticket:list", "ticket:manage",
        "product:list",
    ],
    "viewer": [
        "customer:list", "lead:list", "opportunity:list",
        "quotation:list", "contract:list", "product:list",
        "ticket:list", "report:list", "user:list",
    ],
}


async def init_data(db: AsyncSession):
    """
    初始化基础数据
    仅在首次部署时运行
    """
    # 检查是否已初始化
    result = await db.execute(select(User).limit(1))
    if result.scalar_one_or_none():
        print("✅ 数据已初始化，跳过")
        return

    # 1. 创建默认部门
    dept = Department(
        name="默认部门",
        sort=1,
        description="系统初始化默认部门",
    )
    db.add(dept)
    await db.flush()

    # 2. 创建权限
    perm_map = {}
    for p_data in DEFAULT_PERMISSIONS:
        perm = Permission(**p_data)
        db.add(perm)
        await db.flush()
        perm_map[perm.code] = perm

    # 3. 创建角色并分配权限
    role_map = {}
    for r_data in DEFAULT_ROLES:
        role = Role(**r_data)
        # 分配权限
        perm_codes = ROLE_PERMISSION_MAP.get(role.code, [])
        role.permissions = [perm_map[code] for code in perm_codes if code in perm_map]
        db.add(role)
        await db.flush()
        role_map[role.code] = role

    # 4. 创建超级管理员
    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password=hash_password("admin123"),
        full_name="系统管理员",
        phone="13800138000",
        position="系统管理员",
        department_id=dept.id,
        is_superuser=True,
        is_active=True,
    )
    admin.roles = [role_map["super_admin"]]
    db.add(admin)

    # 5. 创建演示销售员
    demo_sales = User(
        username="sales",
        email="sales@example.com",
        hashed_password=hash_password("sales123"),
        full_name="张三（销售）",
        phone="13900139000",
        position="销售专员",
        department_id=dept.id,
        is_active=True,
    )
    demo_sales.roles = [role_map["salesperson"]]
    db.add(demo_sales)

    await db.flush()
    print("🎉 初始化数据创建完成!")
    print("   管理员: admin / admin123")
    print("   销售员: sales / sales123")


async def main():
    # 1. 先建表
    from app.core.database import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建完成")

    # 2. 再灌初始数据
    async with async_session_factory() as session:
        try:
            await init_data(session)
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"❌ 初始化失败: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
