import os
import asyncpg

pool = None


async def conectar_db():
    global pool

    if pool is not None:
        return pool

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL não encontrada nas variáveis de ambiente.")

    pool = await asyncpg.create_pool(database_url)

    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS warns (
            id SERIAL PRIMARY KEY,
            guild_id BIGINT NOT NULL,
            user_id BIGINT NOT NULL,
            staff_id BIGINT NOT NULL,
            motivo TEXT NOT NULL,
            data TEXT NOT NULL
        )
        """)

    print("✅ PostgreSQL conectado e tabelas verificadas.")
    return pool


def get_pool():
    if pool is None:
        raise RuntimeError("Banco de dados ainda não foi conectado.")
    return pool