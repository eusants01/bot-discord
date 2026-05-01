import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não encontrada no Railway.")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

def criar_tabelas():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conquistas (
            user_id TEXT,
            conquista_id TEXT,
            data TEXT,
            PRIMARY KEY (user_id, conquista_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            user_id TEXT PRIMARY KEY,
            total INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS codigos (
            codigo TEXT,
            user_id TEXT,
            PRIMARY KEY (codigo, user_id)
        )
    """)

    conn.commit()