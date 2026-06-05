import discord
from discord.ext import commands
from discord import app_commands
from io import BytesIO
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import asyncio
import re
import logging

logger = logging.getLogger("tickets")

class CONFIG:
   
    CATEGORIA_TICKETS_ID    = 1495288098010169574
    CANAL_LOG_ID            = 1495272331558391818

    # Quem podem atenter as bençãos - Sants e Bruna 💖
    CARGOS_ATENDIMENTO_IDS = [
        1487560221202321600,
        1505759604842434651,
        1480381506064093225,
        1500545846427652166,
        1501356975491907664,
        1502717285528506536,
    ]

   
    CARGOS_CHAMAR_STAFF = [
        1507901138396123166, 
           
    ]

   
    COOLDOWN_CHAMAR_STAFF_SEGUNDOS = 100
    COOLDOWN_ABRIR_TICKET_SEGUNDOS = 10     

    BANNER_PAINEL          = "https://cdn.discordapp.com/attachments/961677475191078992/1508334091190407208/content.png?ex=6a152916&is=6a13d796&hm=aa521ddcfacb82a3e26124e7ef41e86ea175cffa9b5decf602650519d7fd2869&"
    BANNER_FECHADO         = "https://cdn.discordapp.com/attachments/961677475191078992/1508334620251262976/content.png?ex=6a152994&is=6a13d814&hm=fbfac73eaad884fd2d3f3630b0fd85087cbde0ee881a4c93f403f2e0926313a8&"

    IMAGENS = {
        "duvida":      "https://cdn.discordapp.com/attachments/961677475191078992/1508337815467986984/image.png?ex=6a152c8e&is=6a13db0e&hm=3d7d418a5a837bd8a5a3846c9965679a851845110ae479cffe03effaff9c7def&",
        "denuncia":    "https://cdn.discordapp.com/attachments/961677475191078992/1508337901241499728/image.png?ex=6a152ca3&is=6a13db23&hm=7e9b118ad605a65e7a442f965c64a93c6814165aa1d0a6cb10d0ca73a27f55ef&",
        "patrocinio":  "https://cdn.discordapp.com/attachments/961677475191078992/1508337978878201916/image.png?ex=6a152cb5&is=6a13db35&hm=bb177fb4ed6a305d105858e8f7595c7ca96a97d19c33f30b9ee8ef5a820f7545&",
        "outros":      "https://cdn.discordapp.com/attachments/961677475191078992/1508338084796956822/image.png?ex=6a152cce&is=6a13db4e&hm=5f7b7c852f61c221e79e537１fb６２１９ad３２０e５６a３７dffa４efc０１１９３a４f１ea８e３a&",
    }

    THUMBNAILS = {
        "duvida":      "https://media.tenor.com/3Fss9H6cQZwAAAAi/laughing-cuphead.gif",
        "denuncia":    "https://media.tenor.com/3Fss9H6cQZwAAAAi/laughing-cuphead.gif",
        "patrocinio":  "https://media.tenor.com/3Fss9H6cQZwAAAAi/laughing-cuphead.gif",
        "outros":      "https://media.tenor.com/3Fss9H6cQZwAAAAi/laughing-cuphead.gif",
    }

    #  Paletas
    COR_VERMELHO  = discord.Color.from_rgb(180, 50,  40)
    COR_AZUL      = discord.Color.from_rgb(40,  105, 160)
    COR_DOURADO   = discord.Color.from_rgb(215, 165, 75)
    COR_VERDE     = discord.Color.from_rgb(75,  135, 70)
    COR_ROXO      = discord.Color.from_rgb(110, 70,  160)
    COR_ESCURO    = discord.Color.from_rgb(35,  30,  25)
    COR_CINZA     = discord.Color.from_rgb(80,  80,  80)

    CATEGORIAS = {
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
    """Transforma um texto em slug seguro para nome de canal Discord."""
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9\-]", "-", texto)
    texto = re.sub(r"-{2,}", "-", texto)
    return texto.strip("-")[:80]


def tem_permissao(member: discord.Member) -> bool:
    """Retorna True se o membro é administrador ou possui cargo de atendimento."""
    if member.guild_permissions.administrator:
        return True
    return any(r.id in CONFIG.CARGOS_ATENDIMENTO_IDS for r in member.roles)


def formatar_duracao(segundos: int) -> str:
    """Formata segundos em string legível (ex: 2h 15min)."""
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

