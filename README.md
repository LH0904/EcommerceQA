# 电商智能问答系统

基于 RAG + NL2SQL 架构的电商智能问答系统。用户通过自然语言提问，系统自动生成 SQL 查询 MySQL 数据库，返回结果并生成 Echarts 数据看板和 PDF 分析报告。

## 系统架构

```
用户提问 → 向量检索(ChromaDB) → LLM生成SQL → MySQL执行 → 返回结果
                                                             ↓
                                                      Echarts可视化 / PDF报告
```

### 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue 3（CDN） | 对话式界面，无需构建工具 |
| 后端 | FastAPI | Python Web 框架 |
| 向量库 | ChromaDB + Qwen text-embedding-v3 | 语义检索 |
| 数据库 | MySQL 8.0 | 5张表，45万+条数据 |
| 大模型 | 小米 MiMo mimo-v2.5 | SQL生成 + 看板/报告生成 |
| 可视化 | Echarts | 数据看板 |
| PDF | Playwright + Chrome | 报告导出 |

## 环境要求

- **Python** 3.8+
- **MySQL** 8.0
- **Chrome** 浏览器（Playwright PDF导出需要）

## 部署步骤

### 1. 克隆项目

```bash
# 进入项目目录（整个 EcommerceQA 文件夹发给组员即可）
cd EcommerceQA
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

需要安装的包：
```
mysql-connector-python
openai
chromadb
dashscope
fastapi
uvicorn
python-multipart
playwright
```

### 3. 安装 Playwright 浏览器

```bash
python -m playwright install chromium
```

如果下载慢或失败，代码已配置为使用系统已安装的 Chrome：
```
C:\Program Files\Google\Chrome\Application\chrome.exe
```

### 4. 配置 API Key

编辑项目根目录的 `.env` 文件：

```bash
# Dashscope API Key（用于 Qwen Embedding 向量检索）
DASHSCOPE_API_KEY=sk-620…4152

# 小米 MiMo API Key（用于 SQL 生成和报告生成）
MIMO_API_KEY=tp-cn0…fo3q
```

> **注意**：如果 API Key 失效，请联系组长获取新 Key。

### 5. 配置 MySQL

确保 MySQL 服务已启动，然后执行：

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE ecommerce_qa DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6. 导入数据

CSV 文件已包含在 `data/` 目录中，直接运行导入脚本：

```bash
python import_data.py
```

**数据文件：**
- `data/user_behavior.csv`（用户行为，10万条）
- `data/goods.csv`（商品信息，32.7万条）
- `data/comments.csv`（用户评论，1.45万条）
- `data/categories.csv`（商品类别，5357条）
- `data/user_profiles.csv`（用户画像，1万条）

### 7. 构建向量库

```bash
python nl2sql/add_vec.py
```

预计耗时 20-30 秒，会在 `nl2sql/chroma_db/` 目录生成向量数据库。

### 8. 启动服务

**启动后端 API（端口 35052）：**

```bash
cd EcommerceQA
python new_app.py
```

看到 `Uvicorn running on http://0.0.0.0:35052` 表示启动成功。

**启动前端静态服务（端口 35080）：**

```bash
cd EcommerceQA/frontend
python -m http.server 35080
```

### 9. 访问系统

打开浏览器访问：**http://localhost:35080**

## 测试验证

### API 测试

```bash
# 查询测试
curl -X POST http://localhost:35052/query -d "user_question=统计各行为类型的数量分布"

# 健康检查
curl http://localhost:35052/health
```

### 推荐测试问题

| 问题 | 预期SQL关键词 |
|------|--------------|
| 统计各行为类型的数量分布 | `GROUP BY behavior_type` |
| 最受欢迎的前10个商品类别 | `JOIN goods ... LIMIT 10` |
| 各城市的购买转化率 | `GROUP BY city` |
| 各职业用户的平均消费金额 | `JOIN user_profiles` |
| 每天的购买量趋势 | `DATE_FORMAT(timestamp)` |
| 男女用户比例 | `GROUP BY gender` |

## 项目结构

```
EcommerceQA/
├── .env                    # API Keys（已配置好）
├── new_app.py              # FastAPI 主服务（端口 35052）
├── app.py                  # Streamlit 备用前端
├── requirements.txt        # Python 依赖
├── test.py                 # 测试脚本
├── README.md               # 本文档
├── frontend/
│   └── index.html          # Vue 3 前端（端口 35080）
└── nl2sql/
    ├── vec.py              # 向量库管理
    ├── add_vec.py          # 构建向量库
    ├── del_vec.py          # 清理向量库
    ├── mysqlQuery.py       # MySQL 查询
    ├── data/
    │   ├── DDL.py          # 表结构定义
    │   ├── DOC.py          # 数据字典
    │   └── QA.py           # 问答对
    └── chroma_db/          # 向量数据库（已构建）
```

## 常见问题

### Q: Playwright 报错 "Executable doesn't exist"
A: 运行 `python -m playwright install chromium`，或确保系统已安装 Chrome。

### Q: Dashscope API 报错 "latin-1 codec"
A: 检查 `.env` 中的 API Key 是否包含特殊字符（如 `…` 省略号），确保是完整的 `sk-` 开头的密钥。

### Q: MySQL 连接失败
A: 检查 MySQL 服务是否启动，`mysqlQuery.py` 中的连接参数（host/port/user/password）是否正确。

### Q: 向量检索结果不准确
A: 重新运行 `python nl2sql/add_vec.py` 构建向量库。

### Q: MiMo 返回空内容
A: 确保使用 `stream=True` 模式调用，MiMo 的 reasoning tokens 会占满 max_tokens。

---

*电商智能问答系统 · 计算机科学与技术专业综合实践*
