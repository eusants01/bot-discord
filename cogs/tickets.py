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

    CATEGORIA_TICKETS_ID = 1495288098010169574
    CANAL_LOG_ID         = 1495272331558391818
    CANAL_AVALIACOES_ID  = 1513346061887082666

    DATABASE_URL = os.getenv("DATABASE_URL")

    CARGOS_ATENDIMENTO_IDS: list[int] = [
        1487560221202321600,
        1505759604842434651,
        1480381506064093225,
        1500545846427652166,
        1501356975491907664,
    ]

    CARGOS_CHAMAR_STAFF: list[int] = [
        1512905705819078929,
    ]

    CARGOS_POR_CATEGORIA: dict[str, list[int]] = {
        "duvida":     [],
        "denuncia":   [],
        "patrocinio": [1509054988972851252, 1502717285528506536],
        "outros":     [],
    }

    COOLDOWN_CHAMAR_STAFF_SEGUNDOS = 100
    COOLDOWN_ABRIR_TICKET_SEGUNDOS = 10

    BANNER_PAINEL  = "https://cdn.discordapp.com/attachments/961677475191078992/1518142427087507586/content.png?ex=6a38d7d0&is=6a378650&hm=6d086a0284c5cea10502d122fdf4c668dcbd156064ece7bbbafcef017e80b8ef&"
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

    COR_VERMELHO = discord.Color.from_rgb(200, 60,  90)    
    COR_AZUL     = discord.Color.from_rgb(88,  101, 242)   
    COR_DOURADO  = discord.Color.from_rgb(147, 112, 219)  
    COR_VERDE    = discord.Color.from_rgb(60,  200, 150)   
    COR_ROXO     = discord.Color.from_rgb(98,  54,  163)   
    COR_ESCURO   = discord.Color.from_rgb(15,  12,  30)    
    COR_CINZA    = discord.Color.from_rgb(90,  90,  110)   
    COR_AMARELO  = discord.Color.from_rgb(230, 190, 70)    

    CATEGORIAS: dict[str, dict] = {
        "duvida": {
            "label":       "Dúvidas",
            "description": "Tire suas dúvidas com a equipe.",
            "emoji":       "🛰️",
            "titulo":      "🛰️ Dúvidas — Central de Comunicação",
            "nivel":       "🔵 Suporte Geral",
            "cor":         discord.Color.from_rgb(88, 101, 242),
            "nome_canal":  "duvida",
        },
        "denuncia": {
            "label":       "Denúncias",
            "description": "Reporte algo irregular com provas.",
            "emoji":       "🚨",
            "titulo":      "🚨 Denúncia — Alerta de Anomalia",
            "nivel":       "🔴 Prioridade Alta",
            "cor":         discord.Color.from_rgb(200, 60, 90),
            "nome_canal":  "denuncia",
        },
        "patrocinio": {
            "label":       "Patrocínios",
            "description": "Parcerias e propostas comerciais.",
            "emoji":       "🌌",
            "titulo":      "🌌 Patrocínio — Embaixada Estelar",
            "nivel":       "🟡 Proposta Comercial",
            "cor":         discord.Color.from_rgb(147, 112, 219),
            "nome_canal":  "patrocinio",
        },
        "outros": {
            "label":       "Outros",
            "description": "Assuntos que não se encaixam acima.",
            "emoji":       "🪐",
            "titulo":      "🪐 Outros — Setor Desconhecido",
            "nivel":       "⚪ Atendimento Geral",
            "cor":         discord.Color.from_rgb(90, 90, 110),
            "nome_canal":  "outros",
        },
    }

    SLA_AVISO_MINUTOS   = 10   
    SLA_CRITICO_MINUTOS = 25  

    CARGOS_PATENTES: dict[str, int] = {
        "Ronin Errante":     0,
        "Samurai":           0,
        "Samurai de Elite":  0,
        "Mestre da Lâmina":  0,
        "Lenda de Musashi":  0,
    }
    CANAL_ANUNCIO_PATENTES_ID = CANAL_AVALIACOES_ID

    REABERTURA_JANELA_HORAS = 24


