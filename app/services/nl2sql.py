"""
NL2SQL 服务 - 自然语言转 SQL 的核心引擎
支持两种路径：向量检索（单轮）和 LLM 生成（多轮对话）
"""
import logging

from app.data.vector_db import VectorDBManager
from app.services.llm import generate_sql_prompt

logger = logging.getLogger(__name__)


class NL2SQLService:
    """NL2SQL 核心服务"""

    def __init__(self, vector_db: VectorDBManager):
        self.vector_db = vector_db

    def generate_sql(self, question: str, conversation: list = None) -> str | None:
        """
        主入口：根据是否有对话上下文选择生成策略
        - 有上下文 → 多轮对话 LLM 生成
        - 无上下文 → 向量相似度检索
        """
        if conversation:
            return self._generate_with_context(question, conversation)
        else:
            return self._generate_by_similarity(question)

    def _generate_by_similarity(self, question: str) -> str | None:
        """通过向量相似度检索获取最匹配的 SQL"""
        try:
            similar_qa = self.vector_db.query_similar_qa(question, k=3)
            if similar_qa:
                sql = similar_qa[0]
                logger.info(f"向量检索命中 SQL: {sql[:80]}...")
                return sql
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
        return None

    def _generate_with_context(self, question: str, conversation: list) -> str | None:
        """多轮对话场景：将对话历史和当前问题发给 LLM 生成 SQL"""
        try:
            # 获取数据库 schema
            ddl_list = self.vector_db.query_all_ddl()
            schema_str = "\n".join(ddl_list)

            # 构建对话上下文（取最近 3 轮）
            ctx_lines = []
            for i, item in enumerate(conversation[-3:], 1):
                ctx_lines.append(f"{i}. 问题: {item['question']}\n   SQL: {item['sql']}")
            context_str = "\n".join(ctx_lines)

            sql = generate_sql_prompt(question, schema_str, context_str)
            if sql:
                logger.info(f"LLM 生成 SQL: {sql[:80]}...")
            return sql
        except Exception as e:
            logger.error(f"多轮对话 SQL 生成失败: {e}")
            return None
