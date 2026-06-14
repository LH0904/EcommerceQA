import os
import ssl
import certifi
# 修复 Windows SSL 证书加载问题
os.environ['SSL_CERT_FILE'] = certifi.where()
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

import json
import hashlib
from datetime import datetime
from contextlib import asynccontextmanager
import fastapi
from fastapi.params import Form
from fastapi import Response, Depends
from playwright.async_api import async_playwright
from nl2sql.mysqlQuery import my_sql, my_sql_exec
from fastapi.responses import FileResponse
import time
import logging
import uvicorn
from nl2sql.vec import VectorDBManager
from openai import OpenAI
from pydantic import BaseModel

from fastapi.middleware.cors import CORSMiddleware
from auth import (
    init_users_table, create_token, find_user_by_username,
    hash_password, verify_password, get_current_user, require_admin,
)

# ==================== 配置 ====================

def load_env():
    """Load .env file"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    if k.strip() not in os.environ:
                        os.environ[k.strip()] = v.strip()

load_env()


@asynccontextmanager
async def lifespan(app):
    """应用启动/关闭生命周期管理"""
    create_history_table()
    init_users_table()
    logging.info("Database tables initialized")
    yield

app = fastapi.FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logging.basicConfig(level=logging.INFO)

# MiMo API
MIMO_API_KEY = os.environ.get('MIMO_API_KEY', '')
MIMO_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"
MIMO_MODEL = "mimo-v2.5"
mimo_client = OpenAI(api_key=MIMO_API_KEY, base_url=MIMO_BASE_URL)

db = VectorDBManager()

# ==================== 查询缓存 ====================

query_cache = {}
CACHE_MAX_SIZE = 100


def get_cache_key(question):
    """Generate normalized cache key"""
    normalized = question.strip().lower().replace('？', '?').replace('，', ',')
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()


# ==================== 预设问题 ====================

PRESET_QUESTIONS = {
    "用户分析": [
        "男女用户比例是多少",
        "各城市的用户数量分布",
        "各职业用户的平均消费金额",
        "用户活跃度排行前10",
        "各年龄段用户数量统计",
    ],
    "商品分析": [
        "最受欢迎的前10个商品类别",
        "各行为类型的数量分布",
        "销量最高的前10个商品",
        "收藏量最高的商品",
        "各价格区间的商品数量",
    ],
    "销售趋势": [
        "每天的购买量趋势",
        "每周的浏览量变化",
        "各城市的购买转化率",
        "购买金额最高的前10个城市",
        "各行为类型的转化率分析",
    ],
    "综合分析": [
        "用户购买行为漏斗分析",
        "男女用户购买偏好对比",
        "各城市消费能力排行",
        "商品热度与销量关系分析",
        "用户类型分布统计",
    ],
}


# ==================== 查询历史 ====================

def create_history_table():
    """Create query_history table if not exists"""
    sql = """
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
    my_sql_exec(sql)


def save_to_history(question, sql_query, result, time_cost, category="自定义", cached=False):
    """Save a query to history table"""
    try:
        result_str = json.dumps(result, ensure_ascii=False, default=str) if result else None
        sql = """
        INSERT INTO query_history (question, sql_query, result_json, time_cost, category, cached)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        my_sql_exec(sql, (question, sql_query, result_str, time_cost, category, 1 if cached else 0))
    except Exception as e:
        logging.error(f"Failed to save history: {e}")


def get_category(question):
    """Determine preset category for a question"""
    for cat, questions in PRESET_QUESTIONS.items():
        if question in questions:
            return cat
    return "自定义"


# ==================== LLM 调用 ====================

def call_mimo(messages, temperature=0.7):
    """Call Xiaomi MiMo API"""
    try:
        response = mimo_client.chat.completions.create(
            model=MIMO_MODEL,
            messages=messages,
            temperature=temperature,
            stream=True
        )
        content = ''
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content += chunk.choices[0].delta.content
        return content if content else None
    except Exception as e:
        logging.error(f"MiMo API error: {e}")
        return None


def generate_sql_with_context(question, conversation):
    """Generate SQL using LLM based on conversation context (multi-turn)"""
    # Get database schema from DDL collection
    ddl_list = db.query_all_ddl()
    schema_str = "\n".join(ddl_list)

    # Build conversation context string
    ctx_lines = []
    for i, item in enumerate(conversation[-3:], 1):  # last 3 turns
        ctx_lines.append(f"{i}. 问题: {item['question']}\n   SQL: {item['sql']}")
    context_str = "\n".join(ctx_lines)

    prompt = f"""你是一个SQL专家。根据用户的对话历史和当前问题，生成MySQL查询SQL。

数据库表结构：
{schema_str}

对话历史：
{context_str}

当前问题：{question}

规则：
1. 直接返回SQL语句，不要包含任何解释、注释或markdown格式
2. SQL必须是合法的MySQL语法，只能查询上述数据库中的表
3. 根据对话历史理解上下文，例如"那上个月呢"指的是对话中上次查询的上一个月
4. 时间字段使用 datetime 或 date 字段，timestamp 是Unix时间戳
5. behavior_type 字段值为：pv(浏览)/buy(购买)/cart(加购)/fav(收藏)

请生成SQL："""

    messages = [{"role": "user", "content": prompt}]
    sql = call_mimo(messages, temperature=0.3)
    if sql:
        # Clean up: remove markdown code blocks if present
        sql = sql.strip()
        sql = sql.removeprefix("```sql").removeprefix("```").removesuffix("```").strip()
    return sql


def call_board(result):
    """Generate e-commerce data dashboard (Echarts)"""
    prompt = (
        f"根据提供的电商数据查询结果：{result}，生成一个专业且美观的echarts数据看板。\n"
        "要求：\n"
        "1. 顶部有KPI卡片，展示核心电商指标（如总用户数、总浏览量、购买转化率等），卡片需要美观\n"
        "2. 底部有数据分析和建议，详细一些，至少3条，排版美观\n"
        "3. 尽量使用多种图表综合展示（饼图、柱状图、折线图、漏斗图等），展示应全面且细致\n"
        "4. 图表大小适中，颜色鲜明\n"
        "5. 所有内容居中显示\n"
        "6. 仅返回html代码，不要有任何其他文本\n"
        "7. 输出内容不要包含```html```"
    )
    messages = [{"role": "user", "content": prompt}]
    answer_content = call_mimo(messages)
    if answer_content:
        logging.info("call_board completed")
    return answer_content


def call_html(result):
    """Generate e-commerce data analysis report (HTML)"""
    prompt = (
        f"根据电商用户行为数据查询结果：{result}，生成一个html数据分析报告，使用echarts图表展示数据。\n"
        "要求：\n"
        "1. 每一个echarts图表的上方需要使用表格列出echarts使用的数据\n"
        "2. 每一个echarts图表的下方需要有至少4行的文本描述，用于分析图表含义、数据变化趋势及原因\n"
        "3. html应美观专业\n"
        "4. 不要因为篇幅省略表格或图表\n"
        "5. 没有任何篇幅限制，请完整输出报告\n"
        "6. 仅返回html文本，不要有任何其他内容\n"
        "7. 不要包含```html```"
    )
    messages = [{"role": "user", "content": prompt}]
    answer_content = call_mimo(messages)
    if answer_content:
        logging.info("call_html completed")
    return answer_content


async def generate_pdf_async(file_path):
    """Convert HTML to PDF using Playwright"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                headless=True
            )
            page = await browser.new_page()
            await page.goto(f'file:///{os.path.abspath(file_path)}')
            await page.wait_for_timeout(3000)
            await page.pdf(path=file_path.replace('.html', '.pdf'), format='A4')
            await browser.close()
            logging.info(f"PDF generated: {file_path.replace('.html', '.pdf')}")
    except Exception as e:
        logging.error(f"PDF generation failed: {e}")


# ==================== API 端点 ====================


