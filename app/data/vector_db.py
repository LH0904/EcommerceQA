"""
向量数据库访问层 - 封装 ChromaDB 操作
"""
import os
import logging

import chromadb
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import settings

logger = logging.getLogger(__name__)


class VectorDBManager:
    """ChromaDB 向量数据库管理器"""

    def __init__(self, persist_directory=None):
        if persist_directory is None:
            # 默认路径: nl2sql/chroma_db (项目根目录下)
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            persist_directory = os.path.join(
                project_root,
                "nl2sql",
                "chroma_db",
            )

        self.embeddings = DashScopeEmbeddings(model="text-embedding-v3")
        self.client = chromadb.PersistentClient(path=persist_directory)

        # 4 个集合：DDL / DOC / QA / SQLs
        self.ddl_collection = Chroma(
            client=self.client,
            collection_name="ddl_collection",
            embedding_function=self.embeddings,
        )
        self.doc_collection = Chroma(
            client=self.client,
            collection_name="doc_collection",
            embedding_function=self.embeddings,
        )
        self.qa_collection = Chroma(
            client=self.client,
            collection_name="qa_collection",
            embedding_function=self.embeddings,
        )
        self.sqls_collection = Chroma(
            client=self.client,
            collection_name="sqls_collection",
            embedding_function=self.embeddings,
        )

    # ========== 存储方法 ==========

    def store_ddl(self, ddl):
        """存储表结构 (DDL)"""
        doc = Document(page_content=ddl)
        self.ddl_collection.add_documents([doc])

    def store_doc(self, content):
        """存储文本描述 (DOC)"""
        doc = Document(page_content=content)
        self.doc_collection.add_documents([doc])

    def store_qa(self, question, sql):
        """存储问答对 (QA)"""
        doc = Document(page_content=question, metadata={"answer": sql})
        self.qa_collection.add_documents([doc])

    def store_sqls(self, arr):
        """存储问题映射（用于报告生成）"""
        docs = [
            Document(page_content=pair["question"], metadata={"answer": pair["answer"]})
            for pair in arr
        ]
        self.sqls_collection.add_documents(docs)

    # ========== 查询方法 ==========

    def query_all_ddl(self):
        """查询全部 DDL 信息"""
        all_docs = self.ddl_collection.get()
        return all_docs["documents"]

    def query_similar_doc(self, query, k=4):
        """查询与输入最相似的文档"""
        similar_docs = self.doc_collection.similarity_search(query, k=k)
        return [doc.page_content for doc in similar_docs]

    def query_similar_qa(self, question, k=4):
        """查询与问题最相似的 QA 对，返回 SQL 列表"""
        similar_qa = self.qa_collection.similarity_search(question, k=k)
        return [qa.metadata["answer"] for qa in similar_qa]

    def query_similar_sqls(self, question, k=1):
        """查询最相似的 SQL 映射"""
        sqls = self.sqls_collection.similarity_search(question, k=k)[0].metadata["answer"]
        return sqls

    # ========== 管理方法 ==========

    def clear_all_collections(self):
        """清空所有集合（不可逆！）"""
        for name, attr in [
            ("ddl_collection", "ddl_collection"),
            ("doc_collection", "doc_collection"),
            ("qa_collection", "qa_collection"),
        ]:
            getattr(self, attr).delete_collection()
            setattr(
                self,
                attr,
                Chroma(
                    client=self.client,
                    collection_name=name,
                    embedding_function=self.embeddings,
                ),
            )
        logger.info("所有集合已清空")

    def show(self):
        """展示所有向量数据"""
        collections = [
            ("ddl_collection", self.ddl_collection),
            ("doc_collection", self.doc_collection),
            ("qa_collection", self.qa_collection),
            ("sqls_collection", self.sqls_collection),
        ]
        for coll_name, coll in collections:
            print(f"=== Collection: {coll_name} ===")
            all_docs = coll.get()
            docs = all_docs.get("documents", [])
            doc_ids = all_docs.get("ids", [])
            metadatas = all_docs.get("metadatas", [])

            if not docs:
                print("  Empty\n")
                continue

            for idx, (doc, doc_id, metadata) in enumerate(
                zip(docs, doc_ids, metadatas), start=1
            ):
                print(f"Doc {idx}:")
                print(f"Question: {doc}")
                if metadata:
                    print(f"Answer: {metadata.get('answer', 'N/A')}")
            print("-" * 50)
