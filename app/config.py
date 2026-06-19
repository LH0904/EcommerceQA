"""
统一配置管理 - 从 .env 文件和环境变量读取所有配置
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "ecommerce_qa"

    # MiMo LLM
    MIMO_API_KEY: str = ""
    MIMO_BASE_URL: str = "https://token-plan-cn.xiaomimimo.com/v1"
    MIMO_MODEL: str = "mimo-v2.5"

    # DashScope (向量嵌入)
    DASHSCOPE_API_KEY: str = ""

    # JWT
    JWT_SECRET: str = "ecommerce-qa-secret-key-2024"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # 查询缓存
    CACHE_MAX_SIZE: int = 100

    # 路径
    OUTPUT_DIR: str = "output"

    # 服务端口
    SERVER_PORT: int = 35052

    class Config:
        env_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
        )
        env_file_encoding = "utf-8"


settings = Settings()
