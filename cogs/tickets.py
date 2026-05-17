import discord
from discord.ext import commands
from discord import app_commands
from io import BytesIO
import asyncio
import re
from datetime import datetime, timezone


# =========================
# CONFIGURAÇÕES
# =========================

CATEGORIA_TICKETS_ID = 1495288098010169574
CANAL_LOG_ID = 1495272331558391818

CARGOS_ATENDIMENTO_IDS = [
    1487560221202321600,
    1501356975491907664,
    1500545846427652166,
    1480381506064093225,
]

# Tema Cuphead
COR_CUPHEAD_VERMELHO = discord.Color.from_rgb(160, 45, 35)
COR_CUPHEAD_AZUL = discord.Color.from_rgb(35, 95, 140)
COR_CUPHEAD_DOURADO = discord.Color.from_rgb(205, 155, 70)
COR_CUPHEAD_VERDE = discord.Color.from_rgb(70, 125, 65)
COR_CUPHEAD_ESCURO = discord.Color.from_rgb(35, 30, 25)

# Troque pelos seus banners Cuphead
BANNER_PAINEL_TICKETS = "https://i.imgur.com/mf2J8At.png"
BANNER_TICKET_FECHADO = "https://i.imgur.com/xzTNoyc.png"

IMAGENS_TICKETS = {
    "duvida": "https://i.imgur.com/4GQjoSb.png",
    "denuncia": "https://i.imgur.com/Bl79W4Y.png",
    "cargo_exclusivo": "https://i.imgur.com/UP1k58c.png",
    "comprar_vaga": "https://i.imgur.com/pB3mL7E.png",
}

THUMBNAILS_TICKETS = {
    "duvida": "https://i.imgur.com/AYs4N07.png",
    "denuncia": "https://i.imgur.com/zkIgP83.png",
    "cargo_exclusivo": "https://i.imgur.com/4ZnTLm3.png",
    "comprar_vaga": "https://i.imgur.com/yw1FDpN.png",
}


# =========================
# FUNÇÕES AUXILIARES
# =========================

def limpar_nome(texto: str) -> str:
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9-]", "-", texto)
    texto = re.sub(r"-+", "-", texto)
    return texto.strip("-")


def tem_permissao_ticket(member: discord.Member) -> bool:
    return member.guild_permissions.administrator or any(
        role.id in CARGOS_ATENDIMENTO_IDS for role in member.roles
    )


def formatar_duracao(segundos: int) -> str:
    minutos, segundos = divmod(segundos, 60)
    horas, minutos = divmod(minutos, 60)
    dias, horas = divmod(horas, 24)

    partes = []

    if dias:
        partes.append(f"{dias}d")
    if horas:
        partes.append(f"{horas}h")
    if minutos:
        partes.append(f"{minutos}min")
    if segundos and not partes:
        partes.append(f"{segundos}s")

    return " ".join(partes) if partes else "0s"


async def gerar_transcricao(channel: discord.TextChannel):
    mensagens = []
    total_mensagens = 0

    async for msg in channel.history(limit=None, oldest_first=True):
        total_mensagens += 1

        autor = f"{msg.author} ({msg.author.id})"
        data = msg.created_at.strftime("%d/%m/%Y %H:%M")
        conteudo = msg.content if msg.content else "[Sem texto]"

        if msg.attachments:
            anexos = "\n".join([a.url for a in msg.attachments])
            conteudo += f"\nAnexos:\n{anexos}"

        mensagens.append(f"[{data}] {autor}: {conteudo}")

    if not mensagens:
        mensagens.append("Nenhuma mensagem registrada neste ticket.")

    arquivo = BytesIO("\n".join(mensagens).encode("utf-8"))
    arquivo.seek(0)

    nome_arquivo = f"transcript-{limpar_nome(channel.name)}.txt"

    return discord.File(arquivo, filename=nome_arquivo), total_mensagens


# =========================
# BOTÃO DE DOWNLOAD
# =========================

class BotaoDownload(discord.ui.View):
    def __init__(self, url: str):
        super().__init__(timeout=None)

        self.add_item(
            discord.ui.Button(
                label="📥 Baixar Transcript",
                url=url
            )
        )

        self.add_item(
            discord.ui.Button(
                label="🎬 Ticket Encerrado",
                style=discord.ButtonStyle.gray,
                disabled=True
            )
        )


# =========================
# CONFIRMAR FECHAMENTO
# =========================