# ==================== 鉴权 API ====================

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "merchant"  # 默认为商家角色


@app.post("/auth/login")
async def login(req: LoginRequest):
    """用户登录，返回 JWT token"""
    user = find_user_by_username(req.username)
    if not user or not verify_password(req.password, user['password_hash']):
        raise fastapi.HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_token(user['username'], user['role'])
    return {
        "token": token,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "role": user['role'],
        }
    }


@app.post("/auth/register")
async def register(req: RegisterRequest):
    """用户注册（仅管理员可创建新用户）"""
    # 检查用户名是否已存在
    if find_user_by_username(req.username):
        raise fastapi.HTTPException(status_code=400, detail="用户名已存在")

    # 验证角色
    if req.role not in ('admin', 'merchant'):
        raise fastapi.HTTPException(status_code=400, detail="角色必须是 admin 或 merchant")

    # 插入新用户
    try:
        from auth import get_db
        conn = get_db()
        cursor = conn.cursor()
        hashed = hash_password(req.password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            (req.username, hashed, req.role)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": f"用户 {req.username} 创建成功", "role": req.role}
    except Exception as e:
        logging.error(f"注册失败: {e}")
        raise fastapi.HTTPException(status_code=500, detail="注册失败")


@app.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return {"user": current_user}


@app.get("/auth/users")
async def list_users(current_user: dict = Depends(require_admin)):
    """获取所有用户列表（仅管理员）"""
    try:
        from auth import get_db
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, role, created_at FROM users ORDER BY id")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        # 转换 datetime
        for u in users:
            if u.get('created_at'):
                u['created_at'] = u['created_at'].isoformat()
        return {"users": users}
    except Exception as e:
        logging.error(f"查询用户列表失败: {e}")
        return {"users": []}


@app.delete("/auth/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(require_admin)):
    """删除用户（仅管理员，不能删除自己）"""
    try:
        from auth import get_db
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # 查询目标用户
        cursor.execute("SELECT id, username, role FROM users WHERE id = %s", (user_id,))
        target = cursor.fetchone()
        if not target:
            cursor.close()
            conn.close()
            raise fastapi.HTTPException(status_code=404, detail="用户不存在")

        # 不能删除自己
        if target['username'] == current_user['username']:
            cursor.close()
            conn.close()
            raise fastapi.HTTPException(status_code=400, detail="不能删除自己")

        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": f"用户 {target['username']} 已删除"}
    except fastapi.HTTPException:
        raise
    except Exception as e:
        logging.error(f"删除用户失败: {e}")
        raise fastapi.HTTPException(status_code=500, detail="删除用户失败")


@app.get("/presets")
async def get_presets(current_user: dict = Depends(get_current_user)):
    """Return preset question templates"""
    return {"presets": PRESET_QUESTIONS}


@app.get("/history")
async def get_history(limit: int = 20, current_user: dict = Depends(get_current_user)):
    """Return recent query history"""
    sql = """
    SELECT id, question, sql_query, time_cost, category, cached, created_at
    FROM query_history
    ORDER BY created_at DESC
    LIMIT %s
    """
    result = my_sql_exec(sql, (limit,))
    # Fallback: use raw query if my_sql_exec doesn't return results properly
    try:
        import mysql.connector
        connection = mysql.connector.connect(**{
            'user': 'root', 'password': '123456', 'host': 'localhost',
            'database': 'ecommerce_qa', 'port': '3306'
        })
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql, (limit,))
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        # Convert datetime objects to strings
        for row in rows:
            if 'created_at' in row and row['created_at']:
                row['created_at'] = row['created_at'].isoformat()
            if 'cached' in row:
                row['cached'] = bool(row['cached'])
        return {"history": rows}
    except Exception as e:
        logging.error(f"Failed to fetch history: {e}")
        return {"history": []}


@app.post("/query")
async def query(
    user_question: str = Form(...),
    context: str = Form(default="[]"),
    current_user: dict = Depends(get_current_user),
):
    """API endpoint: natural language question -> SQL + dashboard"""
    start_time = time.time()

    # Parse conversation context
    try:
        conversation = json.loads(context)
    except (json.JSONDecodeError, TypeError):
        conversation = []

    # Check cache
    cache_key = get_cache_key(user_question)
    if cache_key in query_cache:
        cached = query_cache[cache_key]
        elapsed = time.time() - start_time
        save_to_history(user_question, cached['sql'], cached['result'],
                        cached['time_cost'], get_category(user_question), cached=True)
        logging.info(f"Cache hit: {user_question}")
        return {**cached, "cached": True, "time": f"{elapsed:.2f}s"}

    try:
        # Generate SQL: multi-turn with context, or similarity search
        if conversation:
            logging.info(f"Multi-turn query with {len(conversation)} context turns")
            sql_query = generate_sql_with_context(user_question, conversation)
        else:
            similar_qa = db.query_similar_qa(user_question, k=3)
            sql_query = similar_qa[0] if similar_qa else None

        logging.info(f"SQL: {sql_query}")

        if not sql_query:
            return {"error": "无法生成对应的SQL查询"}

        # Execute SQL
        query_result = my_sql(sql_query)
        logging.info(f"Query executed, {len(query_result) if query_result else 0} rows")

        # Generate dashboard
        board_html = call_board(query_result)

        # Save output
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
        os.makedirs(output_dir, exist_ok=True)
        timestamp = int(time.time() * 1000)
        html_path = os.path.join(output_dir, f'board_{timestamp}.html')

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(board_html)

        # Generate PDF
        await generate_pdf_async(html_path)

        elapsed = time.time() - start_time

        result = {
            "sql": sql_query,
            "result": query_result,
            "board_html": board_html,
            "html_path": html_path,
            "pdf_path": html_path.replace('.html', '.pdf'),
            "time": f"{elapsed:.2f}s",
            "cached": False,
        }

        # Cache the result
        cache_result = {
            "sql": sql_query,
            "result": query_result,
            "board_html": board_html,
            "html_path": html_path,
            "pdf_path": html_path.replace('.html', '.pdf'),
            "time": f"{elapsed:.2f}s",
        }
        if len(query_cache) >= CACHE_MAX_SIZE:
            oldest_key = next(iter(query_cache))
            del query_cache[oldest_key]
        query_cache[cache_key] = cache_result

        # Save to history
        save_to_history(user_question, sql_query, query_result,
                        f"{elapsed:.2f}s", get_category(user_question))

        return result

    except Exception as e:
        import traceback
        logging.error(f"Query failed: {e}")
        logging.error(traceback.format_exc())
        return {"error": str(e)}


@app.post("/report")
async def report(user_question: str = Form(...), current_user: dict = Depends(get_current_user)):
    """API endpoint: generate detailed analysis report"""
    start_time = time.time()

    try:
        similar_qa = db.query_similar_qa(user_question, k=3)
        sql_query = similar_qa[0] if similar_qa else None
        if not sql_query:
            return {"error": "No matching SQL found"}

        query_result = my_sql(sql_query)
        report_html = call_html(query_result)

        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
        os.makedirs(output_dir, exist_ok=True)
        timestamp = int(time.time() * 1000)
        html_path = os.path.join(output_dir, f'report_{timestamp}.html')

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(report_html)

        await generate_pdf_async(html_path)

        elapsed = time.time() - start_time

        return {
            "sql": sql_query,
            "result": query_result,
            "report_html": report_html,
            "html_path": html_path,
            "pdf_path": html_path.replace('.html', '.pdf'),
            "time": f"{elapsed:.2f}s"
        }

    except Exception as e:
        logging.error(f"Report generation failed: {e}")
        return {"error": str(e)}


@app.get("/")
async def root():
    return {"message": "E-commerce QA System API", "version": "2.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/download")
async def download_file(path: str, current_user: dict = Depends(get_current_user)):
    """Download a generated file"""
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "File not found"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=35052)
