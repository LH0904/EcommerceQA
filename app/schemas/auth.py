"""
鉴权相关的 Pydantic 模型
"""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "merchant"  # 默认为商家角色
