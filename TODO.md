# 鉴权功能开发 TodoList

## 目标
新增简单鉴权系统，区分 **管理员(admin)** 和 **商家(merchant)** 两种角色。

## 设计方案
- 使用 JWT (JSON Web Token) 进行身份验证
- 使用 bcrypt 进行密码哈希
- 用户表存储在 MySQL 中
- 前端增加登录页面

## 角色权限
| 功能 | admin | merchant |
|------|-------|----------|
| 数据查询 | ✅ | ✅ |
| 生成报告 | ✅ | ✅ |
| 查看历史 | ✅ | ✅ |
| 下载文件 | ✅ | ✅ |
| 用户管理 | ✅ | ❌ |

## TodoList

- [x] Step 1: 添加依赖 (pyjwt, passlib[bcrypt]) 到 requirements.txt
- [x] Step 2: 创建 users 用户表（建表SQL + 初始化脚本）
- [x] Step 3: 创建鉴权模块 auth.py（JWT工具、密码哈希、依赖注入）
- [x] Step 4: 后端添加登录/注册 API 端点
- [x] Step 5: 后端添加用户管理 API（仅admin可用）
- [x] Step 6: 为现有API添加JWT认证保护
- [x] Step 7: 前端添加登录页面和Token管理
- [x] Step 8: 前端根据角色显示/隐藏管理功能

## 完成总结

### 新增文件
- `auth.py` — 鉴权模块（JWT/密码哈希/用户表/依赖注入）

### 修改文件
- `requirements.txt` — 新增 PyJWT, passlib, python-multipart
- `new_app.py` — 新增登录/注册/用户管理API，现有API加JWT保护
- `frontend/index.html` — 新增登录页面、Token管理、角色区分UI

### 默认账号
| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 商家 | merchant | merchant123 |

### API 端点
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | /auth/login | 用户登录 | 公开 |
| POST | /auth/register | 用户注册 | 公开 |
| GET | /auth/me | 获取当前用户 | 需登录 |
| GET | /auth/users | 用户列表 | 仅admin |
| DELETE | /auth/users/{id} | 删除用户 | 仅admin |
| GET/POST | /query, /presets, /history, /report, /download | 原有功能 | 需登录 |
