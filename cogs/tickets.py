import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timezone
import asyncio
import re
import logging
import aiohttp
import os
import asyncpg

logger = logging.getLogger("tickets")



class CONFIG:

    CATEGORIA_TICKETS_ID = 1525269670859374723
    CANAL_LOG_ID         = 1525644381313306714
    CANAL_AVALIACOES_ID  = 1525643925489062029

    DATABASE_URL = os.getenv("DATABASE_URL")

    CARGOS_ATENDIMENTO_IDS: list[int] = [
        1525281649284349962,
    ]

    CARGOS_CHAMAR_STAFF: list[int] = [
        1525281649284349962,
    ]

    CARGOS_POR_CATEGORIA: dict[str, list[int]] = {
        "duvida":     [],
        "denuncia":   [],
        "patrocinio": [1509054988972851252, 1502717285528506536],
        "outros":     [],
    }

    COOLDOWN_CHAMAR_STAFF_SEGUNDOS = 100
    COOLDOWN_ABRIR_TICKET_SEGUNDOS = 10

    BANNER_PAINEL  = "https://cdn.discordapp.com/attachments/961677475191078992/1525639971480797255/content.png?ex=6a541e72&is=6a52ccf2&hm=13773293d43c75670a5d1423b47677bfd9f233872305a1988890e39c300fc7e3&"
    BANNER_FECHADO = "https://cdn.discordapp.com/attachments/961677475191078992/1518143942388879450/content.png?ex=6a38d939&is=6a3787b9&hm=56325c5f006840bc4ad1234c7b943879d4a4c90e0656841f90b7757ad6b6e0e5&"

    IMAGENS: dict[str, str] = {
        "duvida":     "",
        "denuncia":   "",
        "patrocinio": "",
        "outros":     "",
    }

    THUMBNAILS: dict[str, str] = {
        "duvida":     "",
        "denuncia":   "",
        "patrocinio": "",
        "outros":     "",
    }
    COR_VERMELHO = discord.Color.from_rgb(210, 60,  75)    #  alertas / denúncias / SLA crítico
    COR_AZUL     = discord.Color.from_rgb(64,  156, 255)   #  gelo elétrico — cor de assinatura
    COR_DOURADO  = discord.Color.from_rgb(120, 210, 255)   #  cristal de gelo (destaques, avaliações)
    COR_VERDE    = discord.Color.from_rgb(72,  219, 176)   #  em atendimento / sucesso
    COR_ROXO     = discord.Color.from_rgb(122, 108, 230)   #  aurora boreal (staff / notas internas)
    COR_ESCURO   = discord.Color.from_rgb(9,   14,  34)    #  noite polar (avisos neutros)
    COR_CINZA    = discord.Color.from_rgb(88,  108, 140)   #  neutro / concluído
    COR_AMARELO  = discord.Color.from_rgb(255, 196, 90)    #  aviso de SLA

    CATEGORIAS: dict[str, dict] = {
        "duvida": {
            "label":       "Dúvidas",
            "description": "Tire suas dúvidas com a equipe.",
            "emoji":       "❄️",
            "titulo":      "❄️ Dúvidas — Posto de Orientação",
            "nivel":       "🔵 Suporte Geral",
            "cor":         discord.Color.from_rgb(64, 156, 255),
            "nome_canal":  "duvida",
        },
        "denuncia": {
            "label":       "Denúncias",
            "description": "Reporte algo irregular com provas.",
            "emoji":       "🚨",
            "titulo":      "🚨 Denúncia — Alerta na Nevasca",
            "nivel":       "🔴 Prioridade Alta",
            "cor":         discord.Color.from_rgb(210, 60, 75),
            "nome_canal":  "denuncia",
        },
        "patrocinio": {
            "label":       "Patrocínios",
            "description": "Parcerias e propostas comerciais.",
            "emoji":       "🌌",
            "titulo":      "🌌 Patrocínio — Embaixada da Aurora",
            "nivel":       "🟡 Proposta Comercial",
            "cor":         discord.Color.from_rgb(122, 108, 230),
            "nome_canal":  "patrocinio",
        },
        "outros": {
            "label":       "Outros",
            "description": "Assuntos que não se encaixam acima.",
            "emoji":       "🐺",
            "titulo":      "🐺 Outros — Toca da Matilha",
            "nivel":       "⚪ Atendimento Geral",
            "cor":         discord.Color.from_rgb(88, 108, 140),
            "nome_canal":  "outros",
        },
    }

    SLA_AVISO_MINUTOS   = 10   
    SLA_CRITICO_MINUTOS = 25  

    CARGOS_PATENTES: dict[str, int] = {
        "Lobo Errante":       0,
        "Batedor de Gelo":    0,
        "Guardião Glacial":   0,
        "Alfa da Matilha":    0,
        "Lenda de FrostNova": 0,
    }
    CANAL_ANUNCIO_PATENTES_ID = CANAL_AVALIACOES_ID

    REABERTURA_JANELA_HORAS = 24

    INATIVIDADE_AVISO_HORAS      = 5
    INATIVIDADE_FECHAMENTO_HORAS = 2


PATENTE_EMOJI: dict[str, str] = {
    "Lobo Errante":       "🐾",
    "Batedor de Gelo":    "❄️",
    "Guardião Glacial":   "🛡️",
    "Alfa da Matilha":    "🐺",
    "Lenda de FrostNova": "🌌",
}


def slug(texto: str) -> str:
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9\-]", "-", texto)
    texto = re.sub(r"-{2,}", "-", texto)
    return texto.strip("-")[:80]


def tem_permissao(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(r.id in CONFIG.CARGOS_ATENDIMENTO_IDS for r in member.roles)


def tem_permissao_categoria(member: discord.Member, tipo: str) -> bool:
    if tem_permissao(member):
        return True
    cargos_cat = CONFIG.CARGOS_POR_CATEGORIA.get(tipo, [])
    return any(r.id in cargos_cat for r in member.roles)


def formatar_duracao(segundos: int) -> str:
    if segundos < 0:
        segundos = 0
    m, s = divmod(segundos, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    partes = []
    if d: partes.append(f"{d}d")
    if h: partes.append(f"{h}h")
    if m: partes.append(f"{m}min")
    if not partes: partes.append(f"{s}s")
    return " ".join(partes)


def _extrair_dono_id(topic: str) -> int | None:
    match = re.search(r"DONO:(\d+)", topic)
    return int(match.group(1)) if match else None


def _extrair_tipo_ticket(topic: str) -> str | None:
    match = re.search(r"Tipo:\s*(\w+)", topic)
    return match.group(1) if match else None


def _extrair_atendente_id(topic: str) -> int | None:
    match = re.search(r"ATENDENTE:(\d+)", topic)
    return int(match.group(1)) if match else None


def _extrair_msg_id(topic: str) -> int | None:
    match = re.search(r"MSGID:(\d+)", topic)
    return int(match.group(1)) if match else None


def _marcar_atendente_no_topic(topic: str, staff_id: int) -> str:
    if "ATENDENTE:" in topic:
        return re.sub(r"ATENDENTE:\d+", f"ATENDENTE:{staff_id}", topic)
    return f"{topic} | ATENDENTE:{staff_id}"


def _estrelas(nota: int) -> str:
    nota = max(1, min(5, int(nota)))
    return "⭐" * nota + "☆" * (5 - nota)


def _classificacao_media(media: float) -> str:
    if media >= 4.8:
        return "🏆 Atendimento Elite"
    if media >= 4.5:
        return "💎 Excelente"
    if media >= 4.0:
        return "✅ Muito bom"
    if media >= 3.0:
        return "⚠️ Regular"
    return "🚨 Precisa de atenção"


def calcular_patente(media: float, total: int) -> str:
    """Calcula a patente do atendente com base na média e volume de avaliações."""
    if total < 5:
        return "Lobo Errante"
    if media >= 4.9 and total >= 20:
        return "Lenda de FrostNova"
    if media >= 4.7:
        return "Alfa da Matilha"
    if media >= 4.2:
        return "Guardião Glacial"
    if media >= 3.5:
        return "Batedor de Gelo"
    return "Lobo Errante"


async def _abrir_conexao_postgres() -> asyncpg.Connection:
    if not CONFIG.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não configurada. Adicione no .env: "
            "DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_do_banco"
        )
    return await asyncpg.connect(CONFIG.DATABASE_URL)


async def inicializar_banco_avaliacoes():
    conn = await _abrir_conexao_postgres()
    try:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_avaliacoes (
                ticket_id BIGINT PRIMARY KEY,
                ticket_nome TEXT NOT NULL,
                guild_id BIGINT NOT NULL,
                usuario_id BIGINT NOT NULL,
                atendente_id BIGINT NOT NULL,
                nota INTEGER NOT NULL CHECK(nota BETWEEN 1 AND 5),
                transcript_url TEXT,
                criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_ticket_avaliacoes_atendente
                ON ticket_avaliacoes(atendente_id);

            ALTER TABLE ticket_avaliacoes ADD COLUMN IF NOT EXISTS comentario TEXT;

            -- NOVO: patente atual de cada atendente (para detectar mudança de patente)
            CREATE TABLE IF NOT EXISTS atendentes_patentes (
                atendente_id  BIGINT PRIMARY KEY,
                patente_atual TEXT NOT NULL DEFAULT 'Lobo Errante',
                atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            -- NOVO: histórico de fechamento recente, usado pela reabertura via DM
            CREATE TABLE IF NOT EXISTS ticket_fechados_recentes (
                usuario_id     BIGINT PRIMARY KEY,
                guild_id       BIGINT NOT NULL,
                tipo           TEXT,
                atendente_id   BIGINT,
                ticket_nome    TEXT,
                transcript_url TEXT,
                fechado_em     TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS ticket_notas_internas (
                id          BIGSERIAL PRIMARY KEY,
                channel_id  BIGINT NOT NULL,
                autor_id    BIGINT NOT NULL,
                conteudo    TEXT NOT NULL,
                criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_ticket_notas_channel
                ON ticket_notas_internas(channel_id, criado_em DESC);

            CREATE TABLE IF NOT EXISTS ticket_timeline (
                id          BIGSERIAL PRIMARY KEY,
                channel_id  BIGINT NOT NULL,
                autor_id    BIGINT,
                evento      TEXT NOT NULL,
                criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_ticket_timeline_channel
                ON ticket_timeline(channel_id, criado_em ASC);

            -- NOVO: tempo de primeira resposta (criação do ticket -> "Assumir"), por atendente
            CREATE TABLE IF NOT EXISTS ticket_tempo_resposta (
                channel_id    BIGINT PRIMARY KEY,
                atendente_id  BIGINT NOT NULL,
                segundos      INTEGER NOT NULL,
                criado_em     TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_ticket_tempo_resposta_atendente
                ON ticket_tempo_resposta(atendente_id);
            """
        )
    finally:
        await conn.close()


async def salvar_tempo_resposta(channel_id: int, atendente_id: int, segundos: int):
    """NOVO: registra quanto tempo levou até um atendente assumir o ticket pela primeira vez."""
    await inicializar_banco_avaliacoes()
    conn = await _abrir_conexao_postgres()
    try:
        await conn.execute(
            """
            INSERT INTO ticket_tempo_resposta (channel_id, atendente_id, segundos, criado_em)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (channel_id) DO NOTHING
            """,
            channel_id,
            atendente_id,
            max(0, segundos),
        )
    finally:
        await conn.close()


async def obter_tempo_resposta_medio(atendente_id: int) -> int | None:
    """NOVO: tempo médio (em segundos) de primeira resposta de um atendente. None se não há dados."""
    await inicializar_banco_avaliacoes()
    conn = await _abrir_conexao_postgres()
    try:
        row = await conn.fetchrow(
            "SELECT AVG(segundos) AS media FROM ticket_tempo_resposta WHERE atendente_id = $1",
            atendente_id,
        )
    finally:
        await conn.close()
    if not row or row["media"] is None:
        return None
    return int(row["media"])


async def salvar_avaliacao_ticket(
    *,
    ticket_id: int,
    ticket_nome: str,
    guild_id: int,
    usuario_id: int,
    atendente_id: int,
    nota: int,
    transcript_url: str | None,
    comentario: str | None = None,
):
    await inicializar_banco_avaliacoes()
    conn = await _abrir_conexao_postgres()
    try:
        await conn.execute(
            """
            INSERT INTO ticket_avaliacoes
            (ticket_id, ticket_nome, guild_id, usuario_id, atendente_id, nota, transcript_url, comentario, criado_em)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
            ON CONFLICT (ticket_id) DO UPDATE SET
                ticket_nome = EXCLUDED.ticket_nome,
                guild_id = EXCLUDED.guild_id,
                usuario_id = EXCLUDED.usuario_id,
                atendente_id = EXCLUDED.atendente_id,
                nota = EXCLUDED.nota,
                transcript_url = EXCLUDED.transcript_url,
                comentario = EXCLUDED.comentario,
                criado_em = NOW()
            """,
            ticket_id,
            ticket_nome,
            guild_id,
            usuario_id,
            atendente_id,
            nota,
            transcript_url,
            comentario,
        )
    finally:
        await conn.close()


async def obter_resumo_atendente(atendente_id: int) -> tuple[float, int]:
    await inicializar_banco_avaliacoes()
    conn = await _abrir_conexao_postgres()
    try:
        row = await conn.fetchrow(
            """
            SELECT COALESCE(AVG(nota), 0) AS media, COUNT(*) AS total
            FROM ticket_avaliacoes
            WHERE atendente_id = $1
            """,
            atendente_id,
        )
    finally:
        await conn.close()

    media = float(row["media"] or 0)
    total = int(row["total"] or 0)
    return media, total


async def obter_ranking_atendentes(limite: int = 10) -> list[tuple[int, float, int]]:
    await inicializar_banco_avaliacoes()
    conn = await _abrir_conexao_postgres()
    try:
        rows = await conn.fetch(
            """
            SELECT atendente_id, AVG(nota) AS media, COUNT(*) AS total
            FROM ticket_avaliacoes
            GROUP BY atendente_id
            HAVING COUNT(*) > 0
            ORDER BY media DESC, total DESC
            LIMIT $1
            """,
            limite,
        )
    finally:
        await conn.close()

    return [(int(r["atendente_id"]), float(r["media"]), int(r["total"])) for r in rows]


async def obter_comentarios_recentes_atendente(atendente_id: int, limite: int = 5) -> list[dict]:
    """NOVO: últimos comentários deixados para um atendente (usado em painéis administrativos)."""
    await inicializar_banco_avaliacoes()
    conn = await _abrir_conexao_postgres()
    try:
        rows = await conn.fetch(
            """
            SELECT nota, comentario, criado_em
            FROM ticket_avaliacoes
            WHERE atendente_id = $1 AND comentario IS NOT NULL AND comentario <> ''
            ORDER BY criado_em DESC
            LIMIT $2
            """,
            atendente_id,
            limite,
        )
    finally:
        await conn.close()
    return [dict(r) for r in rows]


async def obter_patente_atual_db(atendente_id: int) -> str:
    await inicializar_banco_avaliacoes()
    conn = await _abrir_conexao_postgres()
    try:
        row = await conn.fetchrow(
            "SELECT patente_atual FROM atendentes_patentes WHERE atendente_id = $1",
            atendente_id,
        )
    finally:
        await conn.close()
    return row["patente_atual"] if row else "Lobo Errante"


async def atualizar_patente_db(atendente_id: int, nova_patente: str):
    conn = await _abrir_conexao_postgres()
    try:
        await conn.execute(
            """
            INSERT INTO atendentes_patentes (atendente_id, patente_atual, atualizado_em)
            VALUES ($1, $2, NOW())
            ON CONFLICT (atendente_id) DO UPDATE SET
                patente_atual = EXCLUDED.patente_atual,
                atualizado_em = NOW()
            """,
            atendente_id,
            nova_patente,
        )
    finally:
        await conn.close()


async def sincronizar_patente_atendente(bot: commands.Bot, guild: discord.Guild, atendente_id: int) -> str | None:
    """
    Recalcula a patente do atendente. Retorna o nome da nova patente se ela mudou
    (e já atualiza o cargo no Discord), ou None se não houve mudança.
    """
    media, total = await obter_resumo_atendente(atendente_id)
    nova = calcular_patente(media, total)
    anterior = await obter_patente_atual_db(atendente_id)

    if nova == anterior:
        return None

    await atualizar_patente_db(atendente_id, nova)

    member = guild.get_member(atendente_id)
    if member:
        for nome_patente, role_id in CONFIG.CARGOS_PATENTES.items():
            if not role_id:
                continue
            role = guild.get_role(role_id)
            if role and role in member.roles and nome_patente != nova:
                try:
                    await member.remove_roles(role, reason="Atualização automática de patente")
                except discord.HTTPException:
                    pass

        novo_role_id = CONFIG.CARGOS_PATENTES.get(nova)
        if novo_role_id:
            novo_role = guild.get_role(novo_role_id)
            if novo_role and novo_role not in member.roles:
                try:
                    await member.add_roles(novo_role, reason="Nova patente conquistada")
                except discord.HTTPException:
                    pass

    return nova

async def registrar_ticket_fechado(
    *,
    usuario_id: int,
    guild_id: int,
    tipo: str | None,
    atendente_id: int | None,
    ticket_nome: str,
    transcript_url: str | None,
):
    await inicializar_banco_avaliacoes()
    conn = await _abrir_conexao_postgres()
    try:
        await conn.execute(
            """
            INSERT INTO ticket_fechados_recentes
            (usuario_id, guild_id, tipo, atendente_id, ticket_nome, transcript_url, fechado_em)
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
            ON CONFLICT (usuario_id) DO UPDATE SET
                guild_id = EXCLUDED.guild_id,
                tipo = EXCLUDED.tipo,
                atendente_id = EXCLUDED.atendente_id,
                ticket_nome = EXCLUDED.ticket_nome,
                transcript_url = EXCLUDED.transcript_url,
                fechado_em = NOW()
            """,
            usuario_id,
            guild_id,
            tipo,
            atendente_id,
            ticket_nome,
            transcript_url,
        )
    finally:
        await conn.close()


async def obter_ticket_fechado_recente(usuario_id: int) -> dict | None:
    await inicializar_banco_avaliacoes()
    conn = await _abrir_conexao_postgres()
    try:
        row = await conn.fetchrow(
            """
            SELECT * FROM ticket_fechados_recentes
            WHERE usuario_id = $1
              AND fechado_em > NOW() - ($2 || ' hours')::interval
            """,
            usuario_id,
            str(CONFIG.REABERTURA_JANELA_HORAS),
        )
    finally:
        await conn.close()
    return dict(row) if row else None


async def limpar_ticket_fechado_recente(usuario_id: int):
    conn = await _abrir_conexao_postgres()
    try:
        await conn.execute(
            "DELETE FROM ticket_fechados_recentes WHERE usuario_id = $1",
            usuario_id,
        )
    finally:
        await conn.close()


def _encontrar_ticket_do_usuario(
    guild: discord.Guild,
    user_id: int,
) -> discord.TextChannel | None:
    for ch in guild.text_channels:
        if ch.topic and f"DONO:{user_id}" in ch.topic:
            return ch
    return None


def _construir_overwrites_ticket(guild: discord.Guild, user: discord.Member, tipo: str) -> dict:
    """NOVO: extraído para função própria — reaproveitado na criação normal e na reabertura via DM."""
    overwrites: dict = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True,
            use_application_commands=False,
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_channels=True,
            manage_messages=True,
            read_message_history=True,
            embed_links=True,
            attach_files=True,
        ),
    }

    for cargo_id in CONFIG.CARGOS_ATENDIMENTO_IDS:
        cargo = guild.get_role(cargo_id)
        if cargo:
            overwrites[cargo] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
                manage_messages=True,
            )

    for cargo_id in CONFIG.CARGOS_POR_CATEGORIA.get(tipo, []):
        cargo = guild.get_role(cargo_id)
        if cargo and cargo not in overwrites:
            overwrites[cargo] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
                manage_messages=True,
            )

    return overwrites


async def gerar_transcript_texto(channel: discord.TextChannel) -> tuple[str, int]:
    """Retorna (conteúdo_txt, total_mensagens)."""
    linhas = [
        "=" * 64,
        f"  TRANSCRIPT — {channel.name.upper()}",
        f"  Gerado em: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S')} UTC",
        f"  FrostNova • Sistema de Tickets",
        "=" * 64,
        "",
    ]
    total = 0
    async for msg in channel.history(limit=None, oldest_first=True):
        total += 1
        data  = msg.created_at.strftime("%d/%m/%Y %H:%M")
        autor = f"{msg.author} ({msg.author.id})"
        corpo = msg.content or "[Sem texto]"
        if msg.attachments:
            corpo += "\n  Anexos:\n  " + "\n  ".join(a.url for a in msg.attachments)
        if msg.embeds:
            corpo += f"\n  [Embed: {msg.embeds[0].title or 'sem título'}]"
        linhas.append(f"[{data}] {autor}")
        linhas.append(f"  {corpo}")
        linhas.append("")

    if total == 0:
        linhas.append("Nenhuma mensagem registrada neste ticket.")

    return "\n".join(linhas), total


async def enviar_para_mclogs(conteudo: str) -> str | None:
    """
    Envia o conteúdo para mclo.gs e retorna a URL pública.
    Retorna None se falhar.
    """
    url = "https://api.mclo.gs/1/log"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data={"content": conteudo}, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success"):
                        return data.get("url")
                logger.warning(f"mclo.gs retornou status {resp.status}")
    except Exception as e:
        logger.error(f"Erro ao enviar para mclo.gs: {e}")
    return None


async def gerar_resumo_ticket(conteudo_txt: str, tipo: str | None) -> str:
    """
    NOVO: gera um resumo curto do atendimento para o log de fechamento.

    Se a variável de ambiente ANTHROPIC_API_KEY estiver configurada e o pacote
    `anthropic` instalado (pip install anthropic --break-system-packages),
    usa um modelo Claude para resumir o ticket em poucas frases.
    Caso contrário, cai num resumo heurístico simples (sem custo de API).
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import importlib
            anthropic = importlib.import_module("anthropic")
            client = anthropic.AsyncAnthropic(api_key=api_key)
            resposta = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=150,
                messages=[{
                    "role": "user",
                    "content": (
                        "Resuma o atendimento de suporte abaixo em no máximo 3 frases curtas, "
                        "em português do Brasil, focando no problema relatado e na resolução "
                        f"(se houver). Categoria do ticket: {tipo or 'desconhecida'}.\n\n"
                        f"{conteudo_txt[:6000]}"
                    ),
                }],
            )
            texto = "".join(b.text for b in resposta.content if b.type == "text").strip()
            if texto:
                return texto
        except Exception as e:
            logger.warning(f"Falha ao gerar resumo via IA, usando heurística: {e}")

    linhas_uteis = [
        l for l in conteudo_txt.splitlines()
        if l.strip() and not l.startswith("=") and "TRANSCRIPT" not in l and "Gerado em" not in l
    ]
    total_linhas_mensagem = sum(1 for l in linhas_uteis if l.startswith("["))
    return (
        f"Ticket de categoria `{tipo or 'desconhecida'}` com {total_linhas_mensagem} mensagens registradas. "
        "Resumo automático por IA indisponível (configure ANTHROPIC_API_KEY para ativar)."
    )


class TicketState:
    _ultimo_chamar_staff: dict[int, datetime] = {}
    _tickets_em_fechamento: set[int] = set()

    _inatividade_avisado: set[int] = set()
    _ultima_msg_vista: dict[int, int] = {}

    @classmethod
    def pode_chamar_staff(cls, channel_id: int) -> tuple[bool, int]:
        ultimo = cls._ultimo_chamar_staff.get(channel_id)
        if ultimo is None:
            return True, 0
        delta = (datetime.now(timezone.utc) - ultimo).total_seconds()
        restante = CONFIG.COOLDOWN_CHAMAR_STAFF_SEGUNDOS - delta
        if restante <= 0:
            return True, 0
        return False, int(restante)

    @classmethod
    def registrar_chamar_staff(cls, channel_id: int):
        cls._ultimo_chamar_staff[channel_id] = datetime.now(timezone.utc)

    @classmethod
    def marcar_fechando(cls, channel_id: int) -> bool:
        if channel_id in cls._tickets_em_fechamento:
            return False
        cls._tickets_em_fechamento.add(channel_id)
        return True

    @classmethod
    def desmarcar_fechando(cls, channel_id: int):
        cls._tickets_em_fechamento.discard(channel_id)


async def _anunciar_patente_se_mudou(bot: commands.Bot, guild: discord.Guild, atendente_id: int):
    """NOVO: chama a sincronização de patente e posta um anúncio se ela mudou."""
    nova_patente = await sincronizar_patente_atendente(bot, guild, atendente_id)
    if not nova_patente:
        return

    canal = guild.get_channel(CONFIG.CANAL_ANUNCIO_PATENTES_ID)
    if not canal:
        return

    emoji = PATENTE_EMOJI.get(nova_patente, "🐾")
    embed = discord.Embed(
        title=f"{emoji} Nova Patente Conquistada!",
        description=(
            f"<@{atendente_id}> avançou para a patente **{nova_patente}** "
            "com base na qualidade do seu atendimento. Uivem por essa conquista! 🐺"
        ),
        color=CONFIG.COR_DOURADO,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="FrostNova • Trilha da Matilha")
    try:
        await canal.send(embed=embed)
    except discord.HTTPException:
        pass


class ModalComentarioAvaliacao(discord.ui.Modal, title="Conte como foi seu atendimento"):
    """NOVO: modal exibido após o usuário escolher a nota, para deixar um comentário opcional."""

    comentario = discord.ui.TextInput(
        label="Comentário (opcional)",
        style=discord.TextStyle.paragraph,
        placeholder="O que achou do atendimento? O que podemos melhorar?",
        required=False,
        max_length=500,
    )

    def __init__(
        self,
        *,
        bot: commands.Bot,
        nota: int,
        ticket_id: int,
        ticket_nome: str,
        usuario_id: int,
        atendente_id: int,
        transcript_url: str | None,
        guild_id: int,
        mensagem_origem: discord.Message | None = None,
    ):
        super().__init__()
        self.bot = bot
        self.nota = nota
        self.ticket_id = ticket_id
        self.ticket_nome = ticket_nome
        self.usuario_id = usuario_id
        self.atendente_id = atendente_id
        self.transcript_url = transcript_url
        self.guild_id = guild_id
        self.mensagem_origem = mensagem_origem

    async def on_submit(self, interaction: discord.Interaction):
        await salvar_avaliacao_ticket(
            ticket_id=self.ticket_id,
            ticket_nome=self.ticket_nome,
            guild_id=self.guild_id,
            usuario_id=self.usuario_id,
            atendente_id=self.atendente_id,
            nota=self.nota,
            transcript_url=self.transcript_url,
            comentario=self.comentario.value or None,
        )

        media, total = await obter_resumo_atendente(self.atendente_id)

        embed_confirmacao = discord.Embed(
            title="✅ Avaliação registrada — obrigado!",
            description=(
                f"**Nota enviada:** `{self.nota}/5` {_estrelas(self.nota)}\n"
                + (f"**Seu comentário:** {self.comentario.value}\n" if self.comentario.value else "")
                + f"\n**Atendente:** <@{self.atendente_id}>\n"
                f"**Média atual do atendente:** `{media:.2f}/5`"
            ),
            color=CONFIG.COR_VERDE,
            timestamp=datetime.now(timezone.utc),
        )
        embed_confirmacao.set_footer(text="FrostNova • Avaliação de Atendimento")
        await interaction.response.send_message(embed=embed_confirmacao, ephemeral=True)

        if self.mensagem_origem is not None:
            try:
                for item in self.mensagem_origem.components:
                    pass  # componentes da DM não são editáveis via view salva; tratamos abaixo
                view_desabilitada = discord.ui.View(timeout=None)
                await self.mensagem_origem.edit(view=view_desabilitada)
            except discord.HTTPException:
                pass

        guild = self.bot.get_guild(self.guild_id)
        if guild is None:
            return

        canal_avaliacoes = guild.get_channel(CONFIG.CANAL_AVALIACOES_ID)
        if canal_avaliacoes:
            embed_publico = discord.Embed(
                title="⭐ Nova Avaliação de Atendimento (via DM)",
                description=(
                    f"Um atendimento foi avaliado privadamente.\n\n"
                    f"**Atendente:** <@{self.atendente_id}>\n"
                    f"**Nota:** `{self.nota}/5` {_estrelas(self.nota)}\n"
                    f"**Ticket:** `{self.ticket_nome}`\n"
                    f"**Classificação atual:** {_classificacao_media(media)}"
                ),
                color=CONFIG.COR_DOURADO,
                timestamp=datetime.now(timezone.utc),
            )
            if self.comentario.value:
                embed_publico.add_field(name="💬 Comentário", value=self.comentario.value[:1024], inline=False)
            embed_publico.add_field(name="📊 Média do atendente", value=f"`{media:.2f}/5`", inline=True)
            embed_publico.add_field(name="📋 Avaliações", value=f"`{total}`", inline=True)
            if self.transcript_url:
                embed_publico.add_field(
                    name="📁 Transcript",
                    value=f"[Clique aqui para abrir]({self.transcript_url})",
                    inline=False,
                )
            embed_publico.set_footer(text="FrostNova • Reputação da Equipe")
            try:
                await canal_avaliacoes.send(embed=embed_publico)
            except discord.HTTPException:
                pass

        await _anunciar_patente_se_mudou(self.bot, guild, self.atendente_id)


class BotaoAvaliacaoDM(discord.ui.Button):
    """NOVO: botão de estrela usado no painel de avaliação enviado por DM."""

    def __init__(self, nota: int):
        super().__init__(
            label=str(nota),
            emoji="⭐",
            style=discord.ButtonStyle.secondary if nota < 5 else discord.ButtonStyle.success,
            custom_id=f"ticket_dm_avaliar_nota_{nota}",
        )
        self.nota = nota

    async def callback(self, interaction: discord.Interaction):
        view: "ViewAvaliarAtendimentoDM" = self.view

        if interaction.user.id != view.usuario_id:
            await interaction.response.send_message(
                "❌ Esta avaliação não pertence a você.", ephemeral=True
            )
            return

        modal = ModalComentarioAvaliacao(
            bot=view.bot,
            nota=self.nota,
            ticket_id=view.ticket_id,
            ticket_nome=view.ticket_nome,
            usuario_id=view.usuario_id,
            atendente_id=view.atendente_id,
            transcript_url=view.transcript_url,
            guild_id=view.guild_id,
            mensagem_origem=interaction.message,
        )
        await interaction.response.send_modal(modal)


class ViewAvaliarAtendimentoDM(discord.ui.View):
    """NOVO: painel de avaliação privado enviado na DM do usuário ao fechar o ticket."""

    def __init__(
        self,
        *,
        bot: commands.Bot,
        ticket_id: int,
        ticket_nome: str,
        usuario_id: int,
        atendente_id: int,
        transcript_url: str | None,
        guild_id: int,
    ):
        super().__init__(timeout=None)
        self.bot = bot
        self.ticket_id = ticket_id
        self.ticket_nome = ticket_nome
        self.usuario_id = usuario_id
        self.atendente_id = atendente_id
        self.transcript_url = transcript_url
        self.guild_id = guild_id

        for nota in range(1, 6):
            self.add_item(BotaoAvaliacaoDM(nota))


class ViewAvaliarAtendimento(discord.ui.View):
    """Avaliação no canal — usada como FALLBACK quando a DM do usuário está fechada."""

    def __init__(
        self,
        *,
        ticket_id: int,
        ticket_nome: str,
        usuario_id: int,
        atendente_id: int,
        transcript_url: str | None,
    ):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
        self.ticket_nome = ticket_nome
        self.usuario_id = usuario_id
        self.atendente_id = atendente_id
        self.transcript_url = transcript_url

        for nota in range(1, 6):
            self.add_item(BotaoAvaliacaoAtendimento(nota))

        self.add_item(BotaoDeletarTicketAdmin())


class ViewDeletarTicketAdmin(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(BotaoDeletarTicketAdmin())


class BotaoDeletarTicketAdmin(discord.ui.Button):

    def __init__(self):
        super().__init__(
            label="Deletar Ticket",
            emoji="🗑️",
            style=discord.ButtonStyle.danger,
            custom_id="ticket_v2_deletar_ticket_admin",
            row=1,
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas administradores podem deletar este ticket.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "🗑️ Ticket deletado imediatamente.",
            ephemeral=True,
        )
        try:
            await interaction.channel.delete(reason=f"Ticket deletado por {interaction.user}")
        except discord.HTTPException as e:
            logger.warning(f"Falha ao deletar ticket: {e}")


class BotaoAvaliacaoAtendimento(discord.ui.Button):

    def __init__(self, nota: int):
        super().__init__(
            label=str(nota),
            emoji="⭐",
            style=discord.ButtonStyle.secondary if nota < 5 else discord.ButtonStyle.success,
            custom_id=f"ticket_avaliar_nota_{nota}",
        )
        self.nota = nota

    async def callback(self, interaction: discord.Interaction):
        view: ViewAvaliarAtendimento = self.view

        if interaction.user.id != view.usuario_id:
            await interaction.response.send_message(
                "❌ Apenas o autor do ticket pode avaliar este atendimento.",
                ephemeral=True,
            )
            return

        if interaction.user.id == view.atendente_id:
            await interaction.response.send_message(
                "❌ Você não pode avaliar o próprio atendimento.",
                ephemeral=True,
            )
            return

        await salvar_avaliacao_ticket(
            ticket_id=view.ticket_id,
            ticket_nome=view.ticket_nome,
            guild_id=interaction.guild.id,
            usuario_id=view.usuario_id,
            atendente_id=view.atendente_id,
            nota=self.nota,
            transcript_url=view.transcript_url,
        )

        media, total = await obter_resumo_atendente(view.atendente_id)

        embed = discord.Embed(
            title="✅ Avaliação registrada",
            description=(
                f"Obrigado pelo feedback, {interaction.user.mention}.\n\n"
                f"**Nota enviada:** `{self.nota}/5` {_estrelas(self.nota)}\n"
                f"**Atendente:** <@{view.atendente_id}>\n"
                f"**Média atual:** `{media:.2f}/5`\n"
                f"**Total de avaliações:** `{total}`"
            ),
            color=CONFIG.COR_VERDE,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text="FrostNova • Avaliação de Atendimento")

        for item in view.children:
            item.disabled = True
        await interaction.message.edit(view=view)
        await interaction.response.send_message(embed=embed, ephemeral=True)

        canal_avaliacoes = interaction.guild.get_channel(CONFIG.CANAL_AVALIACOES_ID)
        if canal_avaliacoes:
            embed_publico = discord.Embed(
                title="⭐ Nova Avaliação de Atendimento",
                description=(
                    f"Um atendimento foi avaliado por {interaction.user.mention}.\n\n"
                    f"**Atendente:** <@{view.atendente_id}>\n"
                    f"**Nota:** `{self.nota}/5` {_estrelas(self.nota)}\n"
                    f"**Ticket:** `{view.ticket_nome}`\n"
                    f"**Classificação atual:** {_classificacao_media(media)}"
                ),
                color=CONFIG.COR_DOURADO,
                timestamp=datetime.now(timezone.utc),
            )
            embed_publico.add_field(name="📊 Média do atendente", value=f"`{media:.2f}/5`", inline=True)
            embed_publico.add_field(name="📋 Avaliações", value=f"`{total}`", inline=True)
            if view.transcript_url:
                embed_publico.add_field(
                    name="📁 Transcript",
                    value=f"[Clique aqui para abrir]({view.transcript_url})",
                    inline=False,
                )
            embed_publico.set_footer(text="FrostNova • Reputação da Equipe")
            await canal_avaliacoes.send(embed=embed_publico)

        await _anunciar_patente_se_mudou(interaction.client, interaction.guild, view.atendente_id)

        canal_ticket = interaction.channel
        if isinstance(canal_ticket, discord.TextChannel) and canal_ticket.topic and "DONO:" in canal_ticket.topic:
            await asyncio.sleep(2)
            try:
                await canal_ticket.delete(reason=f"Ticket avaliado por {interaction.user}")
            except discord.HTTPException as e:
                logger.warning(f"Falha ao deletar ticket após avaliação: {e}")


class ViewConfirmarFechamento(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Confirmar Fechamento",
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="ticket_v3_confirmar_fechamento_imediato",
    )
    async def btn_confirmar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        canal = interaction.channel
        if not isinstance(canal, discord.TextChannel):
            await interaction.response.send_message(
                "❌ Este botão só pode ser usado dentro de um ticket.",
                ephemeral=True,
            )
            return

        dono_id = _extrair_dono_id(canal.topic or "")
        autorizado = (
            interaction.user.id == dono_id
            or tem_permissao(interaction.user)
        )

        if not autorizado:
            await interaction.response.send_message(
                "❌ Apenas o autor do ticket ou a equipe pode encerrá-lo.",
                ephemeral=True,
            )
            return

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            content="🔒 Encerrando o ticket...",
            embed=None,
            view=self,
        )
        await executar_fechamento(interaction)

    @discord.ui.button(
        label="Cancelar",
        style=discord.ButtonStyle.gray,
        emoji="✖️",
        custom_id="ticket_v3_cancelar_fechamento",
    )
    async def btn_cancelar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            content="✅ Fechamento cancelado. O ticket continua aberto.",
            embed=None,
            view=self,
        )


async def executar_fechamento(interaction: discord.Interaction):
    """
    Fecha o canal logo após capturar o transcript local.

    Operações lentas — upload do transcript, resumo, banco, log e DM —
    são executadas somente depois que o canal já foi removido.
    """
    canal = interaction.channel

    if not isinstance(canal, discord.TextChannel):
        return

    if not TicketState.marcar_fechando(canal.id):
        try:
            await interaction.followup.send(
                "⚠️ Este ticket já está sendo fechado.",
                ephemeral=True,
            )
        except discord.HTTPException:
            pass
        return

    guild = interaction.guild
    fechador = interaction.user
    topic = canal.topic or ""

    ticket_id = canal.id
    ticket_nome = canal.name
    criado_em = canal.created_at
    fechado_em = datetime.now(timezone.utc)
    dono_id = _extrair_dono_id(topic)
    atendente_id = _extrair_atendente_id(topic)
    tipo_ticket = _extrair_tipo_ticket(topic)
    duracao = formatar_duracao(
        int((fechado_em - criado_em).total_seconds())
    )

    try:
        # O histórico precisa ser lido antes da exclusão do canal.
        conteudo_txt, total_msgs = await gerar_transcript_texto(canal)

        # A exclusão acontece antes de qualquer API externa ou consulta demorada.
        try:
            await canal.delete(
                reason=f"Ticket fechado por {fechador} ({fechador.id})"
            )
        except discord.Forbidden:
            TicketState.desmarcar_fechando(ticket_id)
            try:
                await interaction.followup.send(
                    "❌ Não consegui deletar o canal. Conceda ao bot a permissão "
                    "**Gerenciar Canais** e deixe o cargo do bot acima dos cargos envolvidos.",
                    ephemeral=True,
                )
            except discord.HTTPException:
                pass
            return
        except discord.HTTPException as erro:
            TicketState.desmarcar_fechando(ticket_id)
            logger.error(
                "Falha HTTP ao deletar o ticket %s: %s",
                ticket_id,
                erro,
            )
            try:
                await interaction.followup.send(
                    f"❌ O Discord recusou a exclusão do canal: `{erro}`",
                    ephemeral=True,
                )
            except discord.HTTPException:
                pass
            return

        logger.info(
            "Ticket %s deletado. Iniciando processamento posterior.",
            ticket_id,
        )

        # Daqui em diante, falhas não impedem o fechamento.
        link_transcript = await enviar_para_mclogs(conteudo_txt)
        resumo = await gerar_resumo_ticket(conteudo_txt, tipo_ticket)

        if dono_id:
            try:
                await registrar_ticket_fechado(
                    usuario_id=dono_id,
                    guild_id=guild.id,
                    tipo=tipo_ticket,
                    atendente_id=atendente_id,
                    ticket_nome=ticket_nome,
                    transcript_url=link_transcript,
                )
            except Exception as erro:
                logger.warning(
                    "Falha ao registrar o ticket fechado %s: %s",
                    ticket_id,
                    erro,
                )

        log = guild.get_channel(CONFIG.CANAL_LOG_ID)
        if log:
            embed_log = discord.Embed(
                title="🔒 Ticket Encerrado",
                description=(
                    "O canal foi removido e o registro do atendimento foi salvo."
                    + (
                        f"\n[📋 Abrir transcript]({link_transcript})"
                        if link_transcript
                        else "\n⚠️ O transcript externo não ficou disponível."
                    )
                ),
                color=CONFIG.COR_DOURADO,
                timestamp=fechado_em,
            )
            embed_log.add_field(
                name="👤 Fechado por",
                value=fechador.mention,
                inline=True,
            )
            embed_log.add_field(
                name="📁 Ticket",
                value=f"`{ticket_nome}`",
                inline=True,
            )
            embed_log.add_field(
                name="🏷️ Categoria",
                value=f"`{tipo_ticket or 'desconhecida'}`",
                inline=True,
            )
            embed_log.add_field(
                name="⏳ Duração",
                value=f"`{duracao}`",
                inline=True,
            )
            embed_log.add_field(
                name="💬 Mensagens",
                value=f"`{total_msgs}`",
                inline=True,
            )
            embed_log.add_field(
                name="🧑‍💼 Atendente",
                value=f"<@{atendente_id}>" if atendente_id else "Não assumido",
                inline=True,
            )
            embed_log.add_field(
                name="📝 Resumo",
                value=resumo[:1024],
                inline=False,
            )

            if CONFIG.BANNER_FECHADO:
                embed_log.set_image(url=CONFIG.BANNER_FECHADO)

            embed_log.set_footer(text="FrostNova • Sistema de Tickets")

            view_log = discord.ui.View(timeout=None)
            if link_transcript:
                view_log.add_item(
                    discord.ui.Button(
                        label="Ver Transcript",
                        emoji="📋",
                        url=link_transcript,
                    )
                )

            try:
                await log.send(
                    embed=embed_log,
                    view=view_log if link_transcript else discord.utils.MISSING,
                )
            except discord.HTTPException as erro:
                logger.warning(
                    "Não foi possível enviar o log do ticket %s: %s",
                    ticket_id,
                    erro,
                )

        # A avaliação é enviada por DM. O canal já não existe neste ponto.
        if dono_id and atendente_id and dono_id != atendente_id:
            dono_member = guild.get_member(dono_id)

            if dono_member:
                embed_dm = discord.Embed(
                    title="⭐ Avalie seu atendimento — FrostNova",
                    description=(
                        f"Seu ticket **{ticket_nome}** foi encerrado.\n\n"
                        f"**Atendente:** <@{atendente_id}>\n"
                        f"**Duração:** `{duracao}`\n\n"
                        "Escolha uma nota de **1 a 5 estrelas**. "
                        "Depois, você poderá deixar um comentário opcional."
                    ),
                    color=CONFIG.COR_DOURADO,
                    timestamp=fechado_em,
                )

                if link_transcript:
                    embed_dm.add_field(
                        name="📋 Transcript",
                        value=f"[Ver registro do atendimento]({link_transcript})",
                        inline=False,
                    )

                embed_dm.set_footer(
                    text="FrostNova • Sistema de Avaliações"
                )

                try:
                    await dono_member.send(
                        embed=embed_dm,
                        view=ViewAvaliarAtendimentoDM(
                            bot=interaction.client,
                            ticket_id=ticket_id,
                            ticket_nome=ticket_nome,
                            usuario_id=dono_id,
                            atendente_id=atendente_id,
                            transcript_url=link_transcript,
                            guild_id=guild.id,
                        ),
                    )
                except discord.Forbidden:
                    logger.info(
                        "A DM do usuário %s está fechada; avaliação não enviada.",
                        dono_id,
                    )
                except discord.HTTPException as erro:
                    logger.warning(
                        "Erro ao enviar avaliação do ticket %s: %s",
                        ticket_id,
                        erro,
                    )

    except Exception as erro:
        logger.error(
            "Erro inesperado ao fechar o ticket %s: %s",
            getattr(canal, "id", "desconhecido"),
            erro,
            exc_info=True,
        )
        try:
            await interaction.followup.send(
                f"❌ Ocorreu um erro ao fechar o ticket: `{erro}`",
                ephemeral=True,
            )
        except discord.HTTPException:
            pass
    finally:
        TicketState.desmarcar_fechando(ticket_id)



async def fechar_ticket_por_inatividade(bot: commands.Bot, canal: discord.TextChannel):
    """
    NOVO: encerra automaticamente um ticket abandonado pelo usuário, seguindo o mesmo
    fluxo de transcript + log + histórico de reabertura do fechamento manual, mas
    sem depender de uma interação (é chamado pela task de monitoramento).
    """
    if not TicketState.marcar_fechando(canal.id):
        return

    try:
        topic = canal.topic or ""
        dono_id = _extrair_dono_id(topic)
        atendente_id = _extrair_atendente_id(topic)
        tipo_ticket = _extrair_tipo_ticket(topic)

        conteudo_txt, total_msgs = await gerar_transcript_texto(canal)
        link_transcript = await enviar_para_mclogs(conteudo_txt)
        resumo = await gerar_resumo_ticket(conteudo_txt, tipo_ticket)

        criado_em = canal.created_at
        fechado_em = datetime.now(timezone.utc)
        duracao = formatar_duracao(int((fechado_em - criado_em).total_seconds()))

        log = canal.guild.get_channel(CONFIG.CANAL_LOG_ID)
        if log:
            embed_log = discord.Embed(
                title="❄️ Ticket Encerrado por Inatividade",
                description=(
                    "O solicitante não respondeu dentro do prazo e o atendimento foi arquivado "
                    "automaticamente."
                    + (f"\n[📋 Clique aqui para ver o transcript]({link_transcript})" if link_transcript else "\n⚠️ Transcript indisponível.")
                ),
                color=CONFIG.COR_CINZA,
                timestamp=fechado_em,
            )
            embed_log.add_field(name="👤 Dono", value=f"<@{dono_id}>" if dono_id else "Desconhecido", inline=True)
            embed_log.add_field(name="📁 Canal", value=f"`{canal.name}`", inline=True)
            embed_log.add_field(name="⏳ Duração", value=f"`{duracao}`", inline=True)
            embed_log.add_field(name="💬 Mensagens", value=f"`{total_msgs}`", inline=True)
            embed_log.add_field(name="📝 Resumo do atendimento", value=resumo[:1024], inline=False)
            embed_log.set_footer(text="FrostNova • Sistema de Tickets")
            try:
                await log.send(embed=embed_log)
            except discord.HTTPException:
                pass

        if dono_id:
            try:
                await registrar_ticket_fechado(
                    usuario_id=dono_id,
                    guild_id=canal.guild.id,
                    tipo=tipo_ticket,
                    atendente_id=atendente_id,
                    ticket_nome=canal.name,
                    transcript_url=link_transcript,
                )
            except Exception as e:
                logger.warning(f"Falha ao registrar histórico de fechamento por inatividade: {e}")

        try:
            await canal.delete(reason="Ticket encerrado automaticamente por inatividade")
        except discord.HTTPException as e:
            logger.warning(f"Falha ao deletar ticket inativo: {e}")

    except Exception as e:
        logger.error(f"Erro ao encerrar ticket por inatividade ({canal.name}): {e}", exc_info=True)
    finally:
        TicketState.desmarcar_fechando(canal.id)

STATUS_TICKET = {
    "aguardando": {
        "titulo": "Aguardando equipe",
        "barra": "🟦⬜⬜⬜",
        "emoji": "⏳",
        "cor": CONFIG.COR_AZUL,
    },
    "atendimento": {
        "titulo": "Em atendimento",
        "barra": "🟦🟦⬜⬜",
        "emoji": "🟢",
        "cor": CONFIG.COR_VERDE,
    },
    "finalizando": {
        "titulo": "Finalizando",
        "barra": "🟦🟦🟦⬜",
        "emoji": "🧊",
        "cor": CONFIG.COR_DOURADO,
    },
    "concluido": {
        "titulo": "Concluído",
        "barra": "🟦🟦🟦🟦",
        "emoji": "✅",
        "cor": CONFIG.COR_CINZA,
    },
}


def _substituir_marcador_topic(topic: str, chave: str, valor: str) -> str:
    padrao = rf"{re.escape(chave)}:[^|]+"
    novo = f"{chave}:{valor}"
    if re.search(padrao, topic):
        return re.sub(padrao, novo, topic)
    return f"{topic} | {novo}"


def _extrair_status_ticket(topic: str) -> str:
    match = re.search(r"STATUS:([a-z_]+)", topic or "")
    return match.group(1) if match else "aguardando"


async def registrar_timeline(channel_id: int, evento: str, autor_id: int | None = None):
    await inicializar_banco_avaliacoes()
    conn = await _abrir_conexao_postgres()
    try:
        await conn.execute(
            """
            INSERT INTO ticket_timeline (channel_id, autor_id, evento, criado_em)
            VALUES ($1, $2, $3, NOW())
            """,
            channel_id,
            autor_id,
            evento[:500],
        )
    finally:
        await conn.close()


async def obter_timeline(channel_id: int, limite: int = 12) -> list[dict]:
    await inicializar_banco_avaliacoes()
    conn = await _abrir_conexao_postgres()
    try:
        rows = await conn.fetch(
            """
            SELECT autor_id, evento, criado_em
            FROM ticket_timeline
            WHERE channel_id = $1
            ORDER BY criado_em DESC
            LIMIT $2
            """,
            channel_id,
            limite,
        )
    finally:
        await conn.close()
    return [dict(r) for r in reversed(rows)]


async def salvar_nota_interna(channel_id: int, autor_id: int, conteudo: str):
    await inicializar_banco_avaliacoes()
    conn = await _abrir_conexao_postgres()
    try:
        await conn.execute(
            """
            INSERT INTO ticket_notas_internas (channel_id, autor_id, conteudo, criado_em)
            VALUES ($1, $2, $3, NOW())
            """,
            channel_id,
            autor_id,
            conteudo[:1500],
        )
    finally:
        await conn.close()


async def obter_notas_internas(channel_id: int, limite: int = 10) -> list[dict]:
    await inicializar_banco_avaliacoes()
    conn = await _abrir_conexao_postgres()
    try:
        rows = await conn.fetch(
            """
            SELECT autor_id, conteudo, criado_em
            FROM ticket_notas_internas
            WHERE channel_id = $1
            ORDER BY criado_em DESC
            LIMIT $2
            """,
            channel_id,
            limite,
        )
    finally:
        await conn.close()
    return [dict(r) for r in rows]


async def atualizar_painel_principal(
    canal: discord.TextChannel,
    *,
    status: str | None = None,
    atendente: discord.Member | None = None,
):
    """Atualiza o painel público do ticket com uma apresentação compacta."""
    topic = canal.topic or ""
    msg_id = _extrair_msg_id(topic)
    if not msg_id:
        return

    status = status or _extrair_status_ticket(topic)
    dados = STATUS_TICKET.get(status, STATUS_TICKET["aguardando"])
    tipo = _extrair_tipo_ticket(topic) or "outros"
    info = CONFIG.CATEGORIAS.get(tipo, CONFIG.CATEGORIAS["outros"])
    dono_id = _extrair_dono_id(topic)
    atendente_id = atendente.id if atendente else _extrair_atendente_id(topic)

    membro_atendente = atendente
    media = 0.0
    total = 0

    if atendente_id:
        membro_atendente = membro_atendente or canal.guild.get_member(atendente_id)
        try:
            media, total = await obter_resumo_atendente(atendente_id)
        except Exception as erro:
            logger.warning("Não foi possível carregar a reputação do atendente: %s", erro)

    embed = discord.Embed(
        title=info["titulo"],
        description=(
            f"Olá, <@{dono_id}>! Descreva sua solicitação com clareza e "
            "envie provas ou anexos quando necessário.\n\n"
            f"{dados['emoji']} **{dados['titulo']}**\n"
            f"{dados['barra']}"
        ),
        color=dados["cor"],
        timestamp=datetime.now(timezone.utc),
    )

    embed.add_field(
        name="🏷️ Categoria",
        value=info["nivel"],
        inline=True,
    )
    embed.add_field(
        name="🕒 Aberto",
        value=f"<t:{int(canal.created_at.timestamp())}:R>",
        inline=True,
    )

    if atendente_id:
        nome_atendente = membro_atendente.mention if membro_atendente else f"<@{atendente_id}>"
        reputacao = f"⭐ `{media:.2f}/5` • `{total}` avaliações" if total else "⭐ Ainda sem avaliações"
        embed.add_field(
            name="🧑‍💼 Atendimento",
            value=f"{nome_atendente}\n{reputacao}",
            inline=False,
        )
    else:
        embed.add_field(
            name="🧑‍💼 Atendimento",
            value="Aguardando um membro da equipe assumir.",
            inline=False,
        )

    embed.add_field(
        name="💡 Orientação",
        value=(
            "Use **Minhas ações** para adicionar informações, alterar a categoria "
            "ou chamar a equipe."
        ),
        inline=False,
    )

    imagem = CONFIG.IMAGENS.get(tipo)
    thumbnail = CONFIG.THUMBNAILS.get(tipo)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if imagem:
        embed.set_image(url=imagem)

    embed.set_footer(text="FrostNova • Central de Atendimento")

    try:
        msg = await canal.fetch_message(msg_id)
        await msg.edit(embed=embed, view=ViewAcoesTicket())
    except discord.NotFound:
        logger.warning("Mensagem principal do ticket %s não foi encontrada.", canal.id)
    except discord.HTTPException as erro:
        logger.warning("Falha ao atualizar o painel do ticket %s: %s", canal.id, erro)


async def definir_status_ticket(
    canal: discord.TextChannel,
    status: str,
    *,
    autor_id: int | None = None,
    evento: str | None = None,
):
    if status not in STATUS_TICKET:
        raise ValueError(f"Status inválido: {status}")
    topic = _substituir_marcador_topic(canal.topic or "", "STATUS", status)
    try:
        await canal.edit(topic=topic, reason="Atualização de status do ticket")
    except discord.HTTPException:
        pass
    if evento:
        await registrar_timeline(canal.id, evento, autor_id)
    await atualizar_painel_principal(canal, status=status)


class ModalAdicionarInformacoes(discord.ui.Modal, title="Adicionar informações ao ticket"):
    informacoes = discord.ui.TextInput(
        label="Novas informações",
        style=discord.TextStyle.paragraph,
        placeholder="Descreva detalhes adicionais, links, provas ou contexto...",
        min_length=5,
        max_length=1500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        dono_id = _extrair_dono_id(interaction.channel.topic or "")
        if interaction.user.id != dono_id and not tem_permissao(interaction.user):
            await interaction.response.send_message("❌ Você não pode editar este ticket.", ephemeral=True)
            return
        embed = discord.Embed(
            title="📝 Informações adicionadas",
            description=self.informacoes.value,
            color=CONFIG.COR_AZUL,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        await registrar_timeline(interaction.channel.id, f"{interaction.user.mention} adicionou novas informações.", interaction.user.id)
        await interaction.response.send_message(embed=embed)
        await atualizar_painel_principal(interaction.channel)


class ModalNotaInterna(discord.ui.Modal, title="Adicionar nota interna"):
    nota = discord.ui.TextInput(
        label="Nota exclusiva da equipe",
        style=discord.TextStyle.paragraph,
        placeholder="Registre contexto importante para outros atendentes...",
        min_length=3,
        max_length=1500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        tipo = _extrair_tipo_ticket(interaction.channel.topic or "") or ""
        if not tem_permissao_categoria(interaction.user, tipo):
            await interaction.response.send_message("❌ Recurso exclusivo da equipe.", ephemeral=True)
            return
        await salvar_nota_interna(interaction.channel.id, interaction.user.id, self.nota.value)
        await registrar_timeline(interaction.channel.id, f"Nota interna adicionada por {interaction.user.mention}.", interaction.user.id)
        await interaction.response.send_message("✅ Nota interna salva.", ephemeral=True)


class SelectAlterarCategoria(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Escolha a nova categoria...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=dados["label"],
                    description=dados["description"],
                    emoji=dados["emoji"],
                    value=chave,
                )
                for chave, dados in CONFIG.CATEGORIAS.items()
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        canal = interaction.channel
        tipo_atual = _extrair_tipo_ticket(canal.topic or "") or ""
        dono_id = _extrair_dono_id(canal.topic or "")
        if interaction.user.id != dono_id and not tem_permissao_categoria(interaction.user, tipo_atual):
            await interaction.response.send_message("❌ Você não pode alterar esta categoria.", ephemeral=True)
            return

        novo_tipo = self.values[0]
        info = CONFIG.CATEGORIAS[novo_tipo]
        topic = re.sub(r"Tipo:\s*\w+", f"Tipo: {novo_tipo}", canal.topic or "")
        novo_nome = slug(f"{info['nome_canal']}-{interaction.user.name if interaction.user.id == dono_id else canal.name.split('-', 1)[-1]}")
        try:
            await canal.edit(name=novo_nome, topic=topic, reason=f"Categoria alterada por {interaction.user}")
        except discord.HTTPException:
            await canal.edit(topic=topic, reason=f"Categoria alterada por {interaction.user}")

        await registrar_timeline(canal.id, f"Categoria alterada para **{info['label']}** por {interaction.user.mention}.", interaction.user.id)
        await interaction.response.edit_message(content=f"✅ Categoria alterada para **{info['label']}**.", view=None)
        await atualizar_painel_principal(canal)


class ViewAlterarCategoria(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(SelectAlterarCategoria())


class SelectTransferirAtendente(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="Selecione o novo atendente...", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        canal = interaction.channel
        tipo = _extrair_tipo_ticket(canal.topic or "") or ""
        if not tem_permissao_categoria(interaction.user, tipo):
            await interaction.response.send_message("❌ Recurso exclusivo da equipe.", ephemeral=True)
            return

        novo = self.values[0]
        if not isinstance(novo, discord.Member) or not tem_permissao_categoria(novo, tipo):
            await interaction.response.send_message("❌ Selecione um membro autorizado da equipe.", ephemeral=True)
            return

        topic = _marcar_atendente_no_topic(canal.topic or "", novo.id)
        topic = _substituir_marcador_topic(topic, "STATUS", "atendimento")
        await canal.edit(topic=topic, reason=f"Atendimento transferido por {interaction.user}")
        await registrar_timeline(canal.id, f"Atendimento transferido para {novo.mention} por {interaction.user.mention}.", interaction.user.id)
        await interaction.response.edit_message(content=f"✅ Atendimento transferido para {novo.mention}.", view=None)
        await atualizar_painel_principal(canal, status="atendimento", atendente=novo)


class ViewTransferirAtendente(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(SelectTransferirAtendente())


class SelectAcoesUsuario(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Escolha uma ação do seu ticket...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Adicionar informações", emoji="📝", value="informacoes", description="Envie mais detalhes ou provas."),
                discord.SelectOption(label="Alterar categoria", emoji="🏷️", value="categoria", description="Mova o ticket para outro setor."),
                discord.SelectOption(label="Chamar a equipe", emoji="📢", value="chamar", description="Solicite atenção da staff."),
                discord.SelectOption(label="Marcar como resolvido", emoji="✅", value="resolvido", description="Informe que sua solicitação foi solucionada."),
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        canal = interaction.channel
        dono_id = _extrair_dono_id(canal.topic or "")
        if interaction.user.id != dono_id and not tem_permissao(interaction.user):
            await interaction.response.send_message("❌ Este painel pertence ao autor do ticket.", ephemeral=True)
            return

        acao = self.values[0]
        if acao == "informacoes":
            await interaction.response.send_modal(ModalAdicionarInformacoes())
        elif acao == "categoria":
            await interaction.response.send_message("🏷️ Selecione a nova categoria:", view=ViewAlterarCategoria(), ephemeral=True)
        elif acao == "chamar":
            pode, restante = TicketState.pode_chamar_staff(canal.id)
            if not pode:
                await interaction.response.send_message(f"⏳ Aguarde `{restante}s` antes de chamar novamente.", ephemeral=True)
                return
            TicketState.registrar_chamar_staff(canal.id)
            mencoes = " ".join(f"<@&{cid}>" for cid in CONFIG.CARGOS_CHAMAR_STAFF)
            await registrar_timeline(canal.id, f"Equipe chamada por {interaction.user.mention}.", interaction.user.id)
            await interaction.response.send_message(
                content=mencoes,
                embed=discord.Embed(title="📢 Solicitação de atendimento", description=f"{interaction.user.mention} chamou a equipe.", color=CONFIG.COR_DOURADO),
                allowed_mentions=discord.AllowedMentions(roles=True),
            )
            await atualizar_painel_principal(canal)
        elif acao == "resolvido":
            await definir_status_ticket(canal, "finalizando", autor_id=interaction.user.id, evento=f"{interaction.user.mention} marcou a solicitação como resolvida.")
            await interaction.response.send_message("✅ A equipe foi informada. O ticket está pronto para finalização.", ephemeral=True)


class ViewAcoesUsuario(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(SelectAcoesUsuario())


class SelectPainelStaff(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Escolha uma ferramenta da equipe...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Transferir atendimento", emoji="🔄", value="transferir"),
                discord.SelectOption(label="Adicionar nota interna", emoji="📝", value="nota"),
                discord.SelectOption(label="Ver notas internas", emoji="📚", value="ver_notas"),
                discord.SelectOption(label="Alterar categoria", emoji="🏷️", value="categoria"),
                discord.SelectOption(label="Gerar resumo da conversa", emoji="✨", value="resumo"),
                discord.SelectOption(label="Marcar como finalizando", emoji="🧊", value="finalizando"),
                discord.SelectOption(label="Ver histórico do ticket", emoji="📜", value="historico"),
                discord.SelectOption(label="Ver informações completas", emoji="📋", value="info"),
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        canal = interaction.channel
        tipo = _extrair_tipo_ticket(canal.topic or "") or ""
        if not tem_permissao_categoria(interaction.user, tipo):
            await interaction.response.send_message("❌ Acesso exclusivo da equipe.", ephemeral=True)
            return

        acao = self.values[0]
        if acao == "transferir":
            await interaction.response.send_message("🔄 Selecione o novo atendente:", view=ViewTransferirAtendente(), ephemeral=True)
        elif acao == "nota":
            await interaction.response.send_modal(ModalNotaInterna())
        elif acao == "ver_notas":
            notas = await obter_notas_internas(canal.id)
            texto = "\n\n".join(
                f"<t:{int(n['criado_em'].timestamp())}:d> • <@{n['autor_id']}>\n> {n['conteudo']}"
                for n in notas
            ) or "Nenhuma nota interna registrada."
            await interaction.response.send_message(embed=discord.Embed(title="📚 Notas Internas", description=texto[:4000], color=CONFIG.COR_ROXO), ephemeral=True)
        elif acao == "categoria":
            await interaction.response.send_message("🏷️ Selecione a nova categoria:", view=ViewAlterarCategoria(), ephemeral=True)
        elif acao == "resumo":
            await interaction.response.defer(ephemeral=True, thinking=True)
            conteudo, total = await gerar_transcript_texto(canal)
            resumo = await gerar_resumo_ticket(conteudo, tipo)
            await registrar_timeline(canal.id, f"Resumo da conversa gerado por {interaction.user.mention}.", interaction.user.id)
            await interaction.followup.send(embed=discord.Embed(title="✨ Resumo da Conversa", description=f"{resumo}\n\n`{total} mensagens analisadas`", color=CONFIG.COR_DOURADO), ephemeral=True)
        elif acao == "finalizando":
            await definir_status_ticket(canal, "finalizando", autor_id=interaction.user.id, evento=f"{interaction.user.mention} iniciou a finalização do atendimento.")
            await interaction.response.send_message("🧊 Ticket marcado como finalizando.", ephemeral=True)
        elif acao == "historico":
            eventos = await obter_timeline(canal.id, limite=20)
            texto_historico = "\n".join(
                f"<t:{int(item['criado_em'].timestamp())}:f> • {item['evento']}"
                for item in eventos
            ) or "Nenhum evento registrado."

            embed_historico = discord.Embed(
                title="📜 Histórico Administrativo do Ticket",
                description=texto_historico[:4000],
                color=CONFIG.COR_ROXO,
                timestamp=datetime.now(timezone.utc),
            )
            embed_historico.set_footer(
                text=f"Visualização restrita • Solicitado por {interaction.user.display_name}"
            )
            await interaction.response.send_message(
                embed=embed_historico,
                ephemeral=True,
            )

        elif acao == "info":
            dono_id = _extrair_dono_id(canal.topic or "")
            atendente_id = _extrair_atendente_id(canal.topic or "")
            eventos = await obter_timeline(canal.id, 6)
            embed = discord.Embed(title="⚙️ Painel Restrito FrostNova", color=CONFIG.COR_AZUL, timestamp=datetime.now(timezone.utc))
            embed.add_field(name="📁 Canal", value=canal.mention, inline=True)
            embed.add_field(name="👤 Dono", value=f"<@{dono_id}>" if dono_id else "Desconhecido", inline=True)
            embed.add_field(name="🧑‍💼 Atendente", value=f"<@{atendente_id}>" if atendente_id else "Não assumido", inline=True)
            embed.add_field(name="🏷️ Categoria", value=f"`{tipo}`", inline=True)
            embed.add_field(name="⏳ Duração", value=f"`{formatar_duracao(int((datetime.now(timezone.utc)-canal.created_at).total_seconds()))}`", inline=True)
            embed.add_field(name="📊 Status", value=f"`{STATUS_TICKET[_extrair_status_ticket(canal.topic or '')]['titulo']}`", inline=True)
            if eventos:
                embed.add_field(name="📜 Eventos recentes", value="\n".join(e['evento'] for e in eventos)[:1024], inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)


class ViewPainelStaff(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(SelectPainelStaff())


class ViewAcoesTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Assumir", style=discord.ButtonStyle.success, emoji="🧑‍💼", custom_id="frostnova_ticket_assumir", row=0)
    async def btn_assumir(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal = interaction.channel
        tipo = _extrair_tipo_ticket(canal.topic or "") or ""
        if not tem_permissao_categoria(interaction.user, tipo):
            await interaction.response.send_message("❌ Apenas a equipe pode assumir este atendimento.", ephemeral=True)
            return

        atual = _extrair_atendente_id(canal.topic or "")
        if atual and atual != interaction.user.id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"⚠️ Este ticket já está sob responsabilidade de <@{atual}>. Use **Transferir atendimento**.", ephemeral=True)
            return

        primeira_resposta = atual is None
        topic = _marcar_atendente_no_topic(canal.topic or "", interaction.user.id)
        topic = _substituir_marcador_topic(topic, "STATUS", "atendimento")
        await canal.edit(topic=topic, reason=f"Ticket assumido por {interaction.user}")
        segundos_espera = int((datetime.now(timezone.utc) - canal.created_at).total_seconds())
        tempo = formatar_duracao(segundos_espera)
        await registrar_timeline(canal.id, f"Atendimento assumido por {interaction.user.mention} após **{tempo}**.", interaction.user.id)
        if primeira_resposta:
            await salvar_tempo_resposta(canal.id, interaction.user.id, segundos_espera)
        await atualizar_painel_principal(canal, status="atendimento", atendente=interaction.user)
        await interaction.response.send_message(f"🧑‍💼 {interaction.user.mention} assumiu este atendimento.")

    @discord.ui.button(label="Minhas ações", style=discord.ButtonStyle.primary, emoji="⚡", custom_id="frostnova_ticket_acoes_usuario", row=0)
    async def btn_acoes_usuario(self, interaction: discord.Interaction, button: discord.ui.Button):
        dono_id = _extrair_dono_id(interaction.channel.topic or "")
        if interaction.user.id != dono_id and not tem_permissao(interaction.user):
            await interaction.response.send_message("❌ Este painel pertence ao autor do ticket.", ephemeral=True)
            return
        await interaction.response.send_message("⚡ Escolha uma ação:", view=ViewAcoesUsuario(), ephemeral=True)

    @discord.ui.button(label="Painel Staff", style=discord.ButtonStyle.secondary, emoji="⚙️", custom_id="frostnova_ticket_painel_staff", row=0)
    async def btn_painel_staff(self, interaction: discord.Interaction, button: discord.ui.Button):
        tipo = _extrair_tipo_ticket(interaction.channel.topic or "") or ""
        if not tem_permissao_categoria(interaction.user, tipo):
            await interaction.response.send_message("❌ Acesso exclusivo da equipe.", ephemeral=True)
            return
        await interaction.response.send_message("⚙️ Selecione uma ferramenta:", view=ViewPainelStaff(), ephemeral=True)


    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="frostnova_ticket_fechar", row=1)
    async def btn_fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        dono_id = _extrair_dono_id(interaction.channel.topic or "")
        if interaction.user.id != dono_id and not tem_permissao(interaction.user):
            await interaction.response.send_message("❌ Apenas o dono ou a equipe pode fechar este ticket.", ephemeral=True)
            return
        embed = discord.Embed(
            title="🔒 Confirmar fechamento",
            description=(
                "O transcript e o resumo serão registrados.\n"
                "O autor receberá a avaliação por DM quando possível.\n\n"
                "Deseja realmente encerrar o atendimento?"
            ),
            color=CONFIG.COR_VERMELHO,
        )
        await interaction.response.send_message(embed=embed, view=ViewConfirmarFechamento(), ephemeral=True)


class SelectCategoriaTicket(discord.ui.Select):

    def __init__(self):
        opcoes = [
            discord.SelectOption(
                label=dados["label"],
                description=dados["description"],
                emoji=dados["emoji"],
                value=chave,
            )
            for chave, dados in CONFIG.CATEGORIAS.items()
        ]
        super().__init__(
            placeholder="Selecione uma categoria para abrir seu ticket...",
            min_values=1,
            max_values=1,
            options=opcoes,
            custom_id="ticket_v2_select_categoria",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild     = interaction.guild
        user      = interaction.user
        tipo      = self.values[0]
        info      = CONFIG.CATEGORIAS[tipo]
        categoria = guild.get_channel(CONFIG.CATEGORIA_TICKETS_ID)

        ticket_existente = _encontrar_ticket_do_usuario(guild, user.id)
        if ticket_existente:
            await interaction.followup.send(
                f"❌ Você já possui um ticket aberto: {ticket_existente.mention}\n"
                "Finalize o atendimento atual antes de abrir um novo.",
                ephemeral=True,
            )
            return

        if categoria is None:
            await interaction.followup.send(
                "❌ Categoria de tickets não encontrada. Contate um administrador.",
                ephemeral=True,
            )
            return

        overwrites = _construir_overwrites_ticket(guild, user, tipo)

        nome_canal = slug(f"{info['nome_canal']}-{user.name}")
        topic = (
            f"DONO:{user.id} | "
            f"Ticket de {user} | "
            f"Tipo: {tipo} | "
            f"Aberto em: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} UTC | STATUS:aguardando"
        )

        try:
            canal = await guild.create_text_channel(
                name=nome_canal,
                category=categoria,
                overwrites=overwrites,
                topic=topic,
                reason=f"Ticket aberto por {user} — categoria: {tipo}",
            )
        except discord.HTTPException as e:
            logger.error(f"Erro ao criar canal de ticket: {e}")
            await interaction.followup.send(
                "❌ Não foi possível criar o canal do ticket. Tente novamente.",
                ephemeral=True,
            )
            return

        mencoes_staff = " ".join(f"<@&{cid}>" for cid in CONFIG.CARGOS_ATENDIMENTO_IDS)

        embed_ticket = discord.Embed(
            title=info["titulo"],
            description=(
                f"✨ Olá {user.mention}, bem-vindo ao atendimento da **FrostNova**!\n\n"
                "Descreva sua solicitação com calma e aguarde enquanto a equipe se prepara.\n"
                "Envie prints ou provas se for necessário e evite menções desnecessárias.\n\n"
                f"⏳ **Status:** `Aguardando atendimento`"
            ),
            color=info["cor"],
            timestamp=datetime.now(timezone.utc),
        )
        embed_ticket.add_field(name="🏷️ Categoria", value=info["nivel"], inline=True)
        embed_ticket.add_field(name="👤 Solicitante", value=user.mention, inline=True)
        embed_ticket.add_field(
            name="🕒 Aberto em",
            value=f"<t:{int(datetime.now(timezone.utc).timestamp())}:R>",
            inline=True,
        )

        imagem    = CONFIG.IMAGENS.get(tipo)
        thumbnail = CONFIG.THUMBNAILS.get(tipo)
        if thumbnail: embed_ticket.set_thumbnail(url=thumbnail)
        if imagem:    embed_ticket.set_image(url=imagem)
        embed_ticket.set_footer(text="FrostNova • Sistema de Tickets")

        msg_painel = await canal.send(
            content=f"{user.mention} {mencoes_staff}",
            embed=embed_ticket,
            view=ViewAcoesTicket(),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )

        try:
            await canal.edit(topic=f"{topic} | MSGID:{msg_painel.id}")
        except discord.HTTPException as e:
            logger.warning(f"Não foi possível salvar MSGID no tópico: {e}")

        await registrar_timeline(canal.id, f"Ticket criado por {user.mention} na categoria **{info['label']}**.", user.id)
        await atualizar_painel_principal(canal, status="aguardando")

        await interaction.followup.send(
            f"✅ Ticket criado com sucesso! Acesse: {canal.mention}",
            ephemeral=True,
        )
        logger.info(f"Ticket criado: {canal.name} por {user} ({user.id})")


class ViewPainelTickets(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectCategoriaTicket())


class CogTickets(commands.Cog, name="Tickets"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        asyncio.create_task(inicializar_banco_avaliacoes())
        bot.add_view(ViewPainelTickets())
        bot.add_view(ViewAcoesTicket())
        bot.add_view(ViewConfirmarFechamento())
        self.monitorar_sla.start()
        self.monitorar_inatividade.start()

    def cog_unload(self):
        self.monitorar_sla.cancel()
        self.monitorar_inatividade.cancel()

    @tasks.loop(minutes=2)
    async def monitorar_sla(self):
        for guild in self.bot.guilds:
            categoria = guild.get_channel(CONFIG.CATEGORIA_TICKETS_ID)
            if not categoria or not isinstance(categoria, discord.CategoryChannel):
                continue

            for canal in categoria.text_channels:
                topic = canal.topic or ""
                if "DONO:" not in topic:
                    continue
                if _extrair_atendente_id(topic) is not None:
                    continue  # já assumido, sem necessidade de SLA

                elapsed_min = (datetime.now(timezone.utc) - canal.created_at).total_seconds() / 60

                if elapsed_min >= CONFIG.SLA_CRITICO_MINUTOS and "SLACRIT:1" not in topic:
                    await self._escalar_sla(canal, topic, critico=True)
                elif elapsed_min >= CONFIG.SLA_AVISO_MINUTOS and "SLAAVISO:1" not in topic:
                    await self._escalar_sla(canal, topic, critico=False)

    @monitorar_sla.before_loop
    async def before_monitorar_sla(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=15)
    async def monitorar_inatividade(self):
        """NOVO: avisa e depois encerra automaticamente tickets abandonados pelo solicitante."""
        agora = datetime.now(timezone.utc)

        for guild in self.bot.guilds:
            categoria = guild.get_channel(CONFIG.CATEGORIA_TICKETS_ID)
            if not categoria or not isinstance(categoria, discord.CategoryChannel):
                continue

            for canal in categoria.text_channels:
                topic = canal.topic or ""
                if "DONO:" not in topic or _extrair_status_ticket(topic) == "concluido":
                    continue

                try:
                    ultima_msg = [m async for m in canal.history(limit=1)]
                except discord.HTTPException:
                    continue
                if not ultima_msg:
                    continue
                ultima_msg = ultima_msg[0]

                if TicketState._ultima_msg_vista.get(canal.id) != ultima_msg.id:
                    TicketState._ultima_msg_vista[canal.id] = ultima_msg.id
                    TicketState._inatividade_avisado.discard(canal.id)

                horas_inativo = (agora - ultima_msg.created_at).total_seconds() / 3600

                if horas_inativo >= CONFIG.INATIVIDADE_FECHAMENTO_HORAS:
                    TicketState._inatividade_avisado.discard(canal.id)
                    TicketState._ultima_msg_vista.pop(canal.id, None)
                    await fechar_ticket_por_inatividade(self.bot, canal)
                elif horas_inativo >= CONFIG.INATIVIDADE_AVISO_HORAS and canal.id not in TicketState._inatividade_avisado:
                    TicketState._inatividade_avisado.add(canal.id)
                    dono_id = _extrair_dono_id(topic)
                    restante = int(CONFIG.INATIVIDADE_FECHAMENTO_HORAS - horas_inativo)
                    try:
                        await canal.send(
                            content=f"<@{dono_id}>" if dono_id else None,
                            embed=discord.Embed(
                                title="🧊 Ticket congelando por inatividade",
                                description=(
                                    "Não vimos nenhuma mensagem por aqui há um tempo.\n"
                                    f"Se não houver resposta em cerca de `{max(restante, 1)}h`, este ticket "
                                    "será encerrado automaticamente."
                                ),
                                color=CONFIG.COR_AMARELO,
                            ),
                            allowed_mentions=discord.AllowedMentions(users=True),
                        )
                        await registrar_timeline(canal.id, "⚠️ Aviso de inatividade enviado.")
                    except discord.HTTPException:
                        pass

    @monitorar_inatividade.before_loop
    async def before_monitorar_inatividade(self):
        await self.bot.wait_until_ready()

    async def _escalar_sla(self, canal: discord.TextChannel, topic: str, critico: bool):
        marcador = "SLACRIT:1" if critico else "SLAAVISO:1"
        try:
            await canal.edit(topic=f"{topic} | {marcador}")
        except discord.HTTPException:
            pass

        msg_id = _extrair_msg_id(topic)
        if msg_id:
            try:
                msg = await canal.fetch_message(msg_id)
                if msg.embeds:
                    embed_old = msg.embeds[0]
                    nova_cor = CONFIG.COR_VERMELHO if critico else CONFIG.COR_AMARELO
                    novo_embed = discord.Embed(
                        title=embed_old.title,
                        description=embed_old.description,
                        color=nova_cor,
                        timestamp=embed_old.timestamp,
                    )
                    if embed_old.thumbnail:
                        novo_embed.set_thumbnail(url=embed_old.thumbnail.url)
                    if embed_old.image:
                        novo_embed.set_image(url=embed_old.image.url)
                    if embed_old.footer:
                        novo_embed.set_footer(text=embed_old.footer.text)
                    await msg.edit(embed=novo_embed)
            except (discord.NotFound, discord.HTTPException):
                pass

        if critico:
            mencoes = " ".join(f"<@&{cid}>" for cid in CONFIG.CARGOS_CHAMAR_STAFF)
            try:
                await canal.send(
                    content=mencoes,
                    embed=discord.Embed(
                        title="🚨 SLA Crítico",
                        description=(
                            f"Este ticket está aberto há mais de `{CONFIG.SLA_CRITICO_MINUTOS}min` "
                            "sem atendente. Por favor, assumam o quanto antes."
                        ),
                        color=CONFIG.COR_VERMELHO,
                    ),
                    allowed_mentions=discord.AllowedMentions(roles=True),
                )
            except discord.HTTPException:
                pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is not None:
            return

        try:
            historico = await obter_ticket_fechado_recente(message.author.id)
        except Exception as e:
            logger.warning(f"Falha ao consultar histórico de reabertura: {e}")
            return

        if not historico:
            return

        guild = self.bot.get_guild(historico["guild_id"])
        if not guild:
            return

        membro = guild.get_member(message.author.id)
        if not membro:
            return

        ticket_existente = _encontrar_ticket_do_usuario(guild, message.author.id)
        if ticket_existente:
            try:
                await message.channel.send(
                    f"Você já tem um ticket aberto: vá até {ticket_existente.mention} no servidor."
                )
            except discord.HTTPException:
                pass
            return

        try:
            await message.channel.send(
                "👋 Vi que você teve um ticket recente! Estou reabrindo seu atendimento "
                "automaticamente para você não precisar abrir tudo de novo. Um momento..."
            )
        except discord.HTTPException:
            pass

        tipo = historico.get("tipo") or "outros"
        info = CONFIG.CATEGORIAS.get(tipo, CONFIG.CATEGORIAS["outros"])
        categoria = guild.get_channel(CONFIG.CATEGORIA_TICKETS_ID)
        if not categoria:
            return

        overwrites = _construir_overwrites_ticket(guild, membro, tipo)

        nome_canal = slug(f"reaberto-{info['nome_canal']}-{membro.name}")
        topic = (
            f"DONO:{membro.id} | "
            f"Ticket reaberto de {membro} | "
            f"Tipo: {tipo} | "
            f"Aberto em: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} UTC | STATUS:aguardando"
        )

        try:
            canal_novo = await guild.create_text_channel(
                name=nome_canal,
                category=categoria,
                overwrites=overwrites,
                topic=topic,
                reason=f"Reabertura automática via DM — {membro}",
            )
        except discord.HTTPException as e:
            logger.error(f"Erro ao reabrir ticket via DM: {e}")
            return

        mencoes_staff = " ".join(f"<@&{cid}>" for cid in CONFIG.CARGOS_ATENDIMENTO_IDS)
        atendente_anterior = historico.get("atendente_id")

        embed_reabertura = discord.Embed(
            title=f"🔁 Ticket Reaberto — {info['titulo']}",
            description=(
                f"{membro.mention} reabriu o atendimento via DM.\n\n"
                f"**Mensagem inicial:** {message.content or '[sem texto]'}\n\n"
                + (f"Ticket anterior atendido por: <@{atendente_anterior}>" if atendente_anterior else "")
            ),
            color=info["cor"],
            timestamp=datetime.now(timezone.utc),
        )
        embed_reabertura.set_footer(text="FrostNova • Sistema de Tickets")

        msg_painel = await canal_novo.send(
            content=f"{membro.mention} {mencoes_staff}",
            embed=embed_reabertura,
            view=ViewAcoesTicket(),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )

        try:
            await canal_novo.edit(topic=f"{topic} | MSGID:{msg_painel.id}")
        except discord.HTTPException:
            pass

        await limpar_ticket_fechado_recente(membro.id)

        try:
            await message.channel.send(f"✅ Pronto! Seu novo ticket foi criado: {canal_novo.mention}")
        except discord.HTTPException:
            pass

    @app_commands.command(
        name="ticket",
        description="Envia o painel de tickets no canal atual.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def cmd_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Sistema de Atendimento do Servidor",
            description=(
                "<a:26451timersand:1525657846807658657> | **HORÁRIO DE FUNCIONAMENTO**\n"
                "> - Segunda a sexta: 08:00 às 22:00.\n"
                "> - Sábado e Domingo: 09:00 às 18:00.\n\n"
                "<a:8017warning:1525658717943628006> | **AVISOS IMPORTANTES**\n"
                "> - Evite abrir tickets fora do horário de atendimento.\n"
                "> - Esteja ciente das nossas [regras](https://discord.com/channels/1480334256763961465/1525268820565164233/1525279902570647674) antes de abrir um ticket.\n"
                "> - Não envie mensagens desnecessárias ou spam, caso contrário o ticket poderá ser encerrado.\n"
                
                    ),
            color=CONFIG.COR_DOURADO,
            
                    )
        if CONFIG.BANNER_PAINEL:
            embed.set_image(url=CONFIG.BANNER_PAINEL)
        embed.set_footer(text="FrostNova • Atendimento oficial")

        await interaction.channel.send(embed=embed, view=ViewPainelTickets())
        await interaction.response.send_message(
            "✅ Painel de tickets enviado com sucesso.",
            ephemeral=True,
        )

    @cmd_ticket.error
    async def cmd_ticket_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ):
        msg = "❌ Você precisa ser administrador para usar este comando."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(
        name="fechar",
        description="Fecha o ticket atual (disponível dentro de um ticket).",
    )
    async def cmd_fechar(self, interaction: discord.Interaction):
        canal = interaction.channel
        topic = canal.topic or ""

        if "DONO:" not in topic:
            await interaction.response.send_message(
                "❌ Este comando só pode ser usado dentro de um canal de ticket.",
                ephemeral=True,
            )
            return

        dono_id = _extrair_dono_id(topic)
        e_dono  = dono_id == interaction.user.id
        e_staff = tem_permissao(interaction.user)

        if not (e_dono or e_staff):
            await interaction.response.send_message(
                "❌ Apenas o dono do ticket ou a equipe pode fechá-lo.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="🔒 Confirmar Fechamento",
            description=(
                "Tem certeza que deseja encerrar este atendimento?\n\n"
                "• O transcript será salvo automaticamente.\n"
                "• Um resumo automático do ticket será gerado para o log.\n"
                "• Você receberá um painel de avaliação privado por DM.\n"
                "• O canal será removido imediatamente após a captura do transcript.\n\n"
                "Esta ação encerra o atendimento."
            ),
            color=CONFIG.COR_VERMELHO,
        )
        await interaction.response.send_message(
            embed=embed,
            view=ViewConfirmarFechamento(),
            ephemeral=True,
        )

    @app_commands.command(
        name="ticket-info",
        description="Exibe informações do ticket atual.",
    )
    async def cmd_info(self, interaction: discord.Interaction):
        canal = interaction.channel
        topic = canal.topic or ""

        if "DONO:" not in topic:
            await interaction.response.send_message(
                "❌ Este canal não é um ticket.",
                ephemeral=True,
            )
            return

        tipo = _extrair_tipo_ticket(topic)
        if not tem_permissao_categoria(interaction.user, tipo or ""):
            await interaction.response.send_message(
                "❌ Apenas a equipe pode ver as informações do ticket.",
                ephemeral=True,
            )
            return

        dono_id = _extrair_dono_id(topic)
        dono    = f"<@{dono_id}>" if dono_id else "Desconhecido"
        aberto  = canal.created_at

        total_msgs = 0
        async for _ in canal.history(limit=None):
            total_msgs += 1

        embed = discord.Embed(
            title="📋 Informações do Ticket",
            color=CONFIG.COR_AZUL,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="📁 Canal",     value=canal.mention, inline=True)
        embed.add_field(name="👤 Dono",      value=dono,          inline=True)
        embed.add_field(name="🏷️ Categoria", value=f"`{tipo or 'desconhecida'}`", inline=True)
        embed.add_field(
            name="🕒 Aberto em",
            value=f"<t:{int(aberto.timestamp())}:f>",
            inline=True,
        )
        embed.add_field(
            name="⏳ Duração",
            value=f"`{formatar_duracao(int((datetime.now(timezone.utc) - aberto).total_seconds()))}`",
            inline=True,
        )
        embed.add_field(name="💬 Mensagens", value=f"`{total_msgs}`", inline=True)
        embed.set_footer(text=f"Consultado por {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="ticket-fechar-forcado",
        description="[Admin] Força o fechamento do ticket no canal atual.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def cmd_fechar_forcado(self, interaction: discord.Interaction):
        canal = interaction.channel
        topic = canal.topic or ""

        if "DONO:" not in topic:
            await interaction.response.send_message(
                "❌ Este canal não é um ticket.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        await executar_fechamento(interaction)

    @cmd_fechar_forcado.error
    async def cmd_fechar_forcado_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ):
        msg = "❌ Você precisa ser administrador para usar este comando."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(
        name="reputacao-atendente",
        description="Mostra a reputação de atendimento de um membro da equipe.",
    )
    async def cmd_reputacao_atendente(
        self,
        interaction: discord.Interaction,
        atendente: discord.Member,
    ):
        if not tem_permissao(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas a equipe pode consultar reputações de atendimento.",
                ephemeral=True,
            )
            return

        media, total = await obter_resumo_atendente(atendente.id)
        patente = await obter_patente_atual_db(atendente.id)
        emoji_patente = PATENTE_EMOJI.get(patente, "🐾")
        tempo_medio = await obter_tempo_resposta_medio(atendente.id)

        embed = discord.Embed(
            title="📊 Reputação do Atendente",
            description=(
                f"👤 **Atendente:** {atendente.mention}\n"
                f"{emoji_patente} **Patente:** `{patente}`\n"
                f"⭐ **Média:** `{media:.2f}/5`\n"
                f"📋 **Avaliações:** `{total}`\n"
                f"⏱️ **Tempo médio de 1ª resposta:** `{formatar_duracao(tempo_medio) if tempo_medio is not None else 'Sem dados'}`\n"
                f"🏷️ **Classificação:** {_classificacao_media(media) if total else 'Sem avaliações ainda'}"
            ),
            color=CONFIG.COR_AZUL,
            timestamp=datetime.now(timezone.utc),
        )

        comentarios = await obter_comentarios_recentes_atendente(atendente.id, limite=3)
        if comentarios:
            texto_comentarios = "\n".join(
                f"`{c['nota']}⭐` — {c['comentario'][:120]}" for c in comentarios
            )
            embed.add_field(name="💬 Últimos comentários", value=texto_comentarios[:1024], inline=False)

        embed.set_thumbnail(url=atendente.display_avatar.url)
        embed.set_footer(text="FrostNova • Reputação da Equipe")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="minha-patente",
        description="Mostra sua patente atual de atendimento.",
    )
    async def cmd_minha_patente(self, interaction: discord.Interaction):
        if not tem_permissao(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas a equipe possui patentes de atendimento.",
                ephemeral=True,
            )
            return

        media, total = await obter_resumo_atendente(interaction.user.id)
        patente = await obter_patente_atual_db(interaction.user.id)
        emoji_patente = PATENTE_EMOJI.get(patente, "🐾")
        tempo_medio = await obter_tempo_resposta_medio(interaction.user.id)

        proxima_info = ""
        if total < 5:
            proxima_info = f"Faltam `{5 - total}` avaliações para sair de Lobo Errante."
        elif patente != "Lenda de FrostNova":
            proxima_info = "Continue mantendo a qualidade do atendimento para evoluir."

        embed = discord.Embed(
            title=f"{emoji_patente} Sua Patente: {patente}",
            description=(
                f"⭐ **Média:** `{media:.2f}/5`\n"
                f"📋 **Avaliações:** `{total}`\n"
                f"⏱️ **Tempo médio de 1ª resposta:** `{formatar_duracao(tempo_medio) if tempo_medio is not None else 'Sem dados'}`\n\n"
                f"{_classificacao_media(media) if total else 'Continue atendendo para evoluir sua patente!'}\n\n"
                f"{proxima_info}"
            ),
            color=CONFIG.COR_DOURADO,
        )
        embed.set_footer(text="FrostNova • Trilha da Matilha")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="ranking-atendentes",
        description="Mostra o ranking dos atendentes mais bem avaliados.",
    )
    async def cmd_ranking_atendentes(self, interaction: discord.Interaction):
        if not tem_permissao(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas a equipe pode consultar o ranking de atendentes.",
                ephemeral=True,
            )
            return

        ranking = await obter_ranking_atendentes(10)

        if not ranking:
            await interaction.response.send_message(
                "📭 Ainda não há avaliações registradas.",
                ephemeral=True,
            )
            return

        linhas = []
        medalhas = ["🥇", "🥈", "🥉"]
        for pos, (atendente_id, media, total) in enumerate(ranking, start=1):
            prefixo = medalhas[pos - 1] if pos <= 3 else f"`#{pos}`"
            patente = calcular_patente(media, total)
            emoji_patente = PATENTE_EMOJI.get(patente, "🐾")
            linhas.append(
                f"{prefixo} <@{atendente_id}> {emoji_patente} `{patente}` — "
                f"**{media:.2f}/5** • `{total}` avaliações"
            )

        embed = discord.Embed(
            title="🏆 Ranking de Atendentes",
            description="\n".join(linhas),
            color=CONFIG.COR_DOURADO,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text="FrostNova • Qualidade de Atendimento")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(CogTickets(bot))
    logger.info("CogTickets carregado com sucesso.")