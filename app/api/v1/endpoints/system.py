"""
系统设置：数据字典、系统配置
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.core.database import get_db
from app.api.deps import get_current_user, pagination_params
from app.models.user import User
from app.models.system import DictType, DictData, SystemConfig
from app.schemas.common import ResponseModel, ResponseList
from app.services.base_crud import BaseCRUD
from pydantic import BaseModel, Field
from typing import Optional, List

router = APIRouter(prefix="/system", tags=["⚙️ 系统设置"])
dict_type_crud = BaseCRUD(DictType)


# ── 数据字典 ─────────────────────────────────────
@router.get("/dict/types", response_model=ResponseModel, summary="字典类型列表")
async def list_dict_types(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DictType).options(joinedload(DictType.items)).order_by(DictType.name))
    types = result.unique().scalars().all()
    data = [{"id": t.id, "name": t.name, "code": t.code, "is_active": t.is_active,
             "items": [{"id": i.id, "label": i.label, "value": i.value, "sort": i.sort, "is_active": i.is_active} for i in t.items]} for t in types]
    return ResponseModel(data=data)


@router.post("/dict/types", response_model=ResponseModel, summary="创建字典类型")
async def create_dict_type(data: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    t = DictType(name=data.get("name", ""), code=data.get("code", ""), description=data.get("description", ""))
    db.add(t); await db.flush(); await db.refresh(t)
    return ResponseModel(data={"id": t.id, "name": t.name}, message="创建成功")


@router.post("/dict/items", response_model=ResponseModel, summary="添加字典项")
async def create_dict_item(data: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = DictData(dict_type_id=int(data["dict_type_id"]), label=data["label"], value=data["value"], sort=data.get("sort", 0))
    db.add(item); await db.flush()
    return ResponseModel(data={"id": item.id}, message="添加成功")


@router.delete("/dict/types/{type_id}", response_model=ResponseModel, summary="删除字典类型")
async def delete_dict_type(type_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DictType).where(DictType.id == type_id))
    t = result.scalar_one_or_none()
    if not t: raise HTTPException(404, "字典类型不存在")
    await db.delete(t); await db.flush()
    return ResponseModel(message="已删除")


@router.delete("/dict/items/{item_id}", response_model=ResponseModel, summary="删除字典项")
async def delete_dict_item(item_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DictData).where(DictData.id == item_id))
    item = result.scalar_one_or_none()
    if not item: raise HTTPException(404, "字典项不存在")
    await db.delete(item); await db.flush()
    return ResponseModel(message="已删除")


# ── 系统配置 ─────────────────────────────────────
@router.get("/config", response_model=ResponseModel, summary="系统配置")
async def list_config(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemConfig).order_by(SystemConfig.key))
    configs = result.scalars().all()
    return ResponseModel(data=[{"id": c.id, "key": c.key, "value": c.value, "value_type": c.value_type, "description": c.description} for c in configs])


@router.put("/config/{config_id}", response_model=ResponseModel, summary="更新配置")
async def update_config(config_id: int, data: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemConfig).where(SystemConfig.id == config_id))
    c = result.scalar_one_or_none()
    if not c: raise HTTPException(404, "配置不存在")
    if "value" in data: c.value = data["value"]
    await db.flush()
    return ResponseModel(message="更新成功")