PATENTE_EMOJI: dict[str, str] = {
    "Ronin Errante":    "🗡️",
    "Samurai":          "⚔️",
    "Samurai de Elite":  "🎴",
    "Mestre da Lâmina":  "🌸",
    "Lenda de Musashi":  "🐉",
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
    """NOVO: calcula a patente do atendente com base na média e volume de avaliações."""
    if total < 5:
        return "Ronin Errante"
    if media >= 4.9 and total >= 20:
        return "Lenda de Musashi"
    if media >= 4.7:
        return "Mestre da Lâmina"
    if media >= 4.2:
        return "Samurai de Elite"
    if media >= 3.5:
        return "Samurai"
    return "Ronin Errante"


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
                patente_atual TEXT NOT NULL DEFAULT 'Ronin Errante',
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
            """
        )
    finally:
        await conn.close()


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
    return row["patente_atual"] if row else "Ronin Errante"


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
        f"  Nebularis • Sistema de Tickets",
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

    emoji = PATENTE_EMOJI.get(nova_patente, "🗡️")
    embed = discord.Embed(
        title=f"{emoji} Nova Patente Conquistada!",
        description=(
            f"<@{atendente_id}> avançou para a patente **{nova_patente}** "
            "com base na qualidade do seu atendimento. Parabéns, guerreiro(a)! 🎴"
        ),
        color=CONFIG.COR_DOURADO,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Nebularis • Caminho do Espadachim")
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
        embed_confirmacao.set_footer(text="Nebularis • Avaliação de Atendimento")
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
            embed_publico.set_footer(text="Nebularis • Reputação da Equipe")
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
        embed.set_footer(text="Nebularis • Avaliação de Atendimento")

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
            embed_publico.set_footer(text="Nebularis • Reputação da Equipe")
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
        custom_id="ticket_v2_confirmar_fechamento",
    )
    async def btn_confirmar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas administradores podem encerrar o atendimento e liberar a avaliação.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        await executar_fechamento(interaction)

    @discord.ui.button(
        label="Cancelar",
        style=discord.ButtonStyle.gray,
        emoji="✖️",
        custom_id="ticket_v2_cancelar_fechamento",
    )
    async def btn_cancelar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.send_message(
            "✅ Fechamento cancelado. O ticket continua aberto.",
            ephemeral=True,
        )


async def executar_fechamento(interaction: discord.Interaction):
    canal = interaction.channel
    print(f"[FECHAR] Iniciando: {canal.name} ({canal.id})")

    if not TicketState.marcar_fechando(canal.id):
        print(f"[FECHAR] Canal {canal.id} já está sendo fechado.")
        await interaction.followup.send(
            "⚠️ Este ticket já está sendo fechado.",
            ephemeral=True,
        )
        return

    try:
        print(f"[FECHAR] Gerando transcript...")
        conteudo_txt, total_msgs = await gerar_transcript_texto(canal)
        print(f"[FECHAR] Transcript gerado. Total msgs: {total_msgs}")

        print(f"[FECHAR] Enviando para mclo.gs...")
        link_transcript = await enviar_para_mclogs(conteudo_txt)
        if link_transcript:
            print(f"[FECHAR] Transcript disponível em: {link_transcript}")
        else:
            print(f"[FECHAR] AVISO: falha ao enviar para mclo.gs. Continuando sem link.")

        tipo_ticket = _extrair_tipo_ticket(canal.topic or "")
        print(f"[FECHAR] Gerando resumo automático...")
        resumo = await gerar_resumo_ticket(conteudo_txt, tipo_ticket)

        log        = interaction.guild.get_channel(CONFIG.CANAL_LOG_ID)
        criado_em  = canal.created_at
        fechado_em = datetime.now(timezone.utc)
        duracao    = formatar_duracao(int((fechado_em - criado_em).total_seconds()))
        dono_id    = _extrair_dono_id(canal.topic or "")
        atendente_id = _extrair_atendente_id(canal.topic or "")
        print(f"[FECHAR] Canal de log: {log}")

        if log:
            embed_log = discord.Embed(
                title="🔒 Ticket Encerrado",
                description=(
                    "O atendimento foi finalizado e o registro foi salvo."
                    + (f"\n[📋 Clique aqui para ver o transcript]({link_transcript})" if link_transcript else "\n⚠️ Transcript indisponível.")
                ),
                color=CONFIG.COR_DOURADO,
                timestamp=fechado_em,
            )
            embed_log.add_field(name="👤 Fechado por", value=interaction.user.mention, inline=True)
            embed_log.add_field(name="📁 Canal",       value=f"`{canal.name}`",        inline=True)
            embed_log.add_field(name="⏳ Duração",     value=f"`{duracao}`",            inline=True)
            embed_log.add_field(name="💬 Mensagens",   value=f"`{total_msgs}`",         inline=True)
            embed_log.add_field(
                name="🕒 Aberto em",
                value=f"<t:{int(criado_em.timestamp())}:f>",
                inline=True,
            )
            embed_log.add_field(
                name="🔒 Fechado em",
                value=f"<t:{int(fechado_em.timestamp())}:f>",
                inline=True,
            )
            embed_log.add_field(name="📝 Resumo do atendimento", value=resumo[:1024], inline=False)
            embed_log.set_thumbnail(url=interaction.user.display_avatar.url)
            if CONFIG.BANNER_FECHADO:
                embed_log.set_image(url=CONFIG.BANNER_FECHADO)
            embed_log.set_footer(text="Nebularis • Sistema de Tickets")

            view_links = discord.ui.View(timeout=None)
            if link_transcript:
                view_links.add_item(discord.ui.Button(
                    label="📋 Ver Transcript",
                    url=link_transcript,
                    style=discord.ButtonStyle.link,
                ))

            await log.send(embed=embed_log, view=view_links if link_transcript else discord.utils.MISSING)
            print(f"[FECHAR] Log enviado com sucesso.")
        else:
            print(f"[FECHAR] AVISO: canal de log não encontrado! Verifique CANAL_LOG_ID.")

        try:
            await interaction.followup.send(
                "✅ Ticket encerrado.",
                ephemeral=True,
            )
        except discord.HTTPException as e:
            print(f"[FECHAR] Não foi possível enviar followup: {e}")

        # NOVO: registra o fechamento para permitir reabertura automática via DM
        if dono_id:
            try:
                await registrar_ticket_fechado(
                    usuario_id=dono_id,
                    guild_id=interaction.guild.id,
                    tipo=tipo_ticket,
                    atendente_id=atendente_id,
                    ticket_nome=canal.name,
                    transcript_url=link_transcript,
                )
            except Exception as e:
                logger.warning(f"Falha ao registrar histórico de fechamento: {e}")

        dm_enviada = False

        if dono_id and atendente_id and dono_id != atendente_id:
            dono_member = interaction.guild.get_member(dono_id)
            if dono_member:
                embed_dm = discord.Embed(
                    title="⭐ Avalie seu atendimento — Nebularis",
                    description=(
                        f"Seu ticket **{canal.name}** foi encerrado.\n\n"
                        f"**Atendente:** <@{atendente_id}>\n"
                        f"**Duração:** `{duracao}`\n\n"
                        "Escolha uma nota de **1 a 5 estrelas** abaixo (`1` Ruim · `3` Regular · `5` Excelente). "
                        "Depois você poderá deixar um comentário opcional — isso fica só "
                        "entre você e a equipe."
                    ),
                    color=CONFIG.COR_DOURADO,
                    timestamp=fechado_em,
                )
                if link_transcript:
                    embed_dm.add_field(
                        name="📋 Transcript",
                        value=f"[Ver registro do ticket]({link_transcript})",
                        inline=False,
                    )
                embed_dm.set_footer(text="Nebularis • Sistema de Avaliações")

                try:
                    await dono_member.send(
                        embed=embed_dm,
                        view=ViewAvaliarAtendimentoDM(
                            bot=interaction.client,
                            ticket_id=canal.id,
                            ticket_nome=canal.name,
                            usuario_id=dono_id,
                            atendente_id=atendente_id,
                            transcript_url=link_transcript,
                            guild_id=interaction.guild.id,
                        ),
                    )
                    dm_enviada = True
                    print(f"[FECHAR] Painel de avaliação enviado via DM para {dono_member}.")
                except discord.Forbidden:
                    print(f"[FECHAR] DM fechada para {dono_member}, usando fallback no canal.")
                except discord.HTTPException as e:
                    print(f"[FECHAR] Erro ao enviar DM: {e}")

        if dm_enviada:
            embed_dm_aviso = discord.Embed(
                title="📬 Avaliação enviada na DM",
                description=(
                    f"{interaction.user.mention} encerrou este ticket.\n\n"
                    f"Enviamos um painel de avaliação privado para <@{dono_id}> "
                    "responder com nota e comentário.\n\n"
                    "Este canal será removido automaticamente em instantes. "
                    "Um administrador também pode deletá-lo agora pelo botão abaixo."
                ),
                color=CONFIG.COR_DOURADO,
            )
            await canal.send(embed=embed_dm_aviso, view=ViewDeletarTicketAdmin())
            await asyncio.sleep(45)
            try:
                await canal.delete(reason="Avaliação enviada por DM — ticket encerrado")
            except discord.HTTPException:
                pass

        elif dono_id and atendente_id and dono_id != atendente_id:
            # Fallback: dono não pôde receber DM -> avaliação tradicional no canal
            embed_avaliacao = discord.Embed(
                title="⭐ Avalie o Atendimento",
                description=(
                    f"<@{dono_id}>, seu ticket foi encerrado por **{interaction.user.display_name}**.\n\n"
                    f"**Atendente:** <@{atendente_id}>\n"
                    f"**Ticket:** `{canal.name}`\n\n"
                    "Escolha uma nota de **1 a 5 estrelas** (`1` Ruim · `3` Regular · `5` Excelente). "
                    "Após a avaliação, o ticket será deletado automaticamente.\n\n"
                    "Administradores também podem usar o botão **Deletar Ticket** para apagar o canal imediatamente."
                ),
                color=CONFIG.COR_DOURADO,
                timestamp=fechado_em,
            )
            if link_transcript:
                embed_avaliacao.add_field(
                    name="📋 Transcript",
                    value=f"[Ver registro do ticket]({link_transcript})",
                    inline=False,
                )
            embed_avaliacao.set_footer(text="Nebularis • Sistema de Avaliações")

            await canal.send(
                content=f"<@{dono_id}>",
                embed=embed_avaliacao,
                view=ViewAvaliarAtendimento(
                    ticket_id=canal.id,
                    ticket_nome=canal.name,
                    usuario_id=dono_id,
                    atendente_id=atendente_id,
                    transcript_url=link_transcript,
                ),
                allowed_mentions=discord.AllowedMentions(users=True),
            )
        else:
            print("[FECHAR] Avaliação não enviada: ticket sem atendente assumido ou sem dono válido.")
            embed_aviso = discord.Embed(
                title="🔒 Ticket Encerrado",
                description=(
                    f"Este ticket foi fechado por **{interaction.user.display_name}**.\n\n"
                    "Não foi possível enviar avaliação porque o ticket não possui dono válido ou atendente assumido.\n"
                    "Um administrador pode deletar este canal imediatamente pelo botão abaixo."
                ),
                color=CONFIG.COR_ESCURO,
                timestamp=fechado_em,
            )
            embed_aviso.add_field(
                name="👤 Autor do ticket",
                value=f"<@{dono_id}>" if dono_id else "Desconhecido",
                inline=True,
            )
            embed_aviso.add_field(
                name="🎩 Atendente",
                value=f"<@{atendente_id}>" if atendente_id else "Não assumido",
                inline=True,
            )
            await canal.send(embed=embed_aviso, view=ViewDeletarTicketAdmin())

    except Exception as e:
        print(f"[FECHAR] ERRO INESPERADO: {e}")
        logger.error(f"Erro inesperado ao fechar ticket {canal.name}: {e}", exc_info=True)

    finally:
        TicketState.desmarcar_fechando(canal.id)


class ViewAcoesTicket(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Assumir Atendimento",
        style=discord.ButtonStyle.green,
        emoji="🎩",
        custom_id="ticket_v2_assumir",
    )
    async def btn_assumir(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        canal = interaction.channel
        tipo  = _extrair_tipo_ticket(canal.topic or "")

        if not tem_permissao_categoria(interaction.user, tipo or ""):
            await interaction.response.send_message(
                "❌ Apenas a equipe pode assumir este atendimento.",
                ephemeral=True,
            )
            return

        try:
            novo_topic = _marcar_atendente_no_topic(canal.topic or "", interaction.user.id)
            await canal.edit(topic=novo_topic, reason=f"Ticket assumido por {interaction.user}")
        except discord.HTTPException as e:
            logger.warning(f"Não foi possível marcar atendente no tópico do ticket: {e}")

        msg = interaction.message
        if not msg or not msg.embeds:
            await interaction.response.send_message(
                "❌ Embed do ticket não encontrado.",
                ephemeral=True,
            )
            return

        embed_old = msg.embeds[0]

        nova_descricao = re.sub(
            r"⏳ \*\*Status:\*\* `.+?`",
            f"🟢 **Status:** `Em atendimento por {interaction.user.display_name}`",
            embed_old.description or "",
        )

        novo_embed = discord.Embed(
            title=embed_old.title,
            description=nova_descricao,
            color=CONFIG.COR_VERDE,
        )
        if embed_old.thumbnail:
            novo_embed.set_thumbnail(url=embed_old.thumbnail.url)
        if embed_old.image:
            novo_embed.set_image(url=embed_old.image.url)
        novo_embed.set_footer(
            text=f"Assumido por {interaction.user.display_name} • Nebularis"
        )

        button.disabled = True
        button.label    = "Em Atendimento"
        await msg.edit(embed=novo_embed, view=self)

        await interaction.response.send_message(
            f"🎩 **{interaction.user.mention}** assumiu este atendimento.",
        )

    @discord.ui.button(
        label="Chamar Staff",
        style=discord.ButtonStyle.primary,
        emoji="📢",
        custom_id="ticket_v2_chamar_staff",
    )
    async def btn_chamar_staff(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        pode, restante = TicketState.pode_chamar_staff(interaction.channel.id)

        if not pode:
            mins = restante // 60
            segs = restante % 60
            tempo_fmt = f"{mins}min {segs}s" if mins else f"{segs}s"
            await interaction.response.send_message(
                f"⏳ A staff já foi chamada recentemente. "
                f"Aguarde **{tempo_fmt}** para chamar novamente.",
                ephemeral=True,
            )
            return

        TicketState.registrar_chamar_staff(interaction.channel.id)

        mencoes = " ".join(f"<@&{cid}>" for cid in CONFIG.CARGOS_CHAMAR_STAFF)

        embed = discord.Embed(
            title="📢 Staff Chamada",
            description=(
                f"O usuário **{interaction.user.mention}** precisa de atenção neste ticket.\n"
                f"📁 Canal: {interaction.channel.mention}"
            ),
            color=CONFIG.COR_DOURADO,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text="Nebularis • Sistema de Tickets")

        await interaction.response.send_message(
            content=mencoes,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

    @discord.ui.button(
        label="Painel Restrito",
        style=discord.ButtonStyle.secondary,
        emoji="⚙️",
        custom_id="ticket_v2_painel",
    )
    async def btn_painel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        canal = interaction.channel
        tipo  = _extrair_tipo_ticket(canal.topic or "")

        if not tem_permissao_categoria(interaction.user, tipo or ""):
            await interaction.response.send_message(
                "❌ Acesso negado. Este painel é exclusivo para a equipe.",
                ephemeral=True,
            )
            return

        topic        = canal.topic or "Sem tópico definido"
        dono_id      = _extrair_dono_id(topic)
        dono_mention = f"<@{dono_id}>" if dono_id else "Desconhecido"

        cargos_acesso = list(CONFIG.CARGOS_ATENDIMENTO_IDS)
        if tipo:
            cargos_acesso += CONFIG.CARGOS_POR_CATEGORIA.get(tipo, [])
        cargos_acesso = list(dict.fromkeys(cargos_acesso))

        embed = discord.Embed(
            title="⚙️ Painel Restrito",
            color=CONFIG.COR_AZUL,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="📁 Canal",  value=canal.mention,  inline=True)
        embed.add_field(name="👤 Dono",   value=dono_mention,   inline=True)
        embed.add_field(
            name="🏷️ Categoria",
            value=f"`{tipo or 'desconhecida'}`",
            inline=True,
        )
        embed.add_field(
            name="🕒 Aberto em",
            value=f"<t:{int(canal.created_at.timestamp())}:f>",
            inline=True,
        )
        embed.add_field(
            name="⏳ Duração",
            value=f"`{formatar_duracao(int((datetime.now(timezone.utc) - canal.created_at).total_seconds()))}`",
            inline=True,
        )
        embed.add_field(
            name="👥 Equipe com acesso",
            value="\n".join(f"<@&{cid}>" for cid in cargos_acesso) or "Nenhum",
            inline=False,
        )
        embed.set_footer(text=f"Acessado por {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Fechar Ticket",
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="ticket_v2_fechar",
    )
    async def btn_fechar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        topic_dono_id = _extrair_dono_id(interaction.channel.topic or "")
        e_dono  = topic_dono_id == interaction.user.id
        e_staff = tem_permissao(interaction.user)

        if not (e_dono or e_staff):
            await interaction.response.send_message(
                "❌ Apenas o dono do ticket ou a equipe pode fechar este atendimento.",
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
                "• O canal só será removido após a avaliação ou pelo botão de admin.\n\n"
                "Esta ação encerra o atendimento."
            ),
            color=CONFIG.COR_VERMELHO,
        )
        await interaction.response.send_message(
            embed=embed,
            view=ViewConfirmarFechamento(),
            ephemeral=True,
        )


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
            f"Aberto em: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} UTC"
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
                f"✨ Olá {user.mention}, bem-vindo ao atendimento da **Nebularis**!\n\n"
                "Descreva sua solicitação com calma e aguarde enquanto a equipe se prepara.\n"
                "Envie prints ou provas se for necessário e evite menções desnecessárias.\n\n"
                f"⏳ **Status:** `Aguardando atendimento`"
            ),
            color=info["cor"],
            timestamp=datetime.now(timezone.utc),
        )
        embed_ticket.add_field(name="🛰️ Categoria", value=info["nivel"], inline=True)
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
        embed_ticket.set_footer(text="Nebularis • Sistema de Tickets")

        msg_painel = await canal.send(
            content=f"{user.mention} {mencoes_staff}",
            embed=embed_ticket,
            view=ViewAcoesTicket(),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )

        # NOVO: guarda o ID da mensagem do painel no tópico — usado pelo monitor de SLA
        try:
            await canal.edit(topic=f"{topic} | MSGID:{msg_painel.id}")
        except discord.HTTPException as e:
            logger.warning(f"Não foi possível salvar MSGID no tópico: {e}")

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
        bot.loop.create_task(inicializar_banco_avaliacoes())
        bot.add_view(ViewPainelTickets())
        bot.add_view(ViewAcoesTicket())
        bot.add_view(ViewConfirmarFechamento())
        self.monitorar_sla.start()

    def cog_unload(self):
        self.monitorar_sla.cancel()

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
            f"Aberto em: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} UTC"
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
        embed_reabertura.set_footer(text="Nebularis • Sistema de Tickets")

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
            title="**Nebularis — Sistema de Atendimento**",
            description=(
                "<:35721purplechance:1518149219645657201> **| HORÁRIO DE FUNCIONAMENTO**\n"
                "**Segunda a sexta:** 08:00 às 23:00.\n"
                "**Sábado e Domingo:** 10:00 às 18:00.\n\n"
                "<:41145star:1518149258241642647> **| AVISOS IMPORTANTES**\n"
                "- Evite abrir tickets fora do horário de atendimento.\n"
                "- Forneça o máximo de detalhes possível para agilizar o atendimento.\n"
                "-# Membros que abrirem tickets sem motivo serão penalizados.\n"
            ),
            color=CONFIG.COR_DOURADO,
            timestamp=datetime.now(timezone.utc),
        )
        if CONFIG.BANNER_PAINEL:
            embed.set_image(url=CONFIG.BANNER_PAINEL)
        embed.set_footer(text="Nebularis • Atendimento oficial")

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
                "• O canal só será removido após a avaliação ou pelo botão de admin.\n\n"
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
        emoji_patente = PATENTE_EMOJI.get(patente, "🗡️")

        embed = discord.Embed(
            title="📊 Reputação do Atendente",
            description=(
                f"👤 **Atendente:** {atendente.mention}\n"
                f"{emoji_patente} **Patente:** `{patente}`\n"
                f"⭐ **Média:** `{media:.2f}/5`\n"
                f"📋 **Avaliações:** `{total}`\n"
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
        embed.set_footer(text="Nebularis • Reputação da Equipe")

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
        emoji_patente = PATENTE_EMOJI.get(patente, "🗡️")

        proxima_info = ""
        if total < 5:
            proxima_info = f"Faltam `{5 - total}` avaliações para sair de Aprendiz."
        elif patente != "Lenda de Musashi":
            proxima_info = "Continue mantendo a qualidade do atendimento para evoluir."

        embed = discord.Embed(
            title=f"{emoji_patente} Sua Patente: {patente}",
            description=(
                f"⭐ **Média:** `{media:.2f}/5`\n"
                f"📋 **Avaliações:** `{total}`\n\n"
                f"{_classificacao_media(media) if total else 'Continue atendendo para evoluir sua patente!'}\n\n"
                f"{proxima_info}"
            ),
            color=CONFIG.COR_DOURADO,
        )
        embed.set_footer(text="Nebularis • Caminho do Espadachim")
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
            emoji_patente = PATENTE_EMOJI.get(patente, "🗡️")
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
        embed.set_footer(text="Nebularis • Qualidade de Atendimento")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(CogTickets(bot))
    logger.info("CogTickets carregado com sucesso.")