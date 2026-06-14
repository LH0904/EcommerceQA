from data.DDL import DDL
from data.DOC import DOC
from data.QA import QA
import logging
import time
from vec import VectorDBManager

db = VectorDBManager()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("开始添加向量")

    # 添加DDL
    count_ddl = 0
    logging.info("开始添加ddl")
    start_time = time.time()
    for ddl in DDL:
        db.store_ddl(ddl)
        count_ddl += 1
        logging.info(f"已添加{count_ddl}个ddl")
    logging.info("ddl添加完成")

    # 添加DOC
    count_doc = 0
    logging.info("开始添加doc")
    for doc in DOC:
        db.store_doc(doc)
        count_doc += 1
        logging.info(f"已添加{count_doc}个doc")
    logging.info("doc添加完成")

    # 添加QA
    count_qa = 0
    logging.info("开始添加qa")
    for qa in QA:
        db.store_qa(question=qa["question"], sql=qa["answer"])
        count_qa += 1
        logging.info(f"已添加{count_qa}个qa")
    logging.info(f"qa添加完成,耗时{time.time() - start_time:.2f}秒")