async def gerar_transcript_txt(channel: discord.TextChannel):
    """Gera o transcript em .txt e retorna (File, total_msgs)."""
    linhas = [
        "=" * 64,
        f"  TRANSCRIPT — {channel.name.upper()}",
        f"  Gerado em: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S')} UTC",
        "=" * 64,
        "",
    ]
    total = 0
    async for msg in channel.history(limit=None, oldest_first=True):
        total += 1
        data   = msg.created_at.strftime("%d/%m/%Y %H:%M")
        autor  = f"{msg.author} ({msg.author.id})"
        corpo  = msg.content or "[Sem texto]"
        if msg.attachments:
            corpo += "\n  Anexos:\n  " + "\n  ".join(a.url for a in msg.attachments)
        if msg.embeds:
            corpo += f"\n  [Embed: {msg.embeds[0].title or 'sem título'}]"
        linhas.append(f"[{data}] {autor}")
        linhas.append(f"  {corpo}")
        linhas.append("")

    if total == 0:
        linhas.append("Nenhuma mensagem registrada neste ticket.")

    conteudo = "\n".join(linhas).encode("utf-8")
    buf = BytesIO(conteudo)
    buf.seek(0)
    nome = f"transcript-{slug(channel.name)}.txt"
    return discord.File(buf, filename=nome), total


