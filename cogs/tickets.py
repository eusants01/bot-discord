import discord
from discord.ext import commands
from discord import app_commands
from io import BytesIO

# ================================
# CONFIGURAÇÕES
# ================================
CATEGORIA_TICKETS_ID = 1495288098010169574
CARGO_STAFF_ID = 1487560221202321600
CANAL_LOG_ID = 1495272331558391818

# ================================
# 📄 FUNÇÃO DE TRANSCRIÇÃO
# ================================
async def gerar_transcricao(channel):
    mensagens = []

    async for msg in channel.history(limit=None, oldest_first=True):
        autor = f"{msg.author} ({msg.author.id})"
        data = msg.created_at.strftime("%d/%m/%Y %H:%M")
        conteudo = msg.content if msg.content else "[Sem texto]"

        if msg.attachments:
            anexos = "\n".join([a.url for a in msg.attachments])
            conteudo += f"\nAnexos:\n{anexos}"

        mensagens.append(f"[{data}] {autor}: {conteudo}")

    texto = "\n".join(mensagens)

    arquivo = BytesIO(texto.encode("utf-8"))
    arquivo.seek(0)

    return discord.File(arquivo, filename=f"{channel.name}.txt")


# =========================
# BOTÃO DE CONFIRMAR FECHAMENTO
# =========================
class BotaoDownload(discord.ui.View):
    def __init__(self, url):
        super().__init__(timeout=None)

        self.add_item(
            discord.ui.Button(
                label="📥 Baixar Ticket",
                url=url
            )
        )
class ConfirmarFechamento(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.red, emoji="✅")
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        log = interaction.guild.get_channel(CANAL_LOG_ID)

        if log:
            embed_log = discord.Embed(
                title="<a:D1_blue_check:1485361075930136847> Ticket Encerrado",
                description=(
                    f"👤 **Responsável:** {interaction.user.mention}\n"
                    f"📁 **Canal:** `{interaction.channel.name}`\n"
                    f"🕒 **Data:** <t:{int(interaction.created_at.timestamp())}:f>"
                ),
                color=discord.Color.red()
            )

            embed_log.set_image(url="https://i.imgur.com/ynK8fwA.png")
            embed_log.set_thumbnail(url=interaction.user.display_avatar.url)
            embed_log.set_footer(text="Família Sant's • Sistema de Tickets")

            arquivo = await gerar_transcricao(interaction.channel)

            msg = await log.send(file=arquivo)
            link = msg.attachments[0].url

            await log.send(
                embed=embed_log,
                view=BotaoDownload(link)
            )

        await interaction.response.send_message("🔒 Fechando ticket...", ephemeral=True)
        await interaction.channel.delete()

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.gray, emoji="❌")
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Operação cancelada.", ephemeral=True)


# =========================
# BOTÃO DE FECHAR TICKET
# =========================
class FecharTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.red, emoji="🔒")
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):

        # 🔒 se for admin, ignora tudo
        if interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Tem certeza que deseja fechar este ticket?",
                view=ConfirmarFechamento(),
                ephemeral=True
            )
            return

        # 🔒 cargos permitidos
        cargos_permitidos = [
            1487560221202321600,
            123456789012345678
        ]

        if not any(role.id in cargos_permitidos for role in interaction.user.roles):
            await interaction.response.send_message(
                "❌ Você não tem permissão para fechar tickets.",
                ephemeral=True
            )
            return

        # ✅ continua normal
        await interaction.response.send_message(
            "Tem certeza que deseja fechar este ticket?",
            view=ConfirmarFechamento(),
            ephemeral=True
        )


