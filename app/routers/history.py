"""
查询历史与文件下载路由
"""
import os
import logging

import fastapi
from fastapi import Depends
from fastapi.responses import FileResponse

from app.utils.security import get_current_user
from app.data.history_repo import get_recent
from app.services.file_export import file_exists, get_filename

logger = logging.getLogger(__name__)

router = fastapi.APIRouter(tags=["history"])


@router.get("/history")
async def get_history(limit: int = 20, current_user: dict = Depends(get_current_user)):
    """获取最近的查询历史"""
    rows = get_recent(limit)
    return {"history": rows}


@router.get("/download")
async def download_file(path: str, current_user: dict = Depends(get_current_user)):
    """下载生成的文件（HTML/PDF）"""
    if file_exists(path):
        filename = get_filename(path)
        return FileResponse(path, filename=filename, media_type="application/octet-stream")
    return {"error": "File not found"}
