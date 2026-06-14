import os
import chromadb
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document


class VectorDBManager:
    def __init__(self, persist_directory=None):
        # init embedding model via DashScope API
        if persist_directory is None:
            persist_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chroma_db')
        self.embeddings = DashScopeEmbeddings(model="text-embedding-v3")
        # DashScopeEmbeddings reads DASHSCOPE_API_KEY from env automatically

        # init Chroma client
        self.client = chromadb.PersistentClient(path=persist_directory)

        # create collections for DDL, DOC, QA, SQLs
        self.ddl_collection = Chroma(
            client=self.client,
            collection_name="ddl_collection",
            embedding_function=self.embeddings
        )

        self.doc_collection = Chroma(
            client=self.client,
            collection_name="doc_collection",
            embedding_function=self.embeddings
        )

        self.qa_collection = Chroma(
            client=self.client,
            collection_name="qa_collection",
            embedding_function=self.embeddings
        )

        self.sqls_collection = Chroma(
            client=self.client,
            collection_name="sqls_collection",
            embedding_function=self.embeddings
        )

    # ========== Store Methods ==========

    def store_ddl(self, ddl):
        """Store table schema (DDL)"""
        doc = Document(page_content=ddl)
        self.ddl_collection.add_documents([doc])

    def store_doc(self, content):
        """Store text description (DOC)"""
        doc = Document(page_content=content)
        self.doc_collection.add_documents([doc])

    def store_qa(self, question, sql):
        """Store Q&A pair (QA)"""
        doc = Document(page_content=question, metadata={"answer": sql})
        self.qa_collection.add_documents([doc])

    def store_sqls(self, arr):
        """Store question mappings for report generation"""
        doc = [Document(page_content=pair["question"], metadata={"answer": pair["answer"]}) for pair in arr]
        self.sqls_collection.add_documents(doc)

    # ========== Query Methods ==========

    def query_all_ddl(self):
        """Query all DDL info, return list containing all DDL"""
        all_docs = self.ddl_collection.get()
        return all_docs['documents']

    def query_similar_doc(self, query, k=4):
        """Query documents most similar to input text"""
        similar_docs = self.doc_collection.similarity_search(query, k=k)
        return [doc.page_content for doc in similar_docs]

    def query_similar_qa(self, question, k=4):
        """Query Q&A pairs most similar to input question"""
        similar_qa = self.qa_collection.similarity_search(question, k=k)
        return [qa.metadata['answer'] for qa in similar_qa]

    def query_similar_sqls(self, question, k=1):
        sqls = self.sqls_collection.similarity_search(question, k=k)[0].metadata["answer"]
        return sqls

    # ========== Management Methods ==========

    def clear_all_collections(self):
        """Clear all collections (DDL, DOC, QA). WARNING: irreversible!"""
        self.ddl_collection.delete_collection()
        self.ddl_collection = Chroma(
            client=self.client,
            collection_name="ddl_collection",
            embedding_function=self.embeddings
        )

        self.doc_collection.delete_collection()
        self.doc_collection = Chroma(
            client=self.client,
            collection_name="doc_collection",
            embedding_function=self.embeddings
        )

        self.qa_collection.delete_collection()
        self.qa_collection = Chroma(
            client=self.client,
            collection_name="qa_collection",
            embedding_function=self.embeddings
        )

        print("All collections cleared")

    def show(self):
        """Display all vector data in the database"""
        collections = [
            ("ddl_collection", self.ddl_collection),
            ("doc_collection", self.doc_collection),
            ("qa_collection", self.qa_collection),
            ("sqls_collection", self.sqls_collection)
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