# =========================
# SELECT MENU DO TICKET
# =========================
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
    discord.SelectOption(
        label="Tira Duvidas",
        description="Tem duvidas sobre algo? Abre um ticket para que possamos te ajudar..",
        emoji="❓",
        value="duvidas"
    ),
    discord.SelectOption(
        label="Desejo fazer uma denuncia de alguém!",
        description="Abra um ticket e nos forneça as provas.",
        emoji="🚨",
        value="denuncia"
    ),
    discord.SelectOption(
        label="Compre a sua vaga na Família Sant's",
        description="Cada vaga custa R$80,00.",
        emoji="💰",
        value="comprar_vaga"
    ),
    discord.SelectOption(
        label="Solicite seu cargo Exclusivo",
        description="Abra um ticket para poder preencher o modelo",
        emoji="📝",
        value="cargo_exclusivo"
    )
]

        super().__init__(
            placeholder="Selecione uma opção...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        categoria = guild.get_channel(CATEGORIA_TICKETS_ID)
        cargo_staff = guild.get_role(CARGO_STAFF_ID)
        canal_log = guild.get_channel(CANAL_LOG_ID)

        if categoria is None:
            await interaction.response.send_message(
                "❌ A categoria de tickets não foi encontrada. Verifique o ID.",
                ephemeral=True
            )
            return

        for channel in guild.text_channels:
            if channel.topic and str(user.id) in channel.topic:
                await interaction.response.send_message(
                    f"❌ Você já possui um ticket aberto: {channel.mention}",
                    ephemeral=True
                )
                return

        tipo_ticket = self.values[0]

        tipos_ticket = {
    "duvidas": {
        "nome": "duvida",
        "titulo": "❓ Tirar dúvidas",
        "descricao": "Tem alguma dúvida sobre algo? Abra um ticket e nossa equipe irá te ajudar.",
        "cor": discord.Color.blue(),
        "imagem": "https://i.imgur.com/PSKO7LM.png",
        "thumbnail": "https://i.imgur.com/3m531pJ.png"
    },
    "denuncia": {
        "nome": "denuncia",
        "titulo": "🚨 Fazer uma denúncia",
        "descricao": "Abra um ticket e nos envie as provas necessárias.",
        "cor": discord.Color.dark_red(),
        "imagem": "https://i.imgur.com/D8fWYgP.png",
        "thumbnail": "https://i.imgur.com/jUvYKor.png"
    },
    "cargo_exclusivo": {
        "nome": "cargo-exclusivo",
        "titulo": "Solicitação de Cargo Exclusivo",
        "descricao": "Abra um ticket para poder preencher o modelo",
        "cor": discord.Color.dark_blue(),
        "imagem": "https://i.imgur.com/vCwH82v.png",
        "thumbnail": "https://i.imgur.com/14EGYq9.png"
    },
    "comprar_vaga": {
        "nome": "comprar-vaga",
        "titulo": "💰 Comprar uma vaga",
        "descricao": "Cada vaga custa R$80,00. Abra o ticket para realizar a compra.",
        "cor": discord.Color.green(),
        "imagem": "https://i.imgur.com/8DAE2eE.png",
        "thumbnail": "https://i.imgur.com/9ZN2LJl.png"
    }
}

        if tipo_ticket not in tipos_ticket:
            await interaction.response.send_message(
                "❌ Tipo de ticket inválido.",
                ephemeral=True
            )
            return

        info = tipos_ticket[tipo_ticket]

        nome_canal = f"{info['nome']}-{user.name}".lower().replace(" ", "-")

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
                read_message_history=True,
                manage_channels=True,
                manage_messages=True
            ),
        }

        if cargo_staff:
            overwrites[cargo_staff] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )

        canal = await guild.create_text_channel(
            name=nome_canal,
            category=categoria,
            overwrites=overwrites,
            topic=f"{user.id} | Ticket de {user} | Tipo: {tipo_ticket}"
        )

        embed_ticket = discord.Embed(
            
            description=(
                f"Olá {user.mention}, tudo bem? Agradecemos pelo seu ticket. Aguarde um momento enquanto algum de nosso atendentes venha te ajudar.\n\n"
                f"**Categoria:** {info['titulo']}\n"
                f"**Detalhes:** {info['descricao']}\n\n"
                f"<@&1487560221202321600>."
            ),
            color=info["cor"]
        )

        embed_ticket.set_thumbnail(url=info["thumbnail"])
        embed_ticket.set_image(url=info["imagem"])
        embed_ticket.set_footer(text="Use o botão abaixo para fechar o ticket quando finalizar.")

        await canal.send(
            content=user.mention,
            embed=embed_ticket,
            view=FecharTicketView()
        )

        await interaction.response.send_message(
            f"✅ Seu ticket foi criado: {canal.mention}",
            ephemeral=True
        )

       

# =========================
# VIEW DO PAINEL
# =========================
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


# =========================
# COG
# =========================
class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket", description="Enviar painel de ticket")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Central de Atendimentos da Família Sant's",
            description="Selecione uma das opções abaixo para abrir um ticket.\n\n",
            color=discord.Color.from_rgb(30, 35, 60)
        )

        embed.set_image(url="https://i.imgur.com/BItqGWY.png")
        embed.set_footer(text="Painel oficial de atendimento.")

        await interaction.channel.send(
            embed=embed,
            view=TicketView()
        )

        await interaction.response.send_message(
            "✅ Painel enviado com sucesso.",
            ephemeral=True
        )

    @ticket.error
    async def ticket_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message(
            "❌ Você não tem permissão para usar este comando.",
            ephemeral=True
        )


