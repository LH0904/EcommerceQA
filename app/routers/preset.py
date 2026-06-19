"""
预设问题路由
"""
import fastapi
from fastapi import Depends

from app.utils.security import get_current_user
from app.utils.presets import PRESET_QUESTIONS

router = fastapi.APIRouter(tags=["presets"])


@router.get("/presets")
async def get_presets(current_user: dict = Depends(get_current_user)):
    """返回预设问题模板"""
    return {"presets": PRESET_QUESTIONS}
