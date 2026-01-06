import os
import psycopg2
from psycopg2 import sql

def create_postgres_connection(host, port, database, user, password):
    """建立並返回 PostgreSQL 數據庫連接和游標對象。"""
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    cursor = conn.cursor()
    return conn, cursor

def close_postgres_connection(conn, cursor):
    """關閉 PostgreSQL 數據庫連接和游標對象。"""
    cursor.close()
    conn.close()

def create_database(conn, cursor, database_name):
    """創建 PostgreSQL 數據庫。"""
    cursor.execute(f"CREATE DATABASE {database_name}")

def load_data_to_postgres(conn, cursor, local_dbgen_dir, target_database):
    """從本地文件夾加載數據到 PostgreSQL 數據庫中。"""
    tables = {
        'region': 'region.tbl',
        'nation': 'nation.tbl',
        'partsupp': 'partsupp.tbl',
        'customer': 'customer.tbl',
        'lineitem': 'lineitem.tbl',
        'orders': 'orders.tbl',
        'part': 'part.tbl'
    }

    for table_name, file_name in tables.items():
        file_path = os.path.join(local_dbgen_dir, file_name)
        copy_sql = sql.SQL("COPY {} FROM STDIN WITH CSV DELIMITER '|' NULL ''").format(
            sql.Identifier(table_name)
        )
        with open(file_path, 'r') as f:
            cursor.copy_expert(copy_sql, f)
        print(f"已從 {file_name} 加載數據到表 {table_name}")

if __name__ == '__main__':
    # PostgreSQL 連接信息
    db_params = {
        'host': 'your_postgres_host',
        'port': 'your_postgres_port',
        'database': 'postgresdb',  # 默認連接到 PostgreSQL 的系統數據庫
        'user': 'your_postgres_user',
        'password': 'your_postgres_password'
    }

    # 本地 tpchdbgen 文件夾路徑
    local_dbgen_dir = '/path/to/tpchdbgen'

    # PostgreSQL 目標數據庫名稱
    target_database = 'demo_tpch'

    try:
        # 連接到 PostgreSQL 系統數據庫
        conn, cursor = create_postgres_connection(**db_params)

        # 創建目標數據庫 demo_tpch
        create_database(conn, cursor, target_database)

        # 切換連接到 demo_tpch 數據庫
        close_postgres_connection(conn, cursor)
        db_params['database'] = target_database
        conn, cursor = create_postgres_connection(**db_params)

        # 將數據加載到 demo_tpch 數據庫中
        load_data_to_postgres(conn, cursor, local_dbgen_dir, target_database)

        # 提交更改
        conn.commit()

    except psycopg2.Error as e:
        print(f"錯誤: {e}")

    finally:
        # 關閉連接
        close_postgres_connection(conn, cursor)
