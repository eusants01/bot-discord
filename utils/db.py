import sqlite3

conn = sqlite3.connect("conquistas.db")
cursor = conn.cursor()

def criar_tabelas():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conquistas (
        user_id TEXT,
        conquista_id TEXT,
        data TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mensagens (
        user_id TEXT PRIMARY KEY,
        total INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS codigos (
        codigo TEXT,
        user_id TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS titulos (
        user_id TEXT PRIMARY KEY,
        titulo TEXT
    )
    """)

    conn.commit()