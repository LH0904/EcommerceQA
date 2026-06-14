from vec import VectorDBManager

db = VectorDBManager()

if __name__ == "__main__":
    # 删除所有数据
    # db.clear_all_collections()


    # 展示所有数据
    db.show()