async def gerar_transcript_html(channel: discord.TextChannel) -> discord.File:
    """Gera o transcript em .html com visual bonito."""
    mensagens_html = []
    async for msg in channel.history(limit=None, oldest_first=True):
        data      = msg.created_at.strftime("%d/%m/%Y %H:%M")
        avatar    = msg.author.display_avatar.url
        nome      = discord.utils.escape_mentions(str(msg.author))
        conteudo  = discord.utils.escape_mentions(msg.content) if msg.content else ""
        conteudo  = conteudo.replace("\n", "<br>")

        anexos_html = ""
        for a in msg.attachments:
            if a.content_type and a.content_type.startswith("image/"):
                anexos_html += f'<img src="{a.url}" style="max-width:360px;border-radius:6px;margin-top:6px;">'
            else:
                anexos_html += f'<a href="{a.url}" target="_blank">📎 {a.filename}</a>'

        cor_nome = "#5865f2" if not msg.author.bot else "#57f287"
        mensagens_html.append(f"""
        <div class="msg">
          <img class="avatar" src="{avatar}" alt="">
          <div class="content">
            <span class="nome" style="color:{cor_nome}">{nome}</span>
            <span class="ts">{data}</span>
            <p class="body">{conteudo}</p>
            {anexos_html}
          </div>
        </div>""")

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Transcript — {channel.name}</title>
<style>
  :root {{
    --bg: #1e1f22; --surface: #2b2d31; --border: #3b3d43;
    --text: #dbdee1; --muted: #80848e;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif;
         font-size: 15px; padding: 24px; }}
  header {{ background: var(--surface); border-radius: 10px; padding: 20px 28px;
            margin-bottom: 24px; border: 1px solid var(--border); }}
  header h1 {{ font-size: 20px; font-weight: 700; color: #fff; }}
  header p  {{ color: var(--muted); font-size: 13px; margin-top: 4px; }}
  .msg {{ display: flex; gap: 14px; padding: 10px 0;
          border-bottom: 1px solid #2e2e33; }}
  .msg:last-child {{ border-bottom: none; }}
  .avatar {{ width: 40px; height: 40px; border-radius: 50%;
             flex-shrink: 0; margin-top: 2px; }}
  .nome   {{ font-weight: 600; font-size: 14px; }}
  .ts     {{ color: var(--muted); font-size: 11px; margin-left: 8px; }}
  .body   {{ margin-top: 4px; line-height: 1.5; color: var(--text); }}
  a       {{ color: #00aff4; }}
  img     {{ display: block; }}
</style>
</head>
<body>
<header>
  <h1>📋 Transcript — #{channel.name}</h1>
  <p>Gerado em {datetime.now(timezone.utc).strftime('%d/%m/%Y às %H:%M UTC')} •
     Família Sant's Sistema de Tickets</p>
</header>
{"".join(mensagens_html) or "<p style='color:var(--muted)'>Nenhuma mensagem registrada.</p>"}
</body>
</html>"""

    buf = BytesIO(html.encode("utf-8"))
    buf.seek(0)
    nome = f"transcript-{slug(channel.name)}.html"
    return discord.File(buf, filename=nome)

class TicketState:
    """Estado compartilhado entre views persistentes."""
    _ultimo_chamar_staff: dict[int, datetime] = {}  # channel_id → datetime

    @classmethod
    def pode_chamar_staff(cls, channel_id: int) -> tuple[bool, int]:
        """Retorna (pode_chamar, segundos_restantes)."""
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

class ViewConfirmarFechamento(discord.ui.View):
    """Modal de confirmação antes de fechar o ticket."""

    def __init__(self):
        super().__init__(timeout=60)

    
    @discord.ui.button(
        label="Confirmar Fechamento",
        style=discord.ButtonStyle.red,
        emoji="🔒"
    )
    async def btn_confirmar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        canal = interaction.channel

        # Verifica se quem fecha é dono ou staff
        topic_dono_id = _extrair_dono_id(canal.topic or "")
        e_dono  = topic_dono_id == interaction.user.id
        e_staff = tem_permissao(interaction.user)

        if not (e_dono or e_staff):
            await interaction.response.send_message(
                "❌ Apenas o dono do ticket ou a equipe pode fechar este atendimento.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # ── Gera transcript ────────────────────────────────────────
        arquivo_txt,  total_msgs = await gerar_transcript_txt(canal)
        arquivo_html             = await gerar_transcript_html(canal)

        log = interaction.guild.get_channel(CONFIG.CANAL_LOG_ID)

        criado_em  = canal.created_at
        fechado_em = datetime.now(timezone.utc)
        duracao    = formatar_duracao(int((fechado_em - criado_em).total_seconds()))

        link_txt = link_html = None

        if log:
            # Envia os dois arquivos de transcript
            msg_txt  = await log.send(file=arquivo_txt)
            msg_html = await log.send(file=arquivo_html)
            link_txt  = msg_txt.attachments[0].url
            link_html = msg_html.attachments[0].url

            embed_log = discord.Embed(
                title="🔒 Ticket Encerrado",
                description=(
                    "O atendimento foi finalizado e o registro foi salvo.\n"
                    "Use os botões abaixo para acessar os transcripts."
                ),
                color=CONFIG.COR_DOURADO,
                timestamp=fechado_em
            )
            embed_log.add_field(name="👤 Fechado por",   value=interaction.user.mention, inline=True)
            embed_log.add_field(name="📁 Canal",         value=f"`{canal.name}`",       inline=True)
            embed_log.add_field(name="⏳ Duração",       value=f"`{duracao}`",           inline=True)
            embed_log.add_field(name="💬 Mensagens",     value=f"`{total_msgs}`",        inline=True)
            embed_log.add_field(
                name="🕒 Aberto em",
                value=f"<t:{int(criado_em.timestamp())}:f>",
                inline=True
            )
            embed_log.add_field(
                name="🔒 Fechado em",
                value=f"<t:{int(fechado_em.timestamp())}:f>",
                inline=True
            )
            embed_log.set_thumbnail(url=interaction.user.display_avatar.url)
            embed_log.set_image(url=CONFIG.BANNER_FECHADO)
            embed_log.set_footer(text="Família Sant's • Sistema de Tickets")

            # View com links de download
            view_links = discord.ui.View(timeout=None)
            if link_txt:
                view_links.add_item(discord.ui.Button(
                    label="📄 Transcript .txt",
                    url=link_txt,
                    style=discord.ButtonStyle.link
                ))
            if link_html:
                view_links.add_item(discord.ui.Button(
                    label="🌐 Transcript .html",
                    url=link_html,
                    style=discord.ButtonStyle.link
                ))

            await msg_html.edit(embed=embed_log, view=view_links)

        # ── Avisa no canal e deleta ────────────────────────────────
        embed_aviso = discord.Embed(
            title="🔒 Ticket Encerrado",
            description=(
                f"Este ticket foi fechado por **{interaction.user.display_name}**.\n"
                "O canal será deletado em **5 segundos**."
            ),
            color=CONFIG.COR_ESCURO
        )
        await canal.send(embed=embed_aviso)
        await asyncio.sleep(5)

        try:
            await canal.delete(reason=f"Ticket fechado por {interaction.user}")
        except discord.HTTPException as e:
            logger.warning(f"Falha ao deletar canal {canal.name}: {e}")

    # ── Cancelar ───────────────────────────────────────────────────
    @discord.ui.button(
        label="Cancelar",
        style=discord.ButtonStyle.gray,
        emoji="✖️"
    )
    async def btn_cancelar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "✅ Fechamento cancelado. O ticket continua aberto.",
            ephemeral=True
        )


# ─────────────────────────────────────────────────────────────────
#  VIEW: AÇÕES DO TICKET (persistente)
# ─────────────────────────────────────────────────────────────────

class ViewAcoesTicket(discord.ui.View):
    """Botões principais dentro do canal do ticket."""

    def __init__(self):
        super().__init__(timeout=None)

    # ── Assumir atendimento ────────────────────────────────────────
    @discord.ui.button(
        label="Assumir Atendimento",
        style=discord.ButtonStyle.green,
        emoji="🎩",
        custom_id="ticket_v2_assumir"
    )
    async def btn_assumir(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not tem_permissao(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas a equipe pode assumir este atendimento.",
                ephemeral=True
            )
            return

        msg = interaction.message
        if not msg or not msg.embeds:
            await interaction.response.send_message(
                "❌ Embed do ticket não encontrado.",
                ephemeral=True
            )
            return

        embed_old = msg.embeds[0]

        # Reescreve a linha de status
        nova_descricao = re.sub(
            r"⏳ \*\*Status:\*\* `.+?`",
            f"🟢 **Status:** `Em atendimento por {interaction.user.display_name}`",
            embed_old.description or ""
        )

        novo_embed = discord.Embed(
            title=embed_old.title,
            description=nova_descricao,
            color=CONFIG.COR_VERDE
        )
        if embed_old.thumbnail:
            novo_embed.set_thumbnail(url=embed_old.thumbnail.url)
        if embed_old.image:
            novo_embed.set_image(url=embed_old.image.url)
        novo_embed.set_footer(
            text=f"Assumido por {interaction.user.display_name} • Família Sant's"
        )

        button.disabled  = True
        button.label     = "Em Atendimento"
        await msg.edit(embed=novo_embed, view=self)

        await interaction.response.send_message(
            f"🎩 **{interaction.user.mention}** assumiu este atendimento.",
        )

    # ── Chamar Staff ───────────────────────────────────────────────
    @discord.ui.button(
        label="Chamar Staff",
        style=discord.ButtonStyle.primary,
        emoji="📢",
        custom_id="ticket_v2_chamar_staff"
    )
    async def btn_chamar_staff(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        pode, restante = TicketState.pode_chamar_staff(interaction.channel.id)

        if not pode:
            mins = restante // 60
            segs = restante % 60
            tempo_fmt = f"{mins}min {segs}s" if mins else f"{segs}s"
            await interaction.response.send_message(
                f"⏳ A staff já foi chamada recentemente. Aguarde **{tempo_fmt}** para chamar novamente.",
                ephemeral=True
            )
            return

        TicketState.registrar_chamar_staff(interaction.channel.id)

        mencoes = " ".join(f"<@&{cid}>" for cid in CONFIG.CARGOS_CHAMAR_STAFF)

        embed = discord.Embed(
            title="📢 Staff Chamada",
            description=(
                f"{mencoes}\n\n"
                f"O usuário **{interaction.user.mention}** precisa de atenção neste ticket.\n"
                f"📁 Canal: {interaction.channel.mention}"
            ),
            color=CONFIG.COR_DOURADO,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Família Sant's • Sistema de Tickets")

        await interaction.response.send_message(
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True)
        )

    # ── Painel Restrito ────────────────────────────────────────────
    @discord.ui.button(
        label="Painel Restrito",
        style=discord.ButtonStyle.secondary,
        emoji="⚙️",
        custom_id="ticket_v2_painel"
    )
    async def btn_painel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not tem_permissao(interaction.user):
            await interaction.response.send_message(
                "❌ Acesso negado. Este painel é exclusivo para a equipe.",
                ephemeral=True
            )
            return

        canal  = interaction.channel
        topic  = canal.topic or "Sem tópico definido"
        dono_id = _extrair_dono_id(topic)
        dono_mention = f"<@{dono_id}>" if dono_id else "Desconhecido"

        embed = discord.Embed(
            title="⚙️ Painel Restrito",
            color=CONFIG.COR_AZUL,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="📁 Canal",      value=canal.mention,  inline=True)
        embed.add_field(name="👤 Dono",       value=dono_mention,   inline=True)
        embed.add_field(
            name="🕒 Aberto em",
            value=f"<t:{int(canal.created_at.timestamp())}:f>",
            inline=True
        )
        embed.add_field(name="📋 Tópico",     value=f"`{topic}`",   inline=False)
        embed.add_field(
            name="👥 Equipe com acesso",
            value="\n".join(f"<@&{cid}>" for cid in CONFIG.CARGOS_ATENDIMENTO_IDS) or "Nenhum",
            inline=False
        )
        embed.set_footer(text=f"Acessado por {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Fechar Ticket ──────────────────────────────────────────────
    @discord.ui.button(
        label="Fechar Ticket",
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="ticket_v2_fechar"
    )
    async def btn_fechar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        topic_dono_id = _extrair_dono_id(interaction.channel.topic or "")
        e_dono  = topic_dono_id == interaction.user.id
        e_staff = tem_permissao(interaction.user)

        if not (e_dono or e_staff):
            await interaction.response.send_message(
                "❌ Apenas o dono do ticket ou a equipe pode fechar este atendimento.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🔒 Confirmar Fechamento",
            description=(
                "Tem certeza que deseja encerrar este atendimento?\n\n"
                "• O transcript será salvo automaticamente no canal de logs.\n"
                "• Este canal será **permanentemente deletado** após 5 segundos.\n\n"
                "Esta ação **não pode ser desfeita**."
            ),
            color=CONFIG.COR_VERMELHO
        )
        await interaction.response.send_message(
            embed=embed,
            view=ViewConfirmarFechamento(),
            ephemeral=True
        )


# ─────────────────────────────────────────────────────────────────
#  SELECT MENU DE CATEGORIAS
# ─────────────────────────────────────────────────────────────────

class SelectCategoriaTicket(discord.ui.Select):
    """Menu dropdown com as 4 categorias de ticket."""

    def __init__(self):
        opcoes = [
            discord.SelectOption(
                label=dados["label"],
                description=dados["description"],
                emoji=dados["emoji"],
                value=chave
            )
            for chave, dados in CONFIG.CATEGORIAS.items()
        ]
        super().__init__(
            placeholder="Selecione uma categoria para abrir seu ticket...",
            min_values=1,
            max_values=1,
            options=opcoes,
            custom_id="ticket_v2_select_categoria"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild    = interaction.guild
        user     = interaction.user
        tipo     = self.values[0]
        info     = CONFIG.CATEGORIAS[tipo]
        categoria = guild.get_channel(CONFIG.CATEGORIA_TICKETS_ID)

        # ── Verifica se já possui ticket aberto ───────────────────
        ticket_existente = _encontrar_ticket_do_usuario(guild, user.id)
        if ticket_existente:
            await interaction.followup.send(
                f"❌ Você já possui um ticket aberto: {ticket_existente.mention}\n"
                "Finalize o atendimento atual antes de abrir um novo.",
                ephemeral=True
            )
            return

        if categoria is None:
            await interaction.followup.send(
                "❌ Categoria de tickets não encontrada. Contate um administrador.",
                ephemeral=True
            )
            return

        # ── Permissões do canal ───────────────────────────────────
        overwrites = {
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

        # ── Cria o canal ──────────────────────────────────────────
        nome_canal = slug(f"{info['nome_canal']}-{user.name}")
        topic      = (
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
                reason=f"Ticket aberto por {user} — categoria: {tipo}"
            )
        except discord.HTTPException as e:
            logger.error(f"Erro ao criar canal de ticket: {e}")
            await interaction.followup.send(
                "❌ Não foi possível criar o canal do ticket. Tente novamente.",
                ephemeral=True
            )
            return

        # ── Menções de staff ──────────────────────────────────────
        mencoes_staff = " ".join(
            f"<@&{cid}>" for cid in CONFIG.CARGOS_ATENDIMENTO_IDS
        )

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
                f"⏳ **Status:** `Aguardando atendimento`\n\n"
                f"{mencoes_staff}"
            ),
            color=info["cor"],
            timestamp=datetime.now(timezone.utc)
        )

        imagem    = CONFIG.IMAGENS.get(tipo)
        thumbnail = CONFIG.THUMBNAILS.get(tipo)
        if thumbnail: embed_ticket.set_thumbnail(url=thumbnail)
        if imagem:    embed_ticket.set_image(url=imagem)
        embed_ticket.set_footer(text="Família Sant's • Sistema de Tickets")

        await canal.send(
            content=user.mention,
            embed=embed_ticket,
            view=ViewAcoesTicket(),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True)
        )

        await interaction.followup.send(
            f"✅ Ticket criado com sucesso! Acesse: {canal.mention}",
            ephemeral=True
        )
        logger.info(f"Ticket criado: {canal.name} por {user} ({user.id})")


class ViewPainelTickets(discord.ui.View):
    """View com o select de categorias — persistente."""

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectCategoriaTicket())


# ─────────────────────────────────────────────────────────────────
#  HELPERS INTERNOS
# ─────────────────────────────────────────────────────────────────

def _extrair_dono_id(topic: str) -> int | None:
    """Extrai o ID do dono a partir do tópico do canal."""
    match = re.search(r"DONO:(\d+)", topic)
    return int(match.group(1)) if match else None


def _encontrar_ticket_do_usuario(
    guild: discord.Guild,
    user_id: int
) -> discord.TextChannel | None:
    """Retorna o canal de ticket aberto do usuário, ou None."""
    for ch in guild.text_channels:
        if ch.topic and f"DONO:{user_id}" in ch.topic:
            return ch
    return None


# ─────────────────────────────────────────────────────────────────
#  COG PRINCIPAL
# ─────────────────────────────────────────────────────────────────

class CogTickets(commands.Cog, name="Tickets"):
    """Cog responsável por todo o sistema de tickets."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Registra views persistentes para sobreviver a restarts
        bot.add_view(ViewPainelTickets())
        bot.add_view(ViewAcoesTicket())

    # ── /ticket — envia o painel ───────────────────────────────────
    @app_commands.command(
        name="ticket",
        description="Envia o painel de tickets no canal atual."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def cmd_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="<a:CUPCHILL:1502354528802963538> Família Sant's — Sistema de Atendimeto",
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
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_image(url=CONFIG.BANNER_PAINEL)
        embed.set_footer(text="Família Sant's • Atendimento oficial")

        await interaction.channel.send(embed=embed, view=ViewPainelTickets())
        await interaction.response.send_message(
            "✅ Painel de tickets enviado com sucesso.",
            ephemeral=True
        )

    @cmd_ticket.error
    async def cmd_ticket_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        msg = "❌ Você precisa ser administrador para usar este comando."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    # ── /fechar — fecha o ticket atual (comando alternativo) ───────
    @app_commands.command(
        name="fechar",
        description="Fecha o ticket atual (disponível dentro de um ticket)."
    )
    async def cmd_fechar(self, interaction: discord.Interaction):
        canal = interaction.channel
        topic = canal.topic or ""

        if "DONO:" not in topic:
            await interaction.response.send_message(
                "❌ Este comando só pode ser usado dentro de um canal de ticket.",
                ephemeral=True
            )
            return

        dono_id = _extrair_dono_id(topic)
        e_dono  = dono_id == interaction.user.id
        e_staff = tem_permissao(interaction.user)

        if not (e_dono or e_staff):
            await interaction.response.send_message(
                "❌ Apenas o dono do ticket ou a equipe pode fechá-lo.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🔒 Confirmar Fechamento",
            description=(
                "Tem certeza que deseja encerrar este atendimento?\n\n"
                "• O transcript será salvo no canal de logs.\n"
                "• Este canal será **permanentemente deletado** após 5 segundos.\n\n"
                "Esta ação **não pode ser desfeita**."
            ),
            color=CONFIG.COR_VERMELHO
        )
        await interaction.response.send_message(
            embed=embed,
            view=ViewConfirmarFechamento(),
            ephemeral=True
        )

    # ── /ticket-info — info do ticket atual ────────────────────────
    @app_commands.command(
        name="ticket-info",
        description="Exibe informações do ticket atual."
    )
    async def cmd_info(self, interaction: discord.Interaction):
        canal = interaction.channel
        topic = canal.topic or ""

        if "DONO:" not in topic:
            await interaction.response.send_message(
                "❌ Este canal não é um ticket.",
                ephemeral=True
            )
            return

        if not tem_permissao(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas a equipe pode ver as informações do ticket.",
                ephemeral=True
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
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="📁 Canal",       value=canal.mention,  inline=True)
        embed.add_field(name="👤 Dono",        value=dono,           inline=True)
        embed.add_field(
            name="🕒 Aberto em",
            value=f"<t:{int(aberto.timestamp())}:f>",
            inline=True
        )
        embed.add_field(
            name="⏳ Duração",
            value=f"`{formatar_duracao(int((datetime.now(timezone.utc) - aberto).total_seconds()))}`",
            inline=True
        )
        embed.add_field(name="💬 Mensagens",   value=f"`{total_msgs}`", inline=True)
        embed.set_footer(text=f"Consultado por {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ─────────────────────────────────────────────────────────────────
#  SETUP
# ─────────────────────────────────────────────────────────────────

async def setup(bot: commands.Bot):
    await bot.add_cog(CogTickets(bot))
    logger.info("CogTickets carregado com sucesso.")