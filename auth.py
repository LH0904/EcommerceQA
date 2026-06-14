"""
鉴权模块 - JWT 认证与角色权限管理
支持两种角色: admin(管理员) / merchant(商家)
"""
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
import mysql.connector
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ==================== 配置 ====================

DB_CONFIG = {
    'user': 'root',
    'password': '123456',
    'host': 'localhost',
    'database': 'ecommerce_qa',
    'port': 3306,
}

JWT_SECRET = os.environ.get('JWT_SECRET', 'ecommerce-qa-secret-key-2024')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRE_HOURS = 24

# 密码哈希
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# Bearer token 提取
security = HTTPBearer(auto_error=False)

# ==================== 建表 SQL ====================

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'merchant') NOT NULL DEFAULT 'merchant',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

DEFAULT_ADMIN = {
    'username': 'admin',
    'password': 'admin123',
    'role': 'admin',
}

DEFAULT_MERCHANT = {
    'username': 'merchant',
    'password': 'merchant123',
    'role': 'merchant',
}


# ==================== 数据库工具 ====================

def get_db():
    """获取数据库连接"""
    return mysql.connector.connect(**DB_CONFIG)


def init_users_table():
    """创建 users 表并插入默认用户"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(CREATE_USERS_TABLE)

        # 插入默认管理员（如不存在）
        cursor.execute("SELECT id FROM users WHERE username = %s", (DEFAULT_ADMIN['username'],))
        if not cursor.fetchone():
            hash_pw = pwd_context.hash(DEFAULT_ADMIN['password'])
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (DEFAULT_ADMIN['username'], hash_pw, DEFAULT_ADMIN['role'])
            )
            logging.info(f"默认管理员已创建: {DEFAULT_ADMIN['username']}")

        # 插入默认商家（如不存在）
        cursor.execute("SELECT id FROM users WHERE username = %s", (DEFAULT_MERCHANT['username'],))
        if not cursor.fetchone():
            hash_pw = pwd_context.hash(DEFAULT_MERCHANT['password'])
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (DEFAULT_MERCHANT['username'], hash_pw, DEFAULT_MERCHANT['role'])
            )
            logging.info(f"默认商家用户已创建: {DEFAULT_MERCHANT['username']}")

        conn.commit()
        cursor.close()
        conn.close()
        logging.info("users 表初始化完成")
    except Exception as e:
        logging.error(f"users 表初始化失败: {e}")


# ==================== 密码工具 ====================

def hash_password(password: str) -> str:
    """对密码进行 bcrypt 哈希"""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain, hashed)


# ==================== JWT 工具 ====================

def create_token(username: str, role: str) -> str:
    """生成 JWT token"""
    payload = {
        'sub': username,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """解码并验证 JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的 Token")


# ==================== FastAPI 依赖注入 ====================

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    从请求头提取 JWT token，返回当前用户信息
    用法: current_user: dict = Depends(get_current_user)
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息，请先登录",
        )
    payload = decode_token(credentials.credentials)
    return {
        'username': payload['sub'],
        'role': payload['role'],
    }


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    要求当前用户为管理员角色
    用法: current_user: dict = Depends(require_admin)
    """
    if current_user['role'] != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅管理员可操作",
        )
    return current_user


# ==================== 数据库查询用户 ====================

def find_user_by_username(username: str) -> Optional[dict]:
    """根据用户名查找用户"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, password_hash, role, created_at FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    except Exception as e:
        logging.error(f"查询用户失败: {e}")
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_users_table()
