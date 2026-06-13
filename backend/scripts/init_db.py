"""数据库初始化脚本 - 执行 01_schema.sql + 02_seed.sql"""
import os
import sys
import psycopg2

# 简化:从环境变量或 .env 读
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "xiaoz")
DB_PASSWORD = os.getenv("DB_PASSWORD", "xiaoz_pwd")
DB_NAME = os.getenv("DB_NAME", "xiaoz_resume")


def run_sql_file(path: str):
    print(f"执行: {path}")
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, dbname=DB_NAME,
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(sql)
    cur.close()
    conn.close()
    print(f"✓ {path} 执行完成")


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_dir = os.path.join(os.path.dirname(base), "db")
    run_sql_file(os.path.join(db_dir, "01_schema.sql"))
    run_sql_file(os.path.join(db_dir, "02_seed.sql"))
    print("\n✓ 数据库初始化完成")
