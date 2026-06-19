"""
查询相关的 Pydantic 模型
"""
from pydantic import BaseModel
from typing import Optional


class QueryResponse(BaseModel):
    sql: Optional[str] = None
    result: Optional[list] = None
    board_html: Optional[str] = None
    html_path: Optional[str] = None
    pdf_path: Optional[str] = None
    time: Optional[str] = None
    cached: bool = False
    error: Optional[str] = None


class ReportResponse(BaseModel):
    sql: Optional[str] = None
    result: Optional[list] = None
    report_html: Optional[str] = None
    html_path: Optional[str] = None
    pdf_path: Optional[str] = None
    time: Optional[str] = None
    error: Optional[str] = None
