import mysql.connector
import logging

db_config = {
    'user': 'root',
    'password': '123456',
    'host': 'localhost',
    'database': 'ecommerce_qa',
    'port': '3306',
    'raise_on_warnings': True
}
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def my_sql(sql):
    """Execute SELECT queries, return list of dicts"""
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        return result
    except mysql.connector.Error as err:
        logging.error(f"Error executing SQL query: {err}")
        return None
    finally:
        cursor.close()
        connection.close()


def my_sql_exec(sql, params=None):
    """Execute INSERT/UPDATE/CREATE/DDL statements, return lastrowid or None"""
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params or ())
        connection.commit()
        return cursor.lastrowid
    except mysql.connector.Error as err:
        logging.error(f"Error executing SQL: {err}")
        connection.rollback()
        return None
    finally:
        cursor.close()
        connection.close()
