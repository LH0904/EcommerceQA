"""
[已废弃] 旧版入口 - 保留兼容性，实际逻辑已迁移到 app.main
启动方式不变: uvicorn new_app:app --host 0.0.0.0 --port 35052
"""
import uvicorn

from app.main import app  # noqa: F401 — 重新导出 FastAPI 实例

if __name__ == "__main__":
    from app.config import settings

    uvicorn.run(app, host="0.0.0.0", port=settings.SERVER_PORT)
