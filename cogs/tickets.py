import discord
from discord.ext import commands
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

    BANNER_PAINEL  = "https://cdn.discordapp.com/attachments/961677475191078992/1508334091190407208/content.png"
    BANNER_FECHADO = "https://cdn.discordapp.com/attachments/961677475191078992/1508334620251262976/content.png"

    IMAGENS: dict[str, str] = {
        "duvida":     "https://cdn.discordapp.com/attachments/961677475191078992/1508337815467986984/image.png",
        "denuncia":   "https://cdn.discordapp.com/attachments/961677475191078992/1508337901241499728/image.png",
        "patrocinio": "https://cdn.discordapp.com/attachments/961677475191078992/1508337978878201916/image.png",
        "outros":     "https://cdn.discordapp.com/attachments/961677475191078992/1508338084796956822/image.png",
    }

    THUMBNAILS: dict[str, str] = {
        "duvida":     "https://media.tenor.com/3Fss9H6cQZwAAAAi/laughing-cuphead.gif",
        "denuncia":   "https://media.tenor.com/3Fss9H6cQZwAAAAi/laughing-cuphead.gif",
        "patrocinio": "https://media.tenor.com/3Fss9H6cQZwAAAAi/laughing-cuphead.gif",
        "outros":     "https://media.tenor.com/3Fss9H6cQZwAAAAi/laughing-cuphead.gif",
    }

    COR_VERMELHO = discord.Color.from_rgb(180, 50,  40)
    COR_AZUL     = discord.Color.from_rgb(40,  105, 160)
    COR_DOURADO  = discord.Color.from_rgb(215, 165, 75)
    COR_VERDE    = discord.Color.from_rgb(75,  135, 70)
    COR_ROXO     = discord.Color.from_rgb(110, 70,  160)
    COR_ESCURO   = discord.Color.from_rgb(35,  30,  25)
    COR_CINZA    = discord.Color.from_rgb(80,  80,  80)

    CATEGORIAS: dict[str, dict] = {
        "duvida": {
            "label":       "Dúvidas",
            "description": "Tire suas dúvidas com a equipe.",
            "emoji":       "<:duvidas:1508327310653263934>",
            "titulo":      "<:duvidas:1508327310653263934> Dúvidas — Balcão do Estúdio",
            "nivel":       "🔵 Suporte Geral",
            "cor":         discord.Color.from_rgb(40, 105, 160),
            "nome_canal":  "duvida",
        },
        "denuncia": {
            "label":       "Denúncias",
            "description": "Reporte algo irregular com provas.",
            "emoji":       "<:denuncias:1508327388570980473>",
            "titulo":      "<:denuncias:1508327388570980473> Denúncia — Alerta no Estúdio",
            "nivel":       "🔴 Prioridade Alta",
            "cor":         discord.Color.from_rgb(180, 50, 40),
            "nome_canal":  "denuncia",
        },
        "patrocinio": {
            "label":       "Patrocínios",
            "description": "Parcerias e propostas comerciais.",
            "emoji":       "<:pat:1508327666485297213>",
            "titulo":      "<:pat:1508327666485297213> Patrocínio — Sala de Reuniões",
            "nivel":       "🟡 Proposta Comercial",
            "cor":         discord.Color.from_rgb(215, 165, 75),
            "nome_canal":  "patrocinio",
        },
        "outros": {
            "label":       "Outros",
            "description": "Assuntos que não se encaixam acima.",
            "emoji":       "<:outros:1508327748102520852>",
            "titulo":      "<:outros:1508327748102520852> Outros — Arquivo Geral",
            "nivel":       "⚪ Atendimento Geral",
            "cor":         discord.Color.from_rgb(80, 80, 80),
            "nome_canal":  "outros",
        },
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
):
    await inicializar_banco_avaliacoes()
    conn = await _abrir_conexao_postgres()
    try:
        await conn.execute(
            """
            INSERT INTO ticket_avaliacoes
            (ticket_id, ticket_nome, guild_id, usuario_id, atendente_id, nota, transcript_url, criado_em)
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            ON CONFLICT (ticket_id) DO UPDATE SET
                ticket_nome = EXCLUDED.ticket_nome,
                guild_id = EXCLUDED.guild_id,
                usuario_id = EXCLUDED.usuario_id,
                atendente_id = EXCLUDED.atendente_id,
                nota = EXCLUDED.nota,
                transcript_url = EXCLUDED.transcript_url,
                criado_em = NOW()
            """,
            ticket_id,
            ticket_nome,
            guild_id,
            usuario_id,
            atendente_id,
            nota,
            transcript_url,
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

def _encontrar_ticket_do_usuario(
    guild: discord.Guild,
    user_id: int,
) -> discord.TextChannel | None:
    for ch in guild.text_channels:
        if ch.topic and f"DONO:{user_id}" in ch.topic:
            return ch
    return None



async def gerar_transcript_texto(channel: discord.TextChannel) -> tuple[str, int]:
    """Retorna (conteúdo_txt, total_mensagens)."""
    linhas = [
        "=" * 64,
        f"  TRANSCRIPT — {channel.name.upper()}",
        f"  Gerado em: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S')} UTC",
        f"  Família Sant's • Sistema de Tickets",
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



class ViewAvaliarAtendimento(discord.ui.View):

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
        embed.set_footer(text="Família Sant's • Avaliação de Atendimento")

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
            embed_publico.set_footer(text="Família Sant's • Reputação da Equipe")
            await canal_avaliacoes.send(embed=embed_publico)

        canal_ticket = interaction.channel
        if isinstance(canal_ticket, discord.TextChannel) and canal_ticket.topic and "DONO:" in canal_ticket.topic:
            await asyncio.sleep(2)
            try:
                await canal_ticket.delete(reason=f"Ticket avaliado por {interaction.user}")
            except discord.HTTPException as e:
                logger.warning(f"Falha ao deletar ticket após avaliação: {e}")


class ViewPosFechamento(discord.ui.View):

    def __init__(
        self,
        *,
        ticket_id: int,
        ticket_nome: str,
        usuario_id: int | None,
        atendente_id: int | None,
        transcript_url: str | None,
    ):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
        self.ticket_nome = ticket_nome
        self.usuario_id = usuario_id
        self.atendente_id = atendente_id
        self.transcript_url = transcript_url

    @discord.ui.button(
        label="Liberar Avaliação",
        style=discord.ButtonStyle.success,
        emoji="⭐",
        custom_id="ticket_v2_liberar_avaliacao",
    )
    async def btn_liberar_avaliacao(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas administradores podem liberar a avaliação.",
                ephemeral=True,
            )
            return

        if not self.usuario_id or not self.atendente_id:
            await interaction.response.send_message(
                "❌ Não foi possível liberar a avaliação. O ticket precisa ter dono e atendente assumido.",
                ephemeral=True,
            )
            return

        if self.usuario_id == self.atendente_id:
            await interaction.response.send_message(
                "❌ O dono do ticket não pode ser o próprio atendente.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="⭐ Avaliação de Atendimento",
            description=(
                f"<@{self.usuario_id}>, avalie o atendimento recebido.\n\n"
                f"**Atendente:** <@{self.atendente_id}>\n"
                f"**Ticket:** `{self.ticket_nome}`\n\n"
                "Escolha uma nota de **1 a 5 estrelas**. Após a avaliação, este ticket será deletado automaticamente."
            ),
            color=CONFIG.COR_DOURADO,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="1 ⭐", value="Ruim", inline=True)
        embed.add_field(name="3 ⭐", value="Regular", inline=True)
        embed.add_field(name="5 ⭐", value="Excelente", inline=True)
        if self.transcript_url:
            embed.add_field(
                name="📋 Transcript",
                value=f"[Ver registro do ticket]({self.transcript_url})",
                inline=False,
            )
        embed.set_footer(text="Família Sant's • Sistema de Avaliações")

        button.disabled = True
        button.label = "Avaliação Liberada"
        await interaction.message.edit(view=self)

        await interaction.response.send_message(
            content=f"<@{self.usuario_id}>",
            embed=embed,
            view=ViewAvaliarAtendimento(
                ticket_id=self.ticket_id,
                ticket_nome=self.ticket_nome,
                usuario_id=self.usuario_id,
                atendente_id=self.atendente_id,
                transcript_url=self.transcript_url,
            ),
            allowed_mentions=discord.AllowedMentions(users=True),
        )

    @discord.ui.button(
        label="Deletar Ticket",
        style=discord.ButtonStyle.danger,
        emoji="🗑️",
        custom_id="ticket_v2_deletar_imediato",
    )
    async def btn_deletar_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas administradores podem deletar o ticket.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "🗑️ Ticket deletado.",
            ephemeral=True,
        )
        try:
            await interaction.channel.delete(reason=f"Ticket deletado por {interaction.user}")
        except discord.HTTPException as e:
            logger.warning(f"Falha ao deletar ticket: {e}")


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
            embed_log.set_thumbnail(url=interaction.user.display_avatar.url)
            embed_log.set_image(url=CONFIG.BANNER_FECHADO)
            embed_log.set_footer(text="Família Sant's • Sistema de Tickets")

            # Botão de link para o transcript (se disponível)
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
                "✅ Ticket encerrado. A avaliação foi enviada no canal do ticket.",
                ephemeral=True,
            )
        except discord.HTTPException as e:
            print(f"[FECHAR] Não foi possível enviar followup: {e}")

        if dono_id and atendente_id and dono_id != atendente_id:
            embed_avaliacao = discord.Embed(
                title="⭐ Avalie o Atendimento",
                description=(
                    f"<@{dono_id}>, seu ticket foi encerrado por **{interaction.user.display_name}**.\n\n"
                    f"**Atendente:** <@{atendente_id}>\n"
                    f"**Ticket:** `{canal.name}`\n\n"
                    "Escolha uma nota de **1 a 5 estrelas** para registrar a qualidade do atendimento.\n"
                    "Após a avaliação, o ticket será deletado automaticamente.\n\n"
                    "Administradores também podem usar o botão **Deletar Ticket** para apagar o canal imediatamente."
                ),
                color=CONFIG.COR_DOURADO,
                timestamp=fechado_em,
            )
            embed_avaliacao.add_field(name="1 ⭐", value="Ruim", inline=True)
            embed_avaliacao.add_field(name="3 ⭐", value="Regular", inline=True)
            embed_avaliacao.add_field(name="5 ⭐", value="Excelente", inline=True)
            if link_transcript:
                embed_avaliacao.add_field(
                    name="📋 Transcript",
                    value=f"[Ver registro do ticket]({link_transcript})",
                    inline=False,
                )
            embed_avaliacao.set_footer(text="Família Sant's • Sistema de Avaliações")

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
        canal = interaction.channel
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
            text=f"Assumido por {interaction.user.display_name} • Família Sant's"
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
        embed.set_footer(text="Família Sant's • Sistema de Tickets")

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
        embed.add_field(name="📋 Tópico", value=f"`{topic}`", inline=False)
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
                "• O painel de avaliação será enviado no canal.\n"
                "• O canal só será deletado após a avaliação ou pelo botão de admin.\n\n"
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
                f"🎬 Olá {user.mention}, bem-vindo ao atendimento da **Família Sant's**!\n\n"
                "Seu ticket foi aberto com sucesso. Descreva sua solicitação com calma "
                "e aguarde enquanto nossa equipe prepara o atendimento.\n\n"
                "**📜 Orientações:**\n"
                "• Explique claramente o motivo do ticket.\n"
                "• Envie prints, provas ou informações relevantes se necessário.\n"
                "• Evite spam e menções desnecessárias.\n"
                "• Aguarde pacientemente a equipe responder.\n\n"
                f"🎟️ **Categoria:** {info['titulo']}\n"
                f"⭐ **Nível:** `{info['nivel']}`\n"
                f"👤 **Solicitante:** {user.mention}\n"
                f"🕒 **Aberto em:** <t:{int(datetime.now(timezone.utc).timestamp())}:f>\n"
                f"⏳ **Status:** `Aguardando atendimento`"
            ),
            color=info["cor"],
            timestamp=datetime.now(timezone.utc),
        )

        imagem    = CONFIG.IMAGENS.get(tipo)
        thumbnail = CONFIG.THUMBNAILS.get(tipo)
        if thumbnail: embed_ticket.set_thumbnail(url=thumbnail)
        if imagem:    embed_ticket.set_image(url=imagem)
        embed_ticket.set_footer(text="Família Sant's • Sistema de Tickets")

        await canal.send(
            content=f"{user.mention} {mencoes_staff}",
            embed=embed_ticket,
            view=ViewAcoesTicket(),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )

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

    @app_commands.command(
        name="ticket",
        description="Envia o painel de tickets no canal atual.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def cmd_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="<a:CUPCHILL:1502354528802963538> Família Sant's — Sistema de Atendimento",
            description=(
                "Bem-vindo ao balcão oficial de atendimento da **Família Sant's**.\n\n"
                "Selecione uma categoria abaixo para abrir seu ticket.\n"
                "Nossa equipe irá atendê-lo assim que possível.\n\n"
                "<:duvidas:1508327310653263934> **Dúvidas** — tire suas dúvidas gerais com a equipe.\n"
                "<:denuncias:1508327388570980473> **Denúncias** — reporte irregularidades com provas.\n"
                "<:pat:1508327666485297213> **Patrocínios** — parcerias e propostas comerciais.\n"
                "<:outros:1508327748102520852> **Outros** — assuntos que não se encaixam acima.\n\n"
                "🎞️ Use o menu abaixo para começar."
            ),
            color=CONFIG.COR_DOURADO,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_image(url=CONFIG.BANNER_PAINEL)
        embed.set_footer(text="Família Sant's • Atendimento oficial")

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
                "• O painel de avaliação será enviado no canal.\n"
                "• O canal só será deletado após a avaliação ou pelo botão de admin.\n\n"
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

        embed = discord.Embed(
            title="📊 Reputação do Atendente",
            description=(
                f"👤 **Atendente:** {atendente.mention}\n"
                f"⭐ **Média:** `{media:.2f}/5`\n"
                f"📋 **Avaliações:** `{total}`\n"
                f"🏷️ **Classificação:** {_classificacao_media(media) if total else 'Sem avaliações ainda'}"
            ),
            color=CONFIG.COR_AZUL,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_thumbnail(url=atendente.display_avatar.url)
        embed.set_footer(text="Família Sant's • Reputação da Equipe")

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
            linhas.append(
                f"{prefixo} <@{atendente_id}> — **{media:.2f}/5** • `{total}` avaliações"
            )

        embed = discord.Embed(
            title="🏆 Ranking de Atendentes",
            description="\n".join(linhas),
            color=CONFIG.COR_DOURADO,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text="Família Sant's • Qualidade de Atendimento")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(CogTickets(bot))
    logger.info("CogTickets carregado com sucesso.")