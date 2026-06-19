import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import os
import random
import logging
from datetime import datetime, timedelta, timezone
from collections import Counter

import asyncpg

logger = logging.getLogger("sorteios")

COR_CUPHEAD   = 0xC48A3A
COR_DOURADA   = 0xFFD700
COR_VERDE     = 0x2ECC71
COR_VERMELHO  = 0x8B3A3A
COR_ROXO      = 0x9B59B6
COR_LARANJA   = 0xE67E22   


BANNERS = {
    "ativo":      "https://media.discordapp.net/attachments/961677475191078992/1510111531243933716/RgGXAAAABklEQVQDAEZvdQlgAtWFAAAAAElFTkSuQmCC.png?ex=6a1ba075&is=6a1a4ef5&hm=07e0f157f5e9f534d9e72201ca68dce09a2dcb6f886bc6bc305d89bdde80c8b2&=&format=webp&quality=lossless",
    "vencedor":   "https://media.discordapp.net/attachments/961677475191078992/1510111530731966554/4m1Yc4AAAAGSURBVAMAIhJq0lQ0SxAAAAAASUVORK5CYII.png?ex=6a1ba075&is=6a1a4ef5&hm=e199e8cd1fd4c9d6334564dfc3e9ea68fcd4e2e045d60c3f918fce39b8a47fb1&=&format=webp&quality=lossless",
    "cancelado":  "https://media.discordapp.net/attachments/961677475191078992/1510111531595989183/8n20PEAAAABklEQVQDAKLuoNzTHmVcAAAAAElFTkSuQmCC.png?ex=6a1ba075&is=6a1a4ef5&hm=7db8a9a2a649bb9dd53af3c23535159f4a826e0f81948a24df9d15ef1c87743a&=&format=webp&quality=lossless",
    "sem_ganho":  "https://media.discordapp.net/attachments/961677475191078992/1510111531969544222/9nqs7uAAAABklEQVQDAKFdrWaYqa4kAAAAAElFTkSuQmCC.png?ex=6a1ba075&is=6a1a4ef5&hm=07331996899d4e43ad5904c402ab2abded31749295fc251403267abcc86c396e&=&format=webp&quality=lossless",
    "reroll":     "https://media.discordapp.net/attachments/961677475191078992/1510111532720062645/kudHpAAAAAZJREFUAwBzE3bm4YTgCAAAAABJRU5ErkJggg.png?ex=6a1ba075&is=6a1a4ef5&hm=d6a686124710b250e77b0669a9f75b41e2380f81a164498ed7852809c11a831d&=&format=webp&quality=lossless",
}

CARGOS_BONUS = {
     1486411238513836052: 3,   # Cargo de patrocinador do servidor
     1480334522053558465: 1,   # Cargo de booster do servidor
     1511436547524792526: 1,   # Cargo VIP do servidor 
}


CARGOS_ADMIN_SORTEIO = [
    1492220245996343377,
    1480334545944449024,
    1485706762765074544,
    1483191687927828766,
    1480349452744265759,
    1501356975491907664,
]

CANAL_LOG_SORTEIOS_ID = 0

DATABASE_URL = os.getenv("DATABASE_URL")

FRAMES_ANIMACAO = [
    "🎰 ▓░░░░░░░░░ Sorteando...",
    "🎰 ▓▓▓░░░░░░░ Sorteando...",
    "🎰 ▓▓▓▓▓░░░░░ Sorteando...",
    "🎰 ▓▓▓▓▓▓▓░░░ Quase lá...",
    "🎰 ▓▓▓▓▓▓▓▓▓░ Quase lá...",
    "🎰 ▓▓▓▓▓▓▓▓▓▓ Resultado!",
]

DELAY_FRAME = 0.5
INTERVALO_CHECAGEM_SEGUNDOS = 30
INTERVALO_REFRESH_MINUTOS   = 3
LIMIAR_URGENCIA_SEGUNDOS = 5 * 60

async def _abrir_conexao() -> asyncpg.Connection:
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não configurada. Adicione no .env: "
            "DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_do_banco"
        )
    return await asyncpg.connect(DATABASE_URL)


async def inicializar_banco_sorteios():
    conn = await _abrir_conexao()
    try:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sorteios (
                mensagem_id        BIGINT PRIMARY KEY,
                canal_id           BIGINT NOT NULL,
                guild_id           BIGINT NOT NULL,
                premio             TEXT NOT NULL,
                descricao          TEXT NOT NULL,
                ganhadores         INTEGER NOT NULL,
                requisito_id       BIGINT,
                criado_por         BIGINT NOT NULL,
                inicio             TIMESTAMPTZ NOT NULL,
                fim                TIMESTAMPTZ NOT NULL,
                finalizado         BOOLEAN NOT NULL DEFAULT FALSE,
                cancelado          BOOLEAN NOT NULL DEFAULT FALSE,
                participantes_ids  BIGINT[] NOT NULL DEFAULT '{}'
            );

            CREATE INDEX IF NOT EXISTS idx_sorteios_pendentes
                ON sorteios(fim) WHERE NOT finalizado AND NOT cancelado;
            """
        )
    finally:
        await conn.close()


async def criar_sorteio_db(**kwargs) -> None:
    await inicializar_banco_sorteios()
    conn = await _abrir_conexao()
    try:
        await conn.execute(
            """
            INSERT INTO sorteios
            (mensagem_id, canal_id, guild_id, premio, descricao, ganhadores,
             requisito_id, criado_por, inicio, fim)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            kwargs["mensagem_id"], kwargs["canal_id"], kwargs["guild_id"],
            kwargs["premio"], kwargs["descricao"], kwargs["ganhadores"],
            kwargs["requisito_id"], kwargs["criado_por"], kwargs["inicio"], kwargs["fim"],
        )
    finally:
        await conn.close()


async def obter_sorteio_db(mensagem_id: int) -> dict | None:
    conn = await _abrir_conexao()
    try:
        row = await conn.fetchrow("SELECT * FROM sorteios WHERE mensagem_id = $1", mensagem_id)
    finally:
        await conn.close()
    return dict(row) if row else None


async def obter_sorteios_pendentes_db() -> list[dict]:
    """Sorteios cujo prazo já passou e ainda não foram finalizados/cancelados."""
    conn = await _abrir_conexao()
    try:
        rows = await conn.fetch(
            "SELECT * FROM sorteios WHERE NOT finalizado AND NOT cancelado AND fim <= NOW()"
        )
    finally:
        await conn.close()
    return [dict(r) for r in rows]


async def obter_sorteios_ativos_db() -> list[dict]:
    """Sorteios ainda rolando (pra refresh periódico do embed)."""
    conn = await _abrir_conexao()
    try:
        rows = await conn.fetch(
            "SELECT * FROM sorteios WHERE NOT finalizado AND NOT cancelado AND fim > NOW()"
        )
    finally:
        await conn.close()
    return [dict(r) for r in rows]


async def adicionar_participante_db(mensagem_id: int, user_id: int):
    conn = await _abrir_conexao()
    try:
        await conn.execute(
            """
            UPDATE sorteios
            SET participantes_ids = array_append(participantes_ids, $2)
            WHERE mensagem_id = $1 AND NOT ($2 = ANY(participantes_ids))
            """,
            mensagem_id, user_id,
        )
    finally:
        await conn.close()


async def remover_participante_db(mensagem_id: int, user_id: int):
    conn = await _abrir_conexao()
    try:
        await conn.execute(
            """
            UPDATE sorteios
            SET participantes_ids = array_remove(participantes_ids, $2)
            WHERE mensagem_id = $1
            """,
            mensagem_id, user_id,
        )
    finally:
        await conn.close()


async def marcar_finalizado_db(mensagem_id: int):
    conn = await _abrir_conexao()
    try:
        await conn.execute("UPDATE sorteios SET finalizado = TRUE WHERE mensagem_id = $1", mensagem_id)
    finally:
        await conn.close()


async def marcar_cancelado_db(mensagem_id: int):
    conn = await _abrir_conexao()
    try:
        await conn.execute(
            "UPDATE sorteios SET cancelado = TRUE, finalizado = TRUE WHERE mensagem_id = $1",
            mensagem_id,
        )
    finally:
        await conn.close()


def _entradas_membro(membro: discord.Member) -> int:
    cargos_membro = {r.id for r in membro.roles}
    return 1 + sum(bonus for cargo_id, bonus in CARGOS_BONUS.items() if cargo_id in cargos_membro)


def _construir_pool(membros: list[discord.Member]) -> list[discord.Member]:
    pool = []
    for m in membros:
        pool.extend([m] * _entradas_membro(m))
    return pool


def _resolver_participantes(guild: discord.Guild, participantes_ids: list[int]) -> list[discord.Member]:
    membros = [guild.get_member(uid) for uid in participantes_ids]
    return [m for m in membros if m is not None]


def _sortear_unicos(pool: list[discord.Member], quantidade: int) -> list[discord.Member]:
    """Sorteia membros únicos a partir de uma pool com entradas duplicadas (ponderadas)."""
    vencedores = []
    pool_restante = pool.copy()
    ids_sorteados = set()

    while len(vencedores) < quantidade and pool_restante:
        escolhido = random.choice(pool_restante)
        if escolhido.id not in ids_sorteados:
            vencedores.append(escolhido)
            ids_sorteados.add(escolhido.id)
        pool_restante = [p for p in pool_restante if p.id not in ids_sorteados]

    return vencedores


def _barra_progresso(inicio: datetime, fim: datetime) -> str:
    agora = datetime.now(timezone.utc)
    total = (fim - inicio).total_seconds()
    decorrido = (agora - inicio).total_seconds()
    pct = min(max(decorrido / total, 0), 1.0) if total > 0 else 0
    cheios = int(pct * 10)
    vazios = 10 - cheios
    return f"`[{'█' * cheios}{'░' * vazios}]` `{int(pct * 100)}%`"


def _status_visual(sorteio: dict) -> tuple[int, str, str]:
    """Retorna (cor, chave_banner, texto_rodape) com base no estado atual do sorteio."""
    if sorteio["cancelado"]:
        return COR_VERMELHO, "cancelado", "Sorteio cancelado"
    if sorteio["finalizado"]:
        return COR_VERDE, "vencedor", "Sorteio encerrado"

    restante = (sorteio["fim"] - datetime.now(timezone.utc)).total_seconds()
    if restante <= LIMIAR_URGENCIA_SEGUNDOS:
        return COR_LARANJA, "ativo", "🔥 Últimos minutos — corra!"
    return COR_CUPHEAD, "ativo", "Sorteio em andamento"


def _resumo_bonus_compacto() -> str:
    if not CARGOS_BONUS:
        return "`Nenhum cargo bônus configurado`"
    return " • ".join(f"<@&{cid}> `+{b}`" for cid, b in CARGOS_BONUS.items())


def criar_embed_sorteio(sorteio: dict, guild: discord.Guild) -> discord.Embed:
    """
    NOVO: embed reformulado — antes tinha 8 campos com o requisito duplicado.
    Agora: descrição consolidada + 3 campos objetivos + cor que comunica o status,
    sem precisar de um campo de texto "Status" em bloco de código.
    """
    membros = _resolver_participantes(guild, sorteio["participantes_ids"])
    pool = _construir_pool(membros)

    requisito_role = guild.get_role(sorteio["requisito_id"]) if sorteio["requisito_id"] else None
    requisito_texto = requisito_role.mention if requisito_role else "Nenhum — todo mundo pode entrar"

    cor, banner_key, rodape_status = _status_visual(sorteio)

    embed = discord.Embed(
        title="🎰 SORTEIO • CUPHEAD CASINO",
        description=(
            f"**🎁 {sorteio['premio']}**\n"
            f"{sorteio['descricao']}\n\n"
            f"🎯 **Requisito:** {requisito_texto}\n"
            f"👑 **Ganhadores:** `{sorteio['ganhadores']}`"
        ),
        color=cor,
        timestamp=datetime.now(timezone.utc),
    )

    embed.add_field(
        name="📊 Participação",
        value=f"👤 `{len(membros)}` únicos • 🎟️ `{len(pool)}` entradas",
        inline=True,
    )
    embed.add_field(
        name="⏳ Encerra",
        value=f"<t:{int(sorteio['fim'].timestamp())}:R>",
        inline=True,
    )
    embed.add_field(
        name="📈 Progresso",
        value=_barra_progresso(sorteio["inicio"], sorteio["fim"]),
        inline=True,
    )
    embed.add_field(
        name="⭐ Cargos Bônus",
        value=_resumo_bonus_compacto(),
        inline=False,
    )

    embed.set_image(url=BANNERS[banner_key])
    embed.set_footer(text=f"Família Sant's • Cuphead Casino • {rodape_status}")
    return embed



async def _log_sorteio(bot: commands.Bot, guild: discord.Guild, titulo: str, descricao: str, cor: int):
    if not CANAL_LOG_SORTEIOS_ID:
        return
    canal = guild.get_channel(CANAL_LOG_SORTEIOS_ID)
    if not canal:
        return
    try:
        await canal.send(embed=discord.Embed(
            title=titulo, description=descricao, color=cor, timestamp=datetime.now(timezone.utc)
        ))
    except discord.HTTPException:
        pass


async def _buscar_mensagem(bot: commands.Bot, sorteio: dict) -> tuple[discord.Guild | None, discord.Message | None]:
    guild = bot.get_guild(sorteio["guild_id"])
    if not guild:
        return None, None
    canal = guild.get_channel(sorteio["canal_id"])
    if not canal:
        return guild, None
    try:
        msg = await canal.fetch_message(sorteio["mensagem_id"])
    except (discord.NotFound, discord.HTTPException):
        return guild, None
    return guild, msg


async def atualizar_embed_sorteio(bot: commands.Bot, mensagem_id: int):
    sorteio = await obter_sorteio_db(mensagem_id)
    if not sorteio or sorteio["finalizado"] or sorteio["cancelado"]:
        return
    guild, msg = await _buscar_mensagem(bot, sorteio)
    if not guild or not msg:
        return
    try:
        await msg.edit(embed=criar_embed_sorteio(sorteio, guild), view=SorteioView())
    except discord.HTTPException:
        pass


async def _animar_sorteio(canal: discord.TextChannel) -> discord.Message | None:
    try:
        msg = await canal.send("🎰 Iniciando o sorteio...")
        for frame in FRAMES_ANIMACAO:
            await msg.edit(content=frame)
            await asyncio.sleep(DELAY_FRAME)
        return msg
    except discord.HTTPException:
        return None


async def finalizar_sorteio(bot: commands.Bot, mensagem_id: int):
    sorteio = await obter_sorteio_db(mensagem_id)
    if not sorteio or sorteio["finalizado"] or sorteio["cancelado"]:
        return

    guild, msg = await _buscar_mensagem(bot, sorteio)
    if not guild or not msg:
        await marcar_finalizado_db(mensagem_id)  # canal/mensagem sumiu, não dá pra fazer mais nada
        return

    membros = _resolver_participantes(guild, sorteio["participantes_ids"])
    pool = _construir_pool(membros)
    unicos = len(set(p.id for p in pool))

    await marcar_finalizado_db(mensagem_id)
    sorteio["finalizado"] = True

    if unicos < sorteio["ganhadores"]:
        embed = discord.Embed(
            title="🎬 SORTEIO ENCERRADO",
            description=(
                "A roleta parou, mas não houve participantes suficientes.\n\n"
                f"🎁 **Prêmio:** {sorteio['premio']}\n"
                f"👥 **Participantes únicos:** `{unicos}`\n"
                f"👑 **Ganhadores necessários:** `{sorteio['ganhadores']}`"
            ),
            color=COR_VERMELHO,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_image(url=BANNERS["sem_ganho"])
        embed.set_footer(text="Família Sant's • Sem vencedores")
        try:
            await msg.edit(embed=embed, view=None)
        except discord.HTTPException:
            pass
        await _log_sorteio(bot, guild, "🎬 Sorteio sem vencedores", f"**{sorteio['premio']}** não teve participantes suficientes.", COR_VERMELHO)
        return

    msg_anim = await _animar_sorteio(msg.channel)

    vencedores = _sortear_unicos(pool, sorteio["ganhadores"])
    mencoes = ", ".join(v.mention for v in vencedores)

    embed = discord.Embed(
        title="🏆 RESULTADO DO SORTEIO • CUPHEAD CASINO",
        description=(
            "A roleta parou e a sorte escolheu os seus eleitos.\n\n"
            f"🎁 **Prêmio:** {sorteio['premio']}\n\n"
            f"👑 **Vencedor(es):**\n{mencoes}\n\n"
            f"🎟️ **Participantes únicos:** `{unicos}`\n"
            f"📊 **Entradas totais:** `{len(pool)}`\n\n"
            "☕ Obrigado a todos que participaram!"
        ),
        color=COR_VERDE,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_image(url=BANNERS["vencedor"])
    embed.set_footer(text="Família Sant's • Cuphead Casino")

    try:
        await msg.edit(embed=embed, view=None)
    except discord.HTTPException:
        pass

    if msg_anim:
        try:
            await msg_anim.delete()
        except discord.HTTPException:
            pass

    try:
        await msg.reply(
            f"🏆 Parabéns {mencoes}! "
            f"{'Você venceu' if sorteio['ganhadores'] == 1 else 'Vocês venceram'} "
            f"o sorteio de **{sorteio['premio']}**! 🎉"
        )
    except discord.HTTPException:
        pass

    await _log_sorteio(
        bot, guild, "🏆 Sorteio finalizado",
        f"**{sorteio['premio']}** — vencedor(es): {mencoes}", COR_VERDE,
    )


async def cancelar_sorteio(bot: commands.Bot, mensagem_id: int):
    sorteio = await obter_sorteio_db(mensagem_id)
    if not sorteio or sorteio["finalizado"] or sorteio["cancelado"]:
        return

    guild, msg = await _buscar_mensagem(bot, sorteio)
    await marcar_cancelado_db(mensagem_id)

    if not guild or not msg:
        return

    embed = discord.Embed(
        title="❌ SORTEIO CANCELADO",
        description=(
            "A rodada foi encerrada pela equipe antes do prazo.\n\n"
            f"🎁 **Prêmio:** {sorteio['premio']}\n"
            f"🎟️ **Participantes:** `{len(sorteio['participantes_ids'])}`\n\n"
            "*Fique atento aos próximos sorteios!*"
        ),
        color=COR_VERMELHO,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_image(url=BANNERS["cancelado"])
    embed.set_footer(text="Família Sant's • Sorteio cancelado")

    try:
        await msg.edit(embed=embed, view=None)
    except discord.HTTPException:
        pass

    await _log_sorteio(bot, guild, "❌ Sorteio cancelado", f"**{sorteio['premio']}** foi cancelado.", COR_VERMELHO)


async def reroll_sorteio(bot: commands.Bot, mensagem_id: int) -> list[discord.Member] | None:
    """Retorna a lista de novos vencedores, ou None se não for possível rerolar."""
    sorteio = await obter_sorteio_db(mensagem_id)
    if not sorteio or not sorteio["finalizado"] or sorteio["cancelado"]:
        return None

    guild, msg = await _buscar_mensagem(bot, sorteio)
    if not guild or not msg:
        return None

    membros = _resolver_participantes(guild, sorteio["participantes_ids"])
    pool = _construir_pool(membros)
    if len(set(p.id for p in pool)) < sorteio["ganhadores"]:
        return None

    msg_anim = await _animar_sorteio(msg.channel)
    vencedores = _sortear_unicos(pool, sorteio["ganhadores"])

    if msg_anim:
        mencoes = ", ".join(v.mention for v in vencedores)
        embed = discord.Embed(
            title="🎲 REROLL • CUPHEAD CASINO",
            description=(
                "A roleta girou novamente e um novo destino foi traçado.\n\n"
                f"🎁 **Prêmio:** {sorteio['premio']}\n"
                f"👑 **Novo(s) vencedor(es):** {mencoes}"
            ),
            color=COR_DOURADA,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_image(url=BANNERS["reroll"])
        embed.set_footer(text="Família Sant's • Cuphead Casino")
        try:
            await msg_anim.edit(content=None, embed=embed)
        except discord.HTTPException:
            pass

    return vencedores


def _tem_admin_sorteio(membro: discord.Member) -> bool:
    return membro.guild_permissions.administrator or any(
        cargo.id in CARGOS_ADMIN_SORTEIO for cargo in membro.roles
    )


class SorteioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Entrar no Sorteio", emoji="🎟️", style=discord.ButtonStyle.success,
                        custom_id="sorteio_v2_participar", row=0)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        sorteio = await obter_sorteio_db(interaction.message.id)
        if not sorteio or sorteio["finalizado"] or sorteio["cancelado"]:
            return await interaction.response.send_message("🎬 Este sorteio já foi encerrado.", ephemeral=True)

        if datetime.now(timezone.utc) >= sorteio["fim"]:
            return await interaction.response.send_message("⏳ O prazo deste sorteio já acabou.", ephemeral=True)

        if sorteio["requisito_id"]:
            cargos_membro = {r.id for r in interaction.user.roles}
            if sorteio["requisito_id"] not in cargos_membro:
                role = interaction.guild.get_role(sorteio["requisito_id"])
                nome_cargo = role.mention if role else "necessário"
                return await interaction.response.send_message(
                    f"❌ Você precisa do cargo {nome_cargo} para participar.", ephemeral=True
                )

        if interaction.user.id in sorteio["participantes_ids"]:
            return await interaction.response.send_message("🎟️ Você já está participando deste sorteio.", ephemeral=True)

        await adicionar_participante_db(interaction.message.id, interaction.user.id)

        entradas = _entradas_membro(interaction.user)
        bonus = entradas - 1
        msg_bonus = f"\n✨ **Bônus de cargo aplicado!** Você tem `{entradas}` entradas no total." if bonus > 0 else ""

        await interaction.response.send_message(f"🎰 Você entrou no sorteio! Boa sorte!{msg_bonus}", ephemeral=True)
        await atualizar_embed_sorteio(interaction.client, interaction.message.id)

    @discord.ui.button(label="Sair do Sorteio", emoji="🚪", style=discord.ButtonStyle.secondary,
                        custom_id="sorteio_v2_sair", row=0)
    async def sair(self, interaction: discord.Interaction, button: discord.ui.Button):
        sorteio = await obter_sorteio_db(interaction.message.id)
        if not sorteio or sorteio["finalizado"] or sorteio["cancelado"]:
            return await interaction.response.send_message("🎬 Este sorteio já foi encerrado.", ephemeral=True)

        if interaction.user.id not in sorteio["participantes_ids"]:
            return await interaction.response.send_message("🚪 Você não está participando.", ephemeral=True)

        await remover_participante_db(interaction.message.id, interaction.user.id)
        await interaction.response.send_message("🚪 Você saiu do sorteio.", ephemeral=True)
        await atualizar_embed_sorteio(interaction.client, interaction.message.id)

    @discord.ui.button(label="Minhas Entradas", emoji="📋", style=discord.ButtonStyle.primary,
                        custom_id="sorteio_v2_minhas_entradas", row=0)
    async def minhas_entradas(self, interaction: discord.Interaction, button: discord.ui.Button):
        sorteio = await obter_sorteio_db(interaction.message.id)
        if not sorteio:
            return await interaction.response.send_message("❌ Sorteio não encontrado.", ephemeral=True)

        participando = interaction.user.id in sorteio["participantes_ids"]
        entradas = _entradas_membro(interaction.user) if participando else 0
        bonus = entradas - 1 if participando else 0

        membros = _resolver_participantes(interaction.guild, sorteio["participantes_ids"])
        pool = _construir_pool(membros)
        chance = f"`{(entradas / len(pool) * 100):.1f}%`" if pool and participando else "`0%`"

        cargos_ativos = [
            f"<@&{cid}> (`+{b}` entrada(s))"
            for cid, b in CARGOS_BONUS.items()
            if any(c.id == cid for c in interaction.user.roles)
        ]

        embed = discord.Embed(title="📋 Suas Entradas", color=COR_CUPHEAD, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="✅ Participando", value="`Sim`" if participando else "`Não`", inline=True)
        embed.add_field(name="🎟️ Entradas", value=f"`{entradas}`", inline=True)
        embed.add_field(name="📈 Chance estimada", value=chance, inline=True)
        embed.add_field(
            name="⭐ Cargos bônus ativos",
            value="\n".join(cargos_ativos) if cargos_ativos else "`Nenhum`",
            inline=False,
        )
        embed.set_footer(text="Família Sant's • Cuphead Casino")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Painel Admin", emoji="⚙️", style=discord.ButtonStyle.danger,
                        custom_id="sorteio_v2_admin", row=1)
    async def admin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _tem_admin_sorteio(interaction.user):
            return await interaction.response.send_message("❌ Você não pode acessar este painel.", ephemeral=True)

        await interaction.response.send_message(
            "⚙️ Painel administrativo do sorteio:",
            view=AdminSorteioView(interaction.message.id),
            ephemeral=True,
        )


class AdminSorteioView(discord.ui.View):
    """Painel ephemeral — não precisa ser persistente, é recriado a cada clique em 'Painel Admin'."""

    def __init__(self, mensagem_id: int):
        super().__init__(timeout=300)
        self.mensagem_id = mensagem_id

    @discord.ui.button(label="Participantes", emoji="👥", style=discord.ButtonStyle.primary)
    async def ver_participantes(self, interaction: discord.Interaction, button: discord.ui.Button):
        sorteio = await obter_sorteio_db(self.mensagem_id)
        if not sorteio:
            return await interaction.response.send_message("❌ Sorteio não encontrado.", ephemeral=True)

        membros = _resolver_participantes(interaction.guild, sorteio["participantes_ids"])
        pool = _construir_pool(membros)

        if not membros:
            texto = "Nenhum participante entrou neste sorteio ainda."
        else:
            linhas = []
            for i, m in enumerate(membros[:50]):
                entradas = _entradas_membro(m)
                bonus = entradas - 1
                sufixo = f" `+{bonus} bônus`" if bonus > 0 else ""
                linhas.append(f"`{i + 1}.` {m.mention} — 🎟️ `{entradas}`{sufixo}")
            texto = "\n".join(linhas)
            if len(membros) > 50:
                texto += f"\n\n*+ `{len(membros) - 50}` participante(s)...*"

        embed = discord.Embed(title="👥 Participantes do Sorteio", description=texto,
                               color=COR_CUPHEAD, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="📊 Totais", value=f"👤 **Únicos:** `{len(membros)}`\n🎟️ **Entradas totais:** `{len(pool)}`")
        embed.set_footer(text="Família Sant's • Painel Admin")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Estatísticas", emoji="📊", style=discord.ButtonStyle.primary)
    async def estatisticas(self, interaction: discord.Interaction, button: discord.ui.Button):
        sorteio = await obter_sorteio_db(self.mensagem_id)
        if not sorteio:
            return await interaction.response.send_message("❌ Sorteio não encontrado.", ephemeral=True)

        membros = _resolver_participantes(interaction.guild, sorteio["participantes_ids"])
        pool = _construir_pool(membros)
        contagem = Counter(p.id for p in pool)
        top3 = contagem.most_common(3)

        tempo_restante = max(sorteio["fim"] - datetime.now(timezone.utc), timedelta(0))
        horas, resto = divmod(int(tempo_restante.total_seconds()), 3600)
        minutos = resto // 60

        top_texto = "\n".join(
            f"`{i + 1}.` <@{uid}> — 🎟️ `{qtd}`" for i, (uid, qtd) in enumerate(top3)
        ) if top3 else "Nenhum participante ainda."

        embed = discord.Embed(title="📊 Estatísticas do Sorteio", color=COR_ROXO, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="🎁 Prêmio", value=sorteio["premio"], inline=False)
        embed.add_field(name="👤 Participantes únicos", value=f"`{len(membros)}`", inline=True)
        embed.add_field(name="🎟️ Entradas totais", value=f"`{len(pool)}`", inline=True)
        embed.add_field(name="👑 Ganhadores", value=f"`{sorteio['ganhadores']}`", inline=True)
        embed.add_field(name="⏳ Tempo restante", value=f"`{horas}h {minutos}m`", inline=True)
        embed.add_field(name="🏆 Top entradas", value=top_texto, inline=False)
        embed.set_footer(text="Família Sant's • Painel Admin")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Reroll", emoji="🎲", style=discord.ButtonStyle.secondary)
    async def reroll(self, interaction: discord.Interaction, button: discord.ui.Button):
        sorteio = await obter_sorteio_db(self.mensagem_id)
        if not sorteio or not sorteio["finalizado"] or sorteio["cancelado"]:
            return await interaction.response.send_message(
                "❌ O reroll só pode ser feito após o sorteio ser finalizado.", ephemeral=True
            )

        await interaction.response.defer()
        vencedores = await reroll_sorteio(interaction.client, self.mensagem_id)
        if vencedores is None:
            await interaction.followup.send("❌ Não há participantes únicos suficientes para reroll.", ephemeral=True)
        else:
            await interaction.followup.send("🎲 Reroll concluído!", ephemeral=True)

    @discord.ui.button(label="Finalizar", emoji="🏁", style=discord.ButtonStyle.success)
    async def finalizar(self, interaction: discord.Interaction, button: discord.ui.Button):
        sorteio = await obter_sorteio_db(self.mensagem_id)
        if not sorteio or sorteio["finalizado"] or sorteio["cancelado"]:
            return await interaction.response.send_message("❌ Este sorteio já foi finalizado.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        await finalizar_sorteio(interaction.client, self.mensagem_id)
        await interaction.followup.send("🏁 Sorteio finalizado com sucesso.", ephemeral=True)

    @discord.ui.button(label="Cancelar", emoji="❌", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        sorteio = await obter_sorteio_db(self.mensagem_id)
        if not sorteio or sorteio["finalizado"] or sorteio["cancelado"]:
            return await interaction.response.send_message("❌ Este sorteio já foi encerrado.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        await cancelar_sorteio(interaction.client, self.mensagem_id)
        await interaction.followup.send("❌ Sorteio cancelado com sucesso.", ephemeral=True)


class Sorteio(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.loop.create_task(inicializar_banco_sorteios())
        bot.add_view(SorteioView())  # NOVO: registro persistente — sobrevive a restart
        self.checar_sorteios_finalizados.start()
        self.atualizar_embeds_ativos.start()

    def cog_unload(self):
        self.checar_sorteios_finalizados.cancel()
        self.atualizar_embeds_ativos.cancel()

    # NOVO: substitui o antigo `await asyncio.sleep(tempo_segundos)` dentro do
    # comando — que travava a interação por até 90 dias e morria a cada restart.
    @tasks.loop(seconds=INTERVALO_CHECAGEM_SEGUNDOS)
    async def checar_sorteios_finalizados(self):
        try:
            pendentes = await obter_sorteios_pendentes_db()
        except Exception as e:
            logger.warning(f"Falha ao checar sorteios pendentes: {e}")
            return
        for sorteio in pendentes:
            try:
                await finalizar_sorteio(self.bot, sorteio["mensagem_id"])
            except Exception as e:
                logger.error(f"Erro ao finalizar sorteio {sorteio['mensagem_id']}: {e}", exc_info=True)

    @checar_sorteios_finalizados.before_loop
    async def before_checar(self):
        await self.bot.wait_until_ready()

    # NOVO: mantém a barra de progresso e o contador de tempo sempre atuais,
    # mesmo que ninguém entre/saia do sorteio por um tempo.
    @tasks.loop(minutes=INTERVALO_REFRESH_MINUTOS)
    async def atualizar_embeds_ativos(self):
        try:
            ativos = await obter_sorteios_ativos_db()
        except Exception as e:
            logger.warning(f"Falha ao buscar sorteios ativos: {e}")
            return
        for sorteio in ativos:
            try:
                await atualizar_embed_sorteio(self.bot, sorteio["mensagem_id"])
            except Exception as e:
                logger.warning(f"Erro ao atualizar embed do sorteio {sorteio['mensagem_id']}: {e}")

    @atualizar_embeds_ativos.before_loop
    async def before_atualizar(self):
        await self.bot.wait_until_ready()

    @app_commands.command(
        name="sorteio",
        description="🎰 Cria um sorteio profissional no tema Cuphead Casino."
    )
    @app_commands.describe(
        premio="Prêmio do sorteio",
        descricao="Descrição detalhada do prêmio",
        ganhadores="Quantidade de ganhadores",
        data="Data de encerramento (Ex: 31/05/2026)",
        hora="Hora de encerramento (Ex: 18:00)",
        requisito="Cargo obrigatório para participar (opcional)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def sorteio(
        self,
        interaction: discord.Interaction,
        premio: str,
        descricao: str,
        ganhadores: int,
        data: str,
        hora: str,
        requisito: discord.Role = None
    ):
        if ganhadores <= 0:
            return await interaction.response.send_message(
                "❌ A quantidade de ganhadores precisa ser maior que 0.", ephemeral=True
            )

        try:
            data_hora = datetime.strptime(f"{data} {hora}", "%d/%m/%Y %H:%M")
            data_hora = data_hora.replace(tzinfo=timezone.utc)
        except ValueError:
            return await interaction.response.send_message(
                "❌ Formato inválido.\n\n📅 **Data:** `31/05/2026`\n🕒 **Hora:** `18:00`",
                ephemeral=True
            )

        agora = datetime.now(timezone.utc)

        if data_hora <= agora:
            return await interaction.response.send_message(
                "❌ Você não pode criar sorteios no passado.", ephemeral=True
            )

        if (data_hora - agora) > timedelta(days=90):
            return await interaction.response.send_message(
                "❌ O sorteio não pode ultrapassar 90 dias.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        sorteio_temp = {
            "premio": premio, "descricao": descricao, "ganhadores": ganhadores,
            "requisito_id": requisito.id if requisito else None,
            "participantes_ids": [], "inicio": agora, "fim": data_hora,
            "finalizado": False, "cancelado": False,
        }
        mensagem = await interaction.channel.send(
            embed=criar_embed_sorteio(sorteio_temp, interaction.guild),
            view=SorteioView(),
        )

        await criar_sorteio_db(
            mensagem_id=mensagem.id,
            canal_id=interaction.channel.id,
            guild_id=interaction.guild.id,
            premio=premio,
            descricao=descricao,
            ganhadores=ganhadores,
            requisito_id=requisito.id if requisito else None,
            criado_por=interaction.user.id,
            inicio=agora,
            fim=data_hora,
        )

        await interaction.followup.send(
            f"🎰 Sorteio **{premio}** criado com sucesso! Encerrará <t:{int(data_hora.timestamp())}:R>.",
            ephemeral=True
        )

    @sorteio.error
    async def sorteio_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        msg = "❌ Apenas administradores podem criar sorteios."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(
        name="sorteios-ativos",
        description="📋 Lista todos os sorteios em andamento no servidor."
    )
    async def sorteios_ativos(self, interaction: discord.Interaction):
        if not _tem_admin_sorteio(interaction.user):
            return await interaction.response.send_message(
                "❌ Apenas a equipe pode consultar os sorteios ativos.", ephemeral=True
            )

        ativos = [s for s in await obter_sorteios_ativos_db() if s["guild_id"] == interaction.guild.id]

        if not ativos:
            return await interaction.response.send_message("📭 Nenhum sorteio ativo no momento.", ephemeral=True)

        linhas = []
        for s in sorted(ativos, key=lambda x: x["fim"]):
            linhas.append(
                f"🎁 **{s['premio']}** — `{len(s['participantes_ids'])}` participantes • "
                f"encerra <t:{int(s['fim'].timestamp())}:R> • "
                f"[ir para a mensagem](https://discord.com/channels/{s['guild_id']}/{s['canal_id']}/{s['mensagem_id']})"
            )

        embed = discord.Embed(
            title="📋 Sorteios Ativos",
            description="\n\n".join(linhas),
            color=COR_CUPHEAD,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text="Família Sant's • Cuphead Casino")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Sorteio(bot))
    logger.info("Cog Sorteio carregado com sucesso.")