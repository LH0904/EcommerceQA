"""
鉴权路由 - 登录、注册、用户管理
"""
import logging

import fastapi
from fastapi import Depends

from app.schemas.auth import LoginRequest, RegisterRequest
from app.utils.security import (
    get_current_user,
    require_admin,
    verify_password,
    create_token,
    hash_password,
)
from app.data.user_repo import (
    find_user_by_username,
    create_user,
    list_users,
    find_user_by_id,
    delete_user,
)

logger = logging.getLogger(__name__)

router = fastapi.APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(req: LoginRequest):
    """用户登录，返回 JWT token"""
    user = find_user_by_username(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise fastapi.HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_token(user["username"], user["role"])
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
        },
    }


@router.post("/register")
async def register(req: RegisterRequest):
    """用户注册"""
    if find_user_by_username(req.username):
        raise fastapi.HTTPException(status_code=400, detail="用户名已存在")

    if req.role not in ("admin", "merchant"):
        raise fastapi.HTTPException(status_code=400, detail="角色必须是 admin 或 merchant")

    try:
        hashed = hash_password(req.password)
        create_user(req.username, hashed, req.role)
        return {"message": f"用户 {req.username} 创建成功", "role": req.role}
    except Exception as e:
        logger.error(f"注册失败: {e}")
        raise fastapi.HTTPException(status_code=500, detail="注册失败")


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return {"user": current_user}


@router.get("/users")
async def get_users(current_user: dict = Depends(require_admin)):
    """获取所有用户列表（仅管理员）"""
    try:
        users = list_users()
        return {"users": users}
    except Exception as e:
        logger.error(f"查询用户列表失败: {e}")
        return {"users": []}


@router.delete("/users/{user_id}")
async def remove_user(user_id: int, current_user: dict = Depends(require_admin)):
    """删除用户（仅管理员，不能删除自己）"""
    target = find_user_by_id(user_id)
    if not target:
        raise fastapi.HTTPException(status_code=404, detail="用户不存在")

    if target["username"] == current_user["username"]:
        raise fastapi.HTTPException(status_code=400, detail="不能删除自己")

    try:
        delete_user(user_id)
        return {"message": f"用户 {target['username']} 已删除"}
    except Exception as e:
        logger.error(f"删除用户失败: {e}")
        raise fastapi.HTTPException(status_code=500, detail="删除用户失败")
