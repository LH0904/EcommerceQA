"""
FastAPI 应用入口 - 实例创建、生命周期管理、中间件配置
"""
import os
import ssl
import logging
from contextlib import asynccontextmanager

import certifi
import fastapi
from fastapi.middleware.cors import CORSMiddleware

# Windows SSL 证书修复
os.environ["SSL_CERT_FILE"] = certifi.where()
_original_create_default_context = ssl.create_default_context


def _patched_create_default_context(*args, **kwargs):
    kwargs.setdefault("cafile", certifi.where())
    return _original_create_default_context(*args, **kwargs)


ssl.create_default_context = _patched_create_default_context

from app.data.user_repo import init_users_table
from app.data.history_repo import init_history_table
from app.data.vector_db import VectorDBManager
from app.services.nl2sql import NL2SQLService
from app.services.query_service import QueryService
from app.utils.cache import QueryCache

# ==================== 日志 ====================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== 服务实例（延迟初始化） ====================

_vector_db: VectorDBManager | None = None
_query_service: QueryService | None = None


def get_vector_db() -> VectorDBManager:
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorDBManager()
    return _vector_db


def get_query_service() -> QueryService:
    global _query_service
    if _query_service is None:
        vector_db = get_vector_db()
        nl2sql = NL2SQLService(vector_db)
        cache = QueryCache()
        _query_service = QueryService(nl2sql, cache)
    return _query_service


# ==================== 生命周期 ====================


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    """应用启动/关闭时的初始化与清理"""
    init_history_table()
    init_users_table()
    logger.info("数据库表初始化完成")
    yield


# ==================== 应用实例 ====================

app = fastapi.FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 注册路由 ====================

from app.routers import auth, query, preset, history  # noqa: E402

app.include_router(auth.router)
app.include_router(query.router)
app.include_router(preset.router)
app.include_router(history.router)


# ==================== 基础端点 ====================


@app.get("/")
async def root():
    return {"message": "E-commerce QA System API", "version": "2.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
