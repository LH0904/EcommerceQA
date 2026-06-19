"""
[已废弃] 旧版 MySQL 查询模块 - 保留兼容性，实际逻辑已迁移到 app.data.db
"""

from app.data.db import execute_query as my_sql  # noqa: F401
from app.data.db import execute_write as my_sql_exec  # noqa: F401