class ConfirmarFechamento(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(
        label="Confirmar Fechamento",
        style=discord.ButtonStyle.red,
        emoji="🔒"
    )
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not tem_permissao_ticket(interaction.user):
            await interaction.response.send_message(
                "❌ Você não possui permissão para fechar este ticket.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🎬 O show está chegando ao fim... fechando ticket em instantes.",
            ephemeral=True
        )

        log = interaction.guild.get_channel(CANAL_LOG_ID)

        criado_em = interaction.channel.created_at
        fechado_em = datetime.now(timezone.utc)
        duracao = formatar_duracao(int((fechado_em - criado_em).total_seconds()))

        arquivo, total_mensagens = await gerar_transcricao(interaction.channel)

        if log:
            msg = await log.send(file=arquivo)
            link = msg.attachments[0].url

            embed_log = discord.Embed(
                title="🎬 Ticket Encerrado — Família Sant's",
                description=(
                    "O atendimento foi finalizado com sucesso.\n"
                    "O registro do ticket foi salvo nos arquivos do nosso velho estúdio."
                ),
                color=COR_CUPHEAD_DOURADO
            )

            embed_log.add_field(
                name="👤 Fechado por",
                value=interaction.user.mention,
                inline=True
            )

            embed_log.add_field(
                name="📁 Canal",
                value=f"`{interaction.channel.name}`",
                inline=True
            )

            embed_log.add_field(
                name="🕒 Encerrado em",
                value=f"<t:{int(interaction.created_at.timestamp())}:f>",
                inline=False
            )

            embed_log.add_field(
                name="⏳ Duração",
                value=f"`{duracao}`",
                inline=True
            )

            embed_log.add_field(
                name="💬 Mensagens",
                value=f"`{total_mensagens}`",
                inline=True
            )

            embed_log.add_field(
                name="📜 Transcript",
                value="Use o botão abaixo para baixar o registro completo.",
                inline=False
            )

            embed_log.set_thumbnail(url=interaction.user.display_avatar.url)
            embed_log.set_image(url=BANNER_TICKET_FECHADO)
            embed_log.set_footer(text="Família Sant's • Sistema de Tickets Cuphead")

            await msg.edit(embed=embed_log, view=BotaoDownload(link))

        aviso = discord.Embed(
            title="🎞️ Fim do Episódio",
            description=(
                "O ticket foi encerrado.\n"
                "Este canal será apagado em **5 segundos**."
            ),
            color=COR_CUPHEAD_ESCURO
        )

        await interaction.channel.send(embed=aviso)

        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(
        label="Cancelar",
        style=discord.ButtonStyle.gray,
        emoji="🛑"
    )
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🛑 Fechamento cancelado. O ticket continua aberto.",
            ephemeral=True
        )


# =========================
# BOTÕES DO TICKET
# =========================

class TicketActionsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Assumir Atendimento",
        style=discord.ButtonStyle.green,
        emoji="🎩",
        custom_id="cuphead_assumir_ticket"
    )
    async def assumir(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not tem_permissao_ticket(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas a equipe pode assumir este atendimento.",
                ephemeral=True
            )
            return

        mensagem = interaction.message

        if not mensagem.embeds:
            await interaction.response.send_message(
                "❌ Não consegui encontrar o painel deste ticket.",
                ephemeral=True
            )
            return

        embed_antigo = mensagem.embeds[0]

        novo_embed = discord.Embed(
            title=embed_antigo.title,
            description=(
                embed_antigo.description.replace(
                    "⏳ **Status:** `Aguardando atendimento`",
                    f"🟢 **Status:** `Em atendimento por {interaction.user.display_name}`"
                )
            ),
            color=COR_CUPHEAD_VERDE
        )

        if embed_antigo.thumbnail:
            novo_embed.set_thumbnail(url=embed_antigo.thumbnail.url)

        if embed_antigo.image:
            novo_embed.set_image(url=embed_antigo.image.url)

        novo_embed.set_footer(
            text=f"Atendimento assumido por {interaction.user.display_name}"
        )

        button.disabled = True
        button.label = "Atendimento Assumido"

        await mensagem.edit(embed=novo_embed, view=self)

        await interaction.response.send_message(
            f"🎩 {interaction.user.mention} assumiu este atendimento.",
            ephemeral=False
        )

    @discord.ui.button(
        label="Painel Restrito",
        style=discord.ButtonStyle.blurple,
        emoji="⚙️",
        custom_id="cuphead_painel_restrito"
    )
    async def painel_admin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not tem_permissao_ticket(interaction.user):
            await interaction.response.send_message(
                "❌ Você não possui acesso ao painel restrito.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="⚙️ Painel Restrito do Estúdio",
            description=(
                "Informações administrativas deste atendimento.\n\n"
                f"📁 **Canal:** {interaction.channel.mention}\n"
                f"👤 **Acessado por:** {interaction.user.mention}\n"
                f"🕒 **Criado em:** <t:{int(interaction.channel.created_at.timestamp())}:f>\n\n"
                "Use os botões principais para assumir, chamar a equipe ou fechar o ticket."
            ),
            color=COR_CUPHEAD_AZUL
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    @discord.ui.button(
        label="Fechar Ticket",
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="cuphead_fechar_ticket"
    )
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not tem_permissao_ticket(interaction.user):
            await interaction.response.send_message(
                "❌ Você não possui permissão para fechar este ticket.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🔒 Confirmar Fechamento",
            description=(
                "Tem certeza que deseja fechar este ticket?\n\n"
                "Após confirmar, o transcript será enviado ao canal de logs "
                "e este canal será apagado."
            ),
            color=COR_CUPHEAD_VERMELHO
        )

        await interaction.response.send_message(
            embed=embed,
            view=ConfirmarFechamento(),
            ephemeral=True
        )

    @discord.ui.button(
        label="Chamar Equipe",
        style=discord.ButtonStyle.primary,
        emoji="📢",
        custom_id="cuphead_chamar_equipe"
    )
    async def notificar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not tem_permissao_ticket(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas a equipe pode chamar atendentes.",
                ephemeral=True
            )
            return

        mencoes_staff = " ".join(
            f"<@&{cargo_id}>"
            for cargo_id in CARGOS_ATENDIMENTO_IDS
        )

        embed = discord.Embed(
            title="📢 Equipe Chamada",
            description=(
                f"{mencoes_staff}\n\n"
                "Este ticket precisa de atenção. O palco está aberto para o atendimento!"
            ),
            color=COR_CUPHEAD_DOURADO
        )

        await interaction.response.send_message(
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True)
        )


# =========================
# MENU DE SELEÇÃO
# =========================

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Dúvidas",
                description="Tire suas dúvidas com a equipe.",
                emoji="❓",
                value="duvida"
            ),
            discord.SelectOption(
                label="Denúncias",
                description="Reporte algo errado com provas.",
                emoji="🚨",
                value="denuncia"
            ),
            discord.SelectOption(
                label="Comprar Vaga",
                description="Solicite entrada na Família Sant's.",
                emoji="💰",
                value="comprar_vaga"
            ),
            discord.SelectOption(
                label="Cargo Exclusivo",
                description="Solicite seu cargo exclusivo.",
                emoji="🎖️",
                value="cargo_exclusivo"
            )
        ]

        super().__init__(
            placeholder="Selecione uma categoria do estúdio...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_select_cuphead_sants"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        user = interaction.user
        categoria = guild.get_channel(CATEGORIA_TICKETS_ID)

        if categoria is None:
            await interaction.followup.send(
                "❌ Categoria de tickets não encontrada.",
                ephemeral=True
            )
            return

        for channel in guild.text_channels:
            if channel.topic and f"DONO:{user.id}" in channel.topic:
                await interaction.followup.send(
                    f"❌ Você já possui um ticket ativo: {channel.mention}",
                    ephemeral=True
                )
                return

        tipo_ticket = self.values[0]

        tipos_ticket = {
            "duvida": {
                "nome": "duvida",
                "titulo": "❓ Dúvidas — Balcão do Estúdio",
                "descricao": "Conte sua dúvida e aguarde a equipe.",
                "cor": COR_CUPHEAD_AZUL,
                "imagem": IMAGENS_TICKETS["duvida"],
                "thumbnail": THUMBNAILS_TICKETS["duvida"],
                "nivel": "🔵 Suporte Geral"
            },
            "denuncia": {
                "nome": "denuncia",
                "titulo": "🚨 Denúncia — Alerta no Estúdio",
                "descricao": "Reporte situações incorretas com provas.",
                "cor": COR_CUPHEAD_VERMELHO,
                "imagem": IMAGENS_TICKETS["denuncia"],
                "thumbnail": THUMBNAILS_TICKETS["denuncia"],
                "nivel": "🔴 Prioridade Alta"
            },
            "cargo_exclusivo": {
                "nome": "cargo-exclusivo",
                "titulo": "🎖️ Cargo Exclusivo — Camarim Especial",
                "descricao": "Solicite seu cargo exclusivo preenchendo o modelo.",
                "cor": COR_CUPHEAD_DOURADO,
                "imagem": IMAGENS_TICKETS["cargo_exclusivo"],
                "thumbnail": THUMBNAILS_TICKETS["cargo_exclusivo"],
                "nivel": "🟡 Solicitação Especial"
            },
            "comprar_vaga": {
                "nome": "comprar-vaga",
                "titulo": "💰 Comprar Vaga — Entrada na Família",
                "descricao": "Solicite informações para entrar na Família Sant's.",
                "cor": COR_CUPHEAD_VERDE,
                "imagem": IMAGENS_TICKETS["comprar_vaga"],
                "thumbnail": THUMBNAILS_TICKETS["comprar_vaga"],
                "nivel": "🟢 Atendimento Comercial"
            }
        }

        info = tipos_ticket[tipo_ticket]
        nome_canal = limpar_nome(f"{info['nome']}-{user.name}")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                read_message_history=True
            ),
        }

        for cargo_id in CARGOS_ATENDIMENTO_IDS:
            cargo = guild.get_role(cargo_id)

            if cargo:
                overwrites[cargo] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                )

        canal = await guild.create_text_channel(
            name=nome_canal,
            category=categoria,
            overwrites=overwrites,
            topic=f"DONO:{user.id} | Ticket de {user} | Tipo: {tipo_ticket}"
        )

        mencoes_staff = " ".join(
            f"<@&{cargo_id}>"
            for cargo_id in CARGOS_ATENDIMENTO_IDS
        )

        embed_ticket = discord.Embed(
            title=info["titulo"],
            description=(
                f"🎬 Olá {user.mention}, bem-vindo ao atendimento da **Família Sant's**!\n\n"
                "Seu ticket foi aberto com sucesso. Agora é só explicar sua solicitação "
                "com calma enquanto nossa equipe prepara o espetáculo.\n\n"
                "📜 **Orientações:**\n"
                "• Explique claramente o motivo do ticket.\n"
                "• Envie prints, provas ou informações se necessário.\n"
                "• Evite spam e menções desnecessárias.\n"
                "• Aguarde a equipe responsável responder.\n\n"
                f"🎟️ **Categoria:** {info['titulo']}\n"
                f"⭐ **Tipo:** `{info['nivel']}`\n"
                "⏳ **Status:** `Aguardando atendimento`\n"
                "🎞️ **Estúdio:** `Aberto`\n\n"
                f"{mencoes_staff}"
            ),
            color=info["cor"]
        )

        embed_ticket.set_thumbnail(url=info["thumbnail"])
        embed_ticket.set_image(url=info["imagem"])
        embed_ticket.set_footer(
            text="Família Sant's • Sistema de Tickets Cuphead"
        )

        await canal.send(
            content=user.mention,
            embed=embed_ticket,
            view=TicketActionsView()
        )

        await interaction.followup.send(
            f"✅ Ticket criado com sucesso: {canal.mention}",
            ephemeral=True
        )


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


# =========================
# COG PRINCIPAL
# =========================

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(TicketView())
        self.bot.add_view(TicketActionsView())

    @app_commands.command(
        name="ticket",
        description="Enviar painel de tickets"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎬 Família Sant's — Sistema de Tickets",
            description=(
                "Bem-vindo ao balcão oficial de atendimento da **Família Sant's**.\n\n"
                "Escolha uma categoria abaixo e abra seu ticket.\n"
                "Nossa equipe irá te atender assim que possível.\n\n"
                "❓ **Dúvidas** — tire suas dúvidas gerais.\n"
                "🚨 **Denúncias** — reporte algo errado com provas.\n"
                "💰 **Comprar Vaga** — solicite entrada na Família.\n"
                "🎖️ **Cargo Exclusivo** — solicite seu cargo especial.\n\n"
                "🎞️ Selecione uma opção no menu abaixo para começar."
            ),
            color=COR_CUPHEAD_DOURADO
        )

        embed.set_image(url=BANNER_PAINEL_TICKETS)
        embed.set_footer(text="Família Sant's • Atendimento oficial")

        await interaction.channel.send(
            embed=embed,
            view=TicketView()
        )

        await interaction.response.send_message(
            "✅ Painel de tickets enviado com sucesso.",
            ephemeral=True
        )

    @ticket.error
    async def ticket_error(self, interaction: discord.Interaction, error):
        mensagem = "❌ Você não tem permissão para usar esse comando."

        if interaction.response.is_done():
            await interaction.followup.send(mensagem, ephemeral=True)
        else:
            await interaction.response.send_message(mensagem, ephemeral=True)


async def setup(bot):
    await bot.add_cog(TicketCog(bot))