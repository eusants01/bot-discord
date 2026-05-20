import os
import asyncpg

pool = None


async def conectar_db():
    global pool

    if pool is not None:
        return pool

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL não encontrada.")

    pool = await asyncpg.create_pool(database_url)

    async with pool.acquire() as conn:

        # WARNS
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

        # SORTEIOS
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sorteios (
                id TEXT PRIMARY KEY,

                guild_id BIGINT NOT NULL,
                channel_id BIGINT NOT NULL,
                message_id BIGINT,

                criador_id BIGINT NOT NULL,

                premio TEXT NOT NULL,
                descricao TEXT NOT NULL,

                ganhadores INTEGER NOT NULL,

                requisito_id BIGINT,

                participantes BIGINT[] DEFAULT '{}',
                vencedores BIGINT[] DEFAULT '{}',

                inicio BIGINT NOT NULL,
                fim BIGINT NOT NULL,

                status TEXT NOT NULL DEFAULT 'ativo'
            )
        """)

    return pool