from utils.database import conectar_db


async def criar_sorteio(dados: dict):
    db = await conectar_db()

    async with db.acquire() as conn:
        await conn.execute("""
            INSERT INTO sorteios (
                id,
                guild_id,
                channel_id,
                message_id,
                criador_id,
                premio,
                descricao,
                ganhadores,
                requisito_id,
                participantes,
                vencedores,
                inicio,
                fim,
                status
            )

            VALUES (
                $1,$2,$3,$4,$5,
                $6,$7,$8,$9,
                $10,$11,$12,$13,$14
            )
        """,

        dados["id"],
        dados["guild_id"],
        dados["channel_id"],
        dados["message_id"],
        dados["criador_id"],
        dados["premio"],
        dados["descricao"],
        dados["ganhadores"],
        dados["requisito_id"],
        dados["participantes"],
        dados["vencedores"],
        dados["inicio"],
        dados["fim"],
        dados["status"]
        )


async def buscar_sorteio(sorteio_id):
    db = await conectar_db()

    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM sorteios WHERE id = $1",
            sorteio_id
        )

        return dict(row) if row else None


async def buscar_sorteios_ativos():
    db = await conectar_db()

    async with db.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM sorteios WHERE status = 'ativo'"
        )

        return [dict(r) for r in rows]


async def adicionar_participante(sorteio_id, user_id):
    db = await conectar_db()

    async with db.acquire() as conn:

        sorteio = await conn.fetchrow("""
            SELECT participantes
            FROM sorteios
            WHERE id = $1
        """, sorteio_id)

        if not sorteio:
            return False

        participantes = list(sorteio["participantes"] or [])

        if user_id in participantes:
            return None

        participantes.append(user_id)

        await conn.execute("""
            UPDATE sorteios
            SET participantes = $1
            WHERE id = $2
        """, participantes, sorteio_id)

        return True


async def remover_participante(sorteio_id, user_id):
    db = await conectar_db()

    async with db.acquire() as conn:

        sorteio = await conn.fetchrow("""
            SELECT participantes
            FROM sorteios
            WHERE id = $1
        """, sorteio_id)

        if not sorteio:
            return False

        participantes = list(sorteio["participantes"] or [])

        if user_id not in participantes:
            return None

        participantes.remove(user_id)

        await conn.execute("""
            UPDATE sorteios
            SET participantes = $1
            WHERE id = $2
        """, participantes, sorteio_id)

        return True


async def finalizar_sorteio(sorteio_id, vencedores):
    db = await conectar_db()

    async with db.acquire() as conn:
        await conn.execute("""
            UPDATE sorteios
            SET
                status = 'finalizado',
                vencedores = $1
            WHERE id = $2
        """, vencedores, sorteio_id)


async def cancelar_sorteio(sorteio_id):
    db = await conectar_db()

    async with db.acquire() as conn:
        await conn.execute("""
            UPDATE sorteios
            SET status = 'cancelado'
            WHERE id = $1
        """, sorteio_id)