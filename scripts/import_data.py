"""
数据导入脚本 - 将 CSV 文件导入 MySQL
运行方式: 从项目根目录执行 python scripts/import_data.py
"""
import sys
import csv
import mysql.connector
import os

# 将项目根目录加入 sys.path，以便导入 app 包
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))

from app.config import settings

DB_CONFIG = {
    'host': settings.DB_HOST,
    'port': settings.DB_PORT,
    'user': settings.DB_USER,
    'password': settings.DB_PASSWORD,
    'database': settings.DB_NAME,
}

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'data')

def create_tables():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS user_behavior")
    cursor.execute("DROP TABLE IF EXISTS goods")
    cursor.execute("DROP TABLE IF EXISTS comments")
    cursor.execute("DROP TABLE IF EXISTS categories")
    cursor.execute("DROP TABLE IF EXISTS user_profiles")

    cursor.execute("""
        CREATE TABLE user_behavior (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(50),
            goods_id VARCHAR(50),
            category_id VARCHAR(50),
            behavior_type VARCHAR(20),
            timestamp DATETIME,
            gender VARCHAR(10),
            age INT,
            city VARCHAR(100),
            device VARCHAR(50),
            price DECIMAL(10,2),
            amount INT,
            total_amount DECIMAL(12,2),
            user_age_group VARCHAR(50),
            goods_category VARCHAR(200),
            behavior_hour INT,
            behavior_weekday INT,
            INDEX idx_user_id(user_id),
            INDEX idx_goods_id(goods_id),
            INDEX idx_category_id(category_id),
            INDEX idx_behavior_type(behavior_type),
            INDEX idx_timestamp(timestamp)
        )
    """)

    cursor.execute("""
        CREATE TABLE goods (
            id INT AUTO_INCREMENT PRIMARY KEY,
            goods_id VARCHAR(50),
            sales_count INT,
            goods_name VARCHAR(500),
            category_id VARCHAR(50),
            category_name VARCHAR(200),
            INDEX idx_goods_id(goods_id),
            INDEX idx_category_id(category_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE comments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(50),
            goods_id VARCHAR(50),
            category_id VARCHAR(50),
            comment TEXT,
            INDEX idx_user_id(user_id),
            INDEX idx_goods_id(goods_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category_id VARCHAR(50),
            product_count INT,
            category_name VARCHAR(200),
            INDEX idx_category_id(category_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE user_profiles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(50),
            occupation VARCHAR(100),
            INDEX idx_user_id(user_id)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Tables created")

def import_csv(table_name, csv_file, columns):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    csv_path = os.path.join(DATA_DIR, csv_file)
    placeholders = ', '.join(['%s'] * len(columns))
    cols = ', '.join(columns)

    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        batch = []
        for row in reader:
            values = []
            for c in columns:
                v = row.get(c, '')
                values.append(v if v != '' else None)
            batch.append(tuple(values))
            count += 1
            if len(batch) >= 5000:
                cursor.executemany(f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})", batch)
                conn.commit()
                batch = []
                print(f"  {table_name}: {count} rows")

        if batch:
            cursor.executemany(f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})", batch)
            conn.commit()

    cursor.close()
    conn.close()
    print(f"  {table_name}: DONE ({count} rows)")

if __name__ == "__main__":
    print("Creating tables...")
    create_tables()

    print("\nImporting data...")
    import_csv("user_profiles", "user_profiles.csv", ["user_id", "occupation"])
    import_csv("categories", "categories.csv", ["category_id", "product_count", "category_name"])
    import_csv("goods", "goods.csv", ["goods_id", "sales_count", "goods_name", "category_id", "category_name"])
    import_csv("comments", "comments.csv", ["user_id", "goods_id", "category_id", "comment"])
    import_csv("user_behavior", "user_behavior.csv", [
        "user_id", "goods_id", "category_id", "behavior_type", "timestamp",
        "gender", "age", "city", "device", "price", "amount", "total_amount",
        "user_age_group", "goods_category", "behavior_hour", "behavior_weekday"
    ])
    print("\nAll done!")
