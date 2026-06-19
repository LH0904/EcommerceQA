"""
[已废弃] 旧版鉴权模块 - 保留兼容性，实际逻辑已迁移到 app.utils.security 和 app.data.user_repo
"""

# 重新导出所有公共接口，确保旧代码（import_data.py 等）不受影响

from app.config import settings

DB_CONFIG = {
    "user": settings.DB_USER,
    "password": settings.DB_PASSWORD,
    "host": settings.DB_HOST,
    "database": settings.DB_NAME,
    "port": settings.DB_PORT,
}

JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_EXPIRE_HOURS = settings.JWT_EXPIRE_HOURS

from app.utils.security import (  # noqa: F401, E402
    pwd_context,
    security,
    hash_password,
    verify_password,
    create_token,
    decode_token,
    get_current_user,
    require_admin,
)

from app.data.user_repo import (  # noqa: F401, E402
    DEFAULT_ADMIN,
    DEFAULT_MERCHANT,
    CREATE_USERS_TABLE,
    init_users_table,
    find_user_by_username,
    create_user,
    list_users,
    find_user_by_id,
    delete_user,
)

from app.data.db import get_connection  # noqa: F401, E402


def get_db():
    """[兼容] 获取数据库连接"""
    return get_connection()


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    init_users_table()
