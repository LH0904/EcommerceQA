# 电商智能问答系统

基于 RAG + NL2SQL 架构的电商智能问答系统。用户通过自然语言提问，系统自动从向量知识库检索匹配的 SQL 模板或调用大语言模型生成 SQL，在 MySQL 中执行查询后返回结构化结果，并生成 Echarts 数据看板和 PDF 分析报告。

## 系统架构

```
用户提问 → 缓存检查 → 向量检索(ChromaDB) → LLM生成SQL(MiMo) → MySQL执行 → 返回结果
                                                                        ↓
                                                            Echarts可视化看板 / PDF报告
```

后端采用四层分层架构：

```
routers（路由层）→ services（业务层）→ data（数据层）→ utils（工具层）
```

### 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue 3（CDN） | 对话式交互界面，单文件 SPA |
| 后端 | FastAPI | Python Web 框架，异步 API 服务 |
| 向量库 | ChromaDB + Qwen text-embedding-v3 | 语义相似度检索 |
| 数据库 | MySQL 8.0 | 5 张业务表 + 2 张系统表，45 万+条数据 |
| 大模型 | 小米 MiMo mimo-v2.5 | SQL 生成 + 看板/报告生成 |
| 可视化 | ECharts | 数据看板（KPI 卡片 + 多种图表） |
| 认证 | JWT + bcrypt | 管理员 / 商家角色权限 |
| PDF | Playwright + Chrome | 报告导出 |
| 缓存 | 内存字典 + MD5 归一化 | LRU 查询缓存加速 |

## 环境要求

- **Python** 3.10+
- **MySQL** 8.0
- **Chrome** 浏览器（Playwright PDF 导出需要）

## 部署步骤

### 1. 克隆项目

```bash
git clone https://github.com/LH0904/EcommerceQA.git
cd EcommerceQA
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 安装 Playwright 浏览器

```bash
python -m playwright install chromium
```

如果下载慢或失败，系统会自动回退到已安装的 Chrome 浏览器。

### 4. 配置 API Key

在项目根目录创建 `.env` 文件：

```env
# DashScope API Key（Qwen text-embedding-v3 向量检索）
DASHSCOPE_API_KEY=your_dashscope_key

# 小米 MiMo API Key（SQL 生成 + 看板/报告生成）
MIMO_API_KEY=your_mimo_key
```

> 如需获取 API Key，请联系项目组长。

### 5. 配置 MySQL

确保 MySQL 服务已启动：

```sql
CREATE DATABASE ecommerce_qa DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

数据库连接参数可在 `.env` 中配置：

```env
DB_USER=root
DB_PASSWORD=123456
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ecommerce_qa
```

### 6. 导入数据

```bash
python scripts/import_data.py
```

**数据文件（位于 `data/` 目录）：**

| 文件 | 内容 | 数据量 |
|------|------|--------|
| `user_behavior.csv` | 用户行为（浏览/收藏/加购/购买） | 10 万条 |
| `goods.csv` | 商品信息 | 32.7 万条 |
| `comments.csv` | 用户评论 | 1.45 万条 |
| `categories.csv` | 商品类别 | 5357 条 |
| `user_profiles.csv` | 用户画像（职业） | 1 万条 |

### 7. 构建向量知识库

```bash
python nl2sql/add_vec.py
```

约 20-30 秒，在 `nl2sql/chroma_db/` 生成向量数据库（含 DDL 表结构、数据字典、30 对 QA 问答对）。

### 8. 启动服务

```bash
# 启动后端（端口 35052）
python new_app.py

# 另开终端，启动前端（端口 35080）
cd frontend && python -m http.server 35080
```

### 9. 访问系统

打开浏览器访问 **http://localhost:35080**

默认账号：`admin / admin123`（管理员）或 `merchant / merchant123`（商家），也可在登录页自助注册商家账号。

## 项目结构

```
EcommerceQA/
├── app/                          # 后端四层架构
│   ├── main.py                   # FastAPI 应用入口 + CORS + 生命周期
│   ├── config.py                 # Pydantic Settings 统一配置
│   ├── routers/                  # 路由层（HTTP 接口）
│   │   ├── auth.py               #   登录 / 注册 / 用户管理
│   │   ├── query.py              #   NL2SQL 查询 / 报告生成
│   │   ├── preset.py             #   预设问题模板
│   │   └── history.py            #   查询历史 / 文件下载
│   ├── services/                 # 业务层（核心逻辑）
│   │   ├── nl2sql.py             #   NL2SQL 引擎（向量检索 + LLM 生成）
│   │   ├── llm.py                #   MiMo 大模型调用
│   │   ├── query_service.py      #   查询编排（缓存→SQL→执行→看板→保存）
│   │   └── file_export.py        #   HTML/PDF 报告导出
│   ├── data/                     # 数据层（DB 访问）
│   │   ├── db.py                 #   MySQL 统一连接
│   │   ├── vector_db.py          #   ChromaDB 向量库管理
│   │   ├── user_repo.py          #   用户表 CRUD
│   │   └── history_repo.py       #   查询历史 CRUD
│   ├── schemas/                  # Pydantic 请求/响应模型
│   │   ├── auth.py               #   登录/注册请求体
│   │   └── query.py              #   查询/报告响应体
│   └── utils/                    # 工具层
│       ├── security.py           #   JWT + bcrypt 认证
│       ├── cache.py              #   查询缓存（MD5 归一化 + FIFO）
│       └── presets.py            #   预设问题（4 类 20 个）
├── nl2sql/                       # NL2SQL 知识库
│   ├── add_vec.py                #   构建向量库
│   ├── del_vec.py                #   清理向量库
│   ├── vec.py                    #   向量库兼容接口
│   ├── mysqlQuery.py             #   MySQL 查询兼容接口
│   └── data/                     #   知识库原始数据
│       ├── DDL.py                #     表结构定义（5 张表）
│       ├── DOC.py                #     数据字典描述
│       └── QA.py                 #     问答对（30 对）
├── frontend/
│   └── index.html                # Vue 3 前端（单文件 SPA）
├── scripts/
│   └── import_data.py            # CSV 数据导入脚本
├── tests/
│   ├── test_api.py               # API 接口自动化测试
│   ├── demo.py                   # 答辩演示脚本
│   └── conftest.py               # 测试辅助工具
├── data/                         # CSV 原始数据（45 万+条）
├── new_app.py                    # 兼容入口（→ app.main）
├── auth.py                       # 兼容接口（→ app.utils.security）
├── requirements.txt              # Python 依赖
└── .env                          # 配置文件（不入库）
```

## API 接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/auth/login` | 用户登录 | - |
| POST | `/auth/register` | 商家注册 | - |
| GET | `/auth/me` | 当前用户信息 | JWT |
| GET | `/auth/users` | 用户列表 | Admin |
| DELETE | `/auth/users/{id}` | 删除用户 | Admin |
| POST | `/query` | NL2SQL 查询 | JWT |
| POST | `/report` | 生成 PDF 报告 | JWT |
| GET | `/presets` | 预设问题列表 | JWT |
| GET | `/history` | 查询历史 | JWT |
| GET | `/download` | 下载看板文件 | JWT |

## 常见问题

**Q: MySQL 启动报 `Integer display width is deprecated` 错误？**
A: 这是 MySQL 8.0 的警告，不影响功能。代码已移除 `raise_on_warnings` 参数来避免此问题。

**Q: 向量检索结果不准确？**
A: 重新运行 `python nl2sql/add_vec.py` 构建向量库。确保 `.env` 中的 `DASHSCOPE_API_KEY` 正确。

**Q: Playwright 报错 "Executable doesn't exist"？**
A: 运行 `python -m playwright install chromium`，或确保系统已安装 Chrome 浏览器。

**Q: MiMo 返回空内容？**
A: 确保使用 `stream=True` 模式调用，MiMo 的 reasoning tokens 会占满 max_tokens。

---

*电商智能问答系统 · 计算机科学与技术专业综合实践*
