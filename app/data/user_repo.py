"""
用户数据访问 - users 表操作
"""
import logging
from typing import Optional

from app.data.db import get_connection

logger = logging.getLogger(__name__)

# 默认账户
DEFAULT_ADMIN = {
    "username": "admin",
    "password": "admin123",
    "role": "admin",
}

DEFAULT_MERCHANT = {
    "username": "merchant",
    "password": "merchant123",
    "role": "merchant",
}

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'merchant') NOT NULL DEFAULT 'merchant',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def init_users_table():
    """创建 users 表并插入默认用户"""
    from app.utils.security import hash_password

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(CREATE_USERS_TABLE)

        # 插入默认管理员（如不存在）
        cursor.execute("SELECT id FROM users WHERE username = %s", (DEFAULT_ADMIN["username"],))
        if not cursor.fetchone():
            hash_pw = hash_password(DEFAULT_ADMIN["password"])
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (DEFAULT_ADMIN["username"], hash_pw, DEFAULT_ADMIN["role"]),
            )
            logger.info(f"默认管理员已创建: {DEFAULT_ADMIN['username']}")

        # 插入默认商家（如不存在）
        cursor.execute("SELECT id FROM users WHERE username = %s", (DEFAULT_MERCHANT["username"],))
        if not cursor.fetchone():
            hash_pw = hash_password(DEFAULT_MERCHANT["password"])
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (DEFAULT_MERCHANT["username"], hash_pw, DEFAULT_MERCHANT["role"]),
            )
            logger.info(f"默认商家用户已创建: {DEFAULT_MERCHANT['username']}")

        conn.commit()
        cursor.close()
        conn.close()
        logger.info("users 表初始化完成")
    except Exception as e:
        logger.error(f"users 表初始化失败: {e}")


def find_user_by_username(username: str) -> Optional[dict]:
    """根据用户名查找用户"""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, password_hash, role, created_at FROM users WHERE username = %s",
            (username,),
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    except Exception as e:
        logger.error(f"查询用户失败: {e}")
        return None


def create_user(username: str, password_hash: str, role: str) -> dict:
    """创建新用户"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
        (username, password_hash, role),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"username": username, "role": role}


def list_users() -> list:
    """查询所有用户"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, role, created_at FROM users ORDER BY id")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    for u in users:
        if u.get("created_at"):
            u["created_at"] = u["created_at"].isoformat()
    return users


def find_user_by_id(user_id: int) -> Optional[dict]:
    """根据 ID 查找用户"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, role FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


def delete_user(user_id: int) -> None:
    """删除用户"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
