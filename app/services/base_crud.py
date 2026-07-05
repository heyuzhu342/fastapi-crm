"""
通用 CRUD 服务基类
"""
import math
from typing import Any, Generic, Optional, Type, TypeVar
from sqlalchemy import func, select, delete, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseCRUD(Generic[ModelType]):
    """通用 CRUD 操作"""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        """根据主键获取单个记录"""
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        order: str = "desc",
        search: Optional[str] = None,
        search_fields: Optional[list[str]] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> dict:
        """
        通用分页查询
        - search: 模糊搜索关键词
        - search_fields: 需要模糊搜索的字段列表
        - filters: 精确过滤条件 {field: value}
        - return: {items, total, page, page_size, total_pages}
        """
        query = select(self.model)
        count_query = select(func.count(self.model.id))

        # 软删除模型自动过滤
        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted == False)
            count_query = count_query.where(self.model.is_deleted == False)

        # 精确过滤
        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    column = getattr(self.model, field)
                    if isinstance(value, list):
                        query = query.where(column.in_(value))
                        count_query = count_query.where(column.in_(value))
                    else:
                        query = query.where(column == value)
                        count_query = count_query.where(column == value)

        # 模糊搜索
        if search and search_fields:
            search_filters = []
            for field in search_fields:
                if hasattr(self.model, field):
                    search_filters.append(
                        getattr(self.model, field).like(f"%{search}%")
                    )
            if search_filters:
                search_clause = search_filters[0]
                for f in search_filters[1:]:
                    search_clause = search_clause | f  # 直接使用 | (SQLAlchemy or_)
                query = query.where(search_clause)
                count_query = count_query.where(search_clause)

        # 统计总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 排序
        sort_column = getattr(self.model, sort_by, self.model.created_at)
        if order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        items = list(result.scalars().all())

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        }

    async def create(self, db: AsyncSession, data: dict) -> ModelType:
        """创建记录"""
        obj = self.model(**data)
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def update(self, db: AsyncSession, id: int, data: dict) -> Optional[ModelType]:
        """更新记录"""
        obj = await self.get_by_id(db, id)
        if obj is None:
            return None
        for key, value in data.items():
            if value is not None and hasattr(obj, key):
                setattr(obj, key, value)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def soft_delete(self, db: AsyncSession, id: int) -> bool:
        """软删除"""
        from datetime import datetime
        obj = await self.get_by_id(db, id)
        if obj is None:
            return False
        if hasattr(obj, "is_deleted"):
            obj.is_deleted = True
            obj.deleted_at = datetime.utcnow()
        else:
            await db.delete(obj)
        await db.flush()
        return True

    async def hard_delete(self, db: AsyncSession, id: int) -> bool:
        """硬删除"""
        obj = await self.get_by_id(db, id)
        if obj is None:
            return False
        await db.delete(obj)
        await db.flush()
        return True

    async def batch_delete(self, db: AsyncSession, ids: list[int]) -> int:
        """批量软删除"""
        from datetime import datetime
        stmt = (
            update(self.model)
            .where(self.model.id.in_(ids))
            .values(is_deleted=True, deleted_at=datetime.utcnow())
        ) if hasattr(self.model, "is_deleted") else delete(self.model).where(self.model.id.in_(ids))
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount
