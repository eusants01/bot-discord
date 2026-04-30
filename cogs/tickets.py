import discord
from discord.ext import commands
from discord import app_commands
from io import BytesIO
import asyncio

from cogs.conquistas import liberar_conquista

# ================================
# CONFIGURAÇÕES
# ================================
CATEGORIA_TICKETS_ID = 1495288098010169574
CARGO_STAFF_ID = 1487560221202321600
CANAL_LOG_ID = 1495272331558391818

# ================================
# 📄 TRANSCRIÇÃO
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
# DOWNLOAD
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

# =========================
# CONFIRMAR FECHAMENTO
# =========================
class ConfirmarFechamento(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.red, emoji="✅")
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        log = interaction.guild.get_channel(CANAL_LOG_ID)

        if log:
            embed_log = discord.Embed(
                title="📁 Ticket Encerrado",
                description=(
                    f"👤 **Responsável:** {interaction.user.mention}\n"
                    f"📁 **Canal:** `{interaction.channel.name}`\n"
                ),
                color=discord.Color.dark_blue()
            )

            arquivo = await gerar_transcricao(interaction.channel)
            msg = await log.send(file=arquivo)

            link = msg.attachments[0].url

            await msg.edit(
                embed=embed_log,
                view=BotaoDownload(link)
            )

        await interaction.response.send_message(
            "🔒 Encerrando domínio...",
            ephemeral=True
        )

        await asyncio.sleep(2)
        await interaction.channel.delete()

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.gray, emoji="🛑")
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Cancelado.",
            ephemeral=True
        )

# =========================
# BOTÃO FECHAR
# =========================
class FecharTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.red, emoji="🔒")
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)

        if interaction.user.guild_permissions.administrator:
            await interaction.followup.send(
                "Confirmar fechamento?",
                view=ConfirmarFechamento(),
                ephemeral=True
            )
            return

        cargos_permitidos = [
            1487560221202321600,
            1480381506064093225,
        ]

        if not any(role.id in cargos_permitidos for role in interaction.user.roles):
            await interaction.followup.send(
                "❌ Sem permissão.",
                ephemeral=True
            )
            return

        await interaction.followup.send(
            "Confirmar fechamento?",
            view=ConfirmarFechamento(),
            ephemeral=True
        )

# =========================
# SELECT
# =========================
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Dúvidas", value="duvida"),
            discord.SelectOption(label="Denúncia", value="denuncia"),
            discord.SelectOption(label="Compra", value="comprar_vaga"),
            discord.SelectOption(label="Cargo", value="cargo_exclusivo")
        ]

        super().__init__(
            placeholder="Escolha...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        user = interaction.user

        categoria = guild.get_channel(CATEGORIA_TICKETS_ID)

        if categoria is None:
            return await interaction.followup.send("❌ Categoria não encontrada.", ephemeral=True)

        for ch in guild.text_channels:
            if ch.topic and str(user.id) in ch.topic:
                return await interaction.followup.send(f"Você já tem: {ch.mention}", ephemeral=True)

        nome = f"ticket-{user.name}".lower()

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True),
            guild.me: discord.PermissionOverwrite(view_channel=True),
        }

        canal = await guild.create_text_channel(
            name=nome,
            category=categoria,
            overwrites=overwrites,
            topic=str(user.id)
        )

        embed = discord.Embed(
            description=f"{user.mention} seu ticket foi criado.",
            color=discord.Color.purple()
        )

        await canal.send(
            content=user.mention,
            embed=embed,
            view=FecharTicketView()
        )

        # 🔥 CONQUISTA AUTOMÁTICA
        await liberar_conquista(
            interaction.client,
            user,
            "contrato_aberto",
            canal
        )

        await interaction.followup.send(
            f"Ticket criado: {canal.mention}",
            ephemeral=True
        )

# =========================
# VIEW
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

    @app_commands.command(name="ticket", description="Enviar painel")
    async def ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 Tickets",
            description="Abra um ticket abaixo",
            color=discord.Color.purple()
        )

        await interaction.channel.send(
            embed=embed,
            view=TicketView()
        )

        await interaction.response.send_message(
            "Painel enviado.",
            ephemeral=True
        )

# =========================
# SETUP
# =========================
async def setup(bot):
    await bot.add_cog(TicketCog(bot))