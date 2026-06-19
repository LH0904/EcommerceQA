"""
查询编排服务 - 将缓存→SQL生成→执行→看板→历史的流程组织为清晰的管道
"""
import time
import asyncio
import logging

from app.data.db import execute_query
from app.services.nl2sql import NL2SQLService
from app.services.llm import generate_board_html, generate_report_html
from app.services.file_export import save_html, generate_pdf
from app.data.history_repo import save
from app.utils.cache import QueryCache
from app.utils.presets import get_category

logger = logging.getLogger(__name__)


class QueryService:
    """核心查询编排服务"""

    def __init__(
        self,
        nl2sql: NL2SQLService,
        cache: QueryCache,
    ):
        self.nl2sql = nl2sql
        self.cache = cache

    async def execute_query(self, question: str, conversation: list = None) -> dict:
        """
        完整查询流程：
        1. 检查缓存
        2. 生成 SQL
        3. 执行 SQL
        4. 生成看板
        5. 保存文件
        6. 记录历史
        7. 缓存结果
        """
        start_time = time.time()
        category = get_category(question)

        # 1. 检查缓存
        cache_key = self.cache.make_key(question)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            elapsed = time.time() - start_time
            # 异步保存历史（标记为缓存命中）
            asyncio.get_event_loop().run_in_executor(
                None,
                save,
                question,
                cached_result["sql"],
                cached_result["result"],
                cached_result.get("time", ""),
                category,
                True,
            )
            logger.info(f"缓存命中: {question}")
            return {**cached_result, "cached": True, "time": f"{elapsed:.2f}s"}

        try:
            # 2. 生成 SQL
            sql_query = self.nl2sql.generate_sql(question, conversation)
            logger.info(f"SQL: {sql_query}")

            if not sql_query:
                return {"error": "无法生成对应的SQL查询"}

            # 3. 执行 SQL
            query_result = execute_query(sql_query)
            logger.info(f"查询完成，{len(query_result) if query_result else 0} 行")

            # 4. 生成看板
            board_html = generate_board_html(query_result)

            # 5. 保存文件
            html_path = save_html(board_html, prefix="board")
            await generate_pdf(html_path)

            elapsed = time.time() - start_time
            time_str = f"{elapsed:.2f}s"
            pdf_path = html_path.replace(".html", ".pdf")

            result = {
                "sql": sql_query,
                "result": query_result,
                "board_html": board_html,
                "html_path": html_path,
                "pdf_path": pdf_path,
                "time": time_str,
                "cached": False,
            }

            # 6. 缓存结果（不含 cached 标记）
            cache_value = {
                "sql": sql_query,
                "result": query_result,
                "board_html": board_html,
                "html_path": html_path,
                "pdf_path": pdf_path,
                "time": time_str,
            }
            self.cache.put(cache_key, cache_value)

            # 7. 保存历史
            save(question, sql_query, query_result, time_str, category)

            return result

        except Exception as e:
            import traceback

            logger.error(f"查询失败: {e}")
            logger.error(traceback.format_exc())
            return {"error": str(e)}

    async def generate_report(self, question: str) -> dict:
        """生成详细分析报告"""
        start_time = time.time()

        try:
            # 向量检索获取 SQL
            sql_query = self.nl2sql.generate_sql(question)
            if not sql_query:
                return {"error": "No matching SQL found"}

            # 执行 SQL
            query_result = execute_query(sql_query)

            # 生成报告
            report_html = generate_report_html(query_result)

            # 保存文件
            html_path = save_html(report_html, prefix="report")
            await generate_pdf(html_path)

            elapsed = time.time() - start_time

            return {
                "sql": sql_query,
                "result": query_result,
                "report_html": report_html,
                "html_path": html_path,
                "pdf_path": html_path.replace(".html", ".pdf"),
                "time": f"{elapsed:.2f}s",
            }

        except Exception as e:
            logger.error(f"报告生成失败: {e}")
            return {"error": str(e)}
