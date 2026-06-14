"""
鉴权模块 - 用户表初始化
"""
import mysql.connector
import logging

DB_CONFIG = {
    'user': 'root',
    'password': '123456',
    'host': 'localhost',
    'database': 'ecommerce_qa',
    'port': 3306,
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
    """创建 users 表"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(CREATE_USERS_TABLE)
        conn.commit()
        cursor.close()
        conn.close()
        logging.info("users 表初始化成功")
    except Exception as e:
        logging.error(f"users 表初始化失败: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_users_table()
