"""
查询路由 - NL2SQL 查询与报告生成
"""
import json
import logging

import fastapi
from fastapi.params import Form
from fastapi import Depends

from app.utils.security import get_current_user

logger = logging.getLogger(__name__)

router = fastapi.APIRouter(tags=["query"])


@router.post("/query")
async def query(
    user_question: str = Form(...),
    context: str = Form(default="[]"),
    current_user: dict = Depends(get_current_user),
):
    """自然语言提问 → SQL + 数据看板"""
    from app.main import get_query_service

    # 解析对话上下文
    try:
        conversation = json.loads(context)
    except (json.JSONDecodeError, TypeError):
        conversation = []

    query_service = get_query_service()
    return await query_service.execute_query(user_question, conversation)


@router.post("/report")
async def report(
    user_question: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    """生成详细分析报告"""
    from app.main import get_query_service

    query_service = get_query_service()
    return await query_service.generate_report(user_question)
