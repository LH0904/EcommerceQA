"""
统一数据库连接 - 消除多处硬编码的 MySQL 配置
"""
import logging
import mysql.connector
from app.config import settings

logger = logging.getLogger(__name__)


def get_connection():
    """获取 MySQL 数据库连接"""
    return mysql.connector.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
    )


def execute_query(sql, params=None):
    """
    执行 SELECT 查询，返回字典列表
    等价于原 my_sql()
    """
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        result = cursor.fetchall()
        return result
    except mysql.connector.Error as err:
        logger.error(f"SQL 查询失败: {err}")
        return None
    finally:
        cursor.close()
        connection.close()


def execute_write(sql, params=None):
    """
    执行 INSERT/UPDATE/DDL 语句，提交并返回 lastrowid
    等价于原 my_sql_exec()
    """
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params or ())
        connection.commit()
        return cursor.lastrowid
    except mysql.connector.Error as err:
        logger.error(f"SQL 执行失败: {err}")
        connection.rollback()
        return None
    finally:
        cursor.close()
        connection.close()
