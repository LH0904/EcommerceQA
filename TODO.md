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

- [ ] Step 1: 添加依赖 (pyjwt, passlib[bcrypt]) 到 requirements.txt
- [ ] Step 2: 创建 users 用户表（建表SQL + 初始化脚本）
- [ ] Step 3: 创建鉴权模块 auth.py（JWT工具、密码哈希、依赖注入）
- [ ] Step 4: 后端添加登录/注册 API 端点
- [ ] Step 5: 后端添加用户管理 API（仅admin可用）
- [ ] Step 6: 为现有API添加JWT认证保护
- [ ] Step 7: 前端添加登录页面和Token管理
- [ ] Step 8: 前端根据角色显示/隐藏管理功能
