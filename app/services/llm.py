"""
MiMo LLM 调用封装 - 统一管理与大模型的交互
"""
import logging
from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# MiMo 客户端（延迟初始化）
_mimo_client: OpenAI | None = None


def get_mimo_client() -> OpenAI:
    """获取或创建 MiMo API 客户端"""
    global _mimo_client
    if _mimo_client is None:
        _mimo_client = OpenAI(
            api_key=settings.MIMO_API_KEY,
            base_url=settings.MIMO_BASE_URL,
        )
    return _mimo_client


def call_mimo(messages: list, temperature: float = 0.7) -> str | None:
    """
    调用 MiMo API，返回生成的文本
    使用流式传输，拼接完整响应后返回
    """
    try:
        client = get_mimo_client()
        response = client.chat.completions.create(
            model=settings.MIMO_MODEL,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        content = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content += chunk.choices[0].delta.content
        return content if content else None
    except Exception as e:
        logger.error(f"MiMo API 调用失败: {e}")
        return None


def generate_board_html(result) -> str | None:
    """根据查询结果生成 Echarts 数据看板 HTML"""
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
    content = call_mimo(messages)
    if content:
        logger.info("数据看板生成完成")
    return content


def generate_report_html(result) -> str | None:
    """根据查询结果生成详细数据分析报告 HTML"""
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
    content = call_mimo(messages)
    if content:
        logger.info("分析报告生成完成")
    return content


def generate_sql_prompt(question: str, schema_str: str, context_str: str) -> str | None:
    """
    使用 LLM 根据对话上下文生成 SQL
    返回纯 SQL 文本，或 None
    """
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
        sql = sql.strip()
        sql = sql.removeprefix("```sql").removeprefix("```").removesuffix("```").strip()
    return sql
