"""
七牛云文件上传工具
支持本地存储 & 七牛云双向切换
"""
import uuid
from pathlib import Path
from typing import Optional
from app.core.config import settings


async def upload_file(
    file_content: bytes,
    filename: str,
    folder: str = "crm",
) -> str:
    """
    统一文件上传接口

    - 如果 QINIU_ENABLED=true，上传到七牛云
    - 否则存储到本地 UPLOAD_DIR
    - return: 文件访问 URL
    """
    ext = Path(filename).suffix.lower()
    unique_name = f"{folder}/{uuid.uuid4().hex}{ext}"

    if settings.QINIU_ENABLED and settings.QINIU_ACCESS_KEY:
        return await _upload_to_qiniu(file_content, unique_name)
    else:
        return await _upload_to_local(file_content, unique_name)


async def _upload_to_local(file_content: bytes, object_name: str) -> str:
    """存储到本地文件系统"""
    upload_dir = Path(settings.UPLOAD_DIR)
    file_path = upload_dir / object_name
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(file_content)

    return f"/uploads/{object_name}"


async def _upload_to_qiniu(file_content: bytes, object_name: str) -> str:
    """上传到七牛云"""
    from qiniu import Auth, put_data

    # 构建鉴权对象
    q = Auth(settings.QINIU_ACCESS_KEY, settings.QINIU_SECRET_KEY)

    # 上传策略
    token = q.upload_token(settings.QINIU_BUCKET_NAME, object_name, 3600)

    # 上传文件
    ret, info = put_data(token, object_name, file_content)

    if info.status_code != 200:
        raise Exception(f"七牛云上传失败: {info.text_body}")

    if settings.QINIU_DOMAIN:
        return f"{settings.QINIU_DOMAIN.rstrip('/')}/{object_name}"
    return object_name


async def delete_file(file_url: str) -> bool:
    """
    删除文件
    - 本地文件直接删除
    - 七牛云文件需要调用删除 API（需要 bucket 操作权限）
    """
    if not file_url:
        return False

    if file_url.startswith("/uploads/"):
        file_path = Path(file_url.lstrip("/"))
        if file_path.exists():
            file_path.unlink()
            return True
    elif settings.QINIU_ENABLED and settings.QINIU_DOMAIN in file_url:
        # 七牛云删除（需额外权限，这里仅做标记）
        from qiniu import Auth, BucketManager
        q = Auth(settings.QINIU_ACCESS_KEY, settings.QINIU_SECRET_KEY)
        bucket = BucketManager(q)
        object_name = file_url.replace(settings.QINIU_DOMAIN.rstrip("/") + "/", "")
        ret, info = bucket.delete(settings.QINIU_BUCKET_NAME, object_name)
        return info.status_code == 200

    return False
