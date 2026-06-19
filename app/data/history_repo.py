"""
查询历史数据访问 - query_history 表操作
"""
import json
import logging

from app.data.db import get_connection, execute_write

logger = logging.getLogger(__name__)

CREATE_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS query_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question TEXT NOT NULL,
    sql_query TEXT,
    result_json TEXT,
    time_cost VARCHAR(32),
    category VARCHAR(64) DEFAULT '自定义',
    cached TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def init_history_table():
    """创建查询历史表（如不存在）"""
    try:
        execute_write(CREATE_HISTORY_TABLE)
        logger.info("query_history 表已就绪")
    except Exception as e:
        logger.error(f"query_history 表创建失败: {e}")


def save(question, sql_query, result, time_cost, category="自定义", cached=False):
    """保存一条查询记录"""
    try:
        result_str = json.dumps(result, ensure_ascii=False, default=str) if result else None
        sql = """
        INSERT INTO query_history (question, sql_query, result_json, time_cost, category, cached)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        execute_write(sql, (question, sql_query, result_str, time_cost, category, 1 if cached else 0))
    except Exception as e:
        logger.error(f"保存查询历史失败: {e}")


def get_recent(limit=20) -> list:
    """获取最近的查询历史"""
    sql = """
    SELECT id, question, sql_query, time_cost, category, cached, created_at
    FROM query_history
    ORDER BY created_at DESC
    LIMIT %s
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, (limit,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        for row in rows:
            if "created_at" in row and row["created_at"]:
                row["created_at"] = row["created_at"].isoformat()
            if "cached" in row:
                row["cached"] = bool(row["cached"])
        return rows
    except Exception as e:
        logger.error(f"获取查询历史失败: {e}")
        return []
