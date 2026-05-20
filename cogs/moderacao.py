import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
from datetime import datetime

# ==================================================
# 🎰 CONFIGURAÇÕES • CUPHEAD MODERATION
# ==================================================

GUILD_ID = 1480334256763961465
CANAL_LOGS_ID = 1501594489939300524

COR_CUPHEAD = 0xC48A3A
COR_VERDE = 0x2ECC71
COR_VERMELHO = 0xC0392B
COR_ESCURO = 0x2B1B12

# ==================================================
# 🖼️ BANNERS
# ==================================================

BANNER_WARN = "https://i.imgur.com/7VCFn76.png"
BANNER_BAN = "https://i.imgur.com/UqFKdTL.png"
BANNER_UNBAN = "https://i.imgur.com/IFDHuR3.png"
BANNER_CLEAR = "https://i.imgur.com/X98wym6.png"

# ==================================================
# 🗄️ BANCO DE DADOS
# ==================================================

conn = sqlite3.connect("moderacao.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS warns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    staff_id INTEGER NOT NULL,
    motivo TEXT NOT NULL,
    data TEXT NOT NULL
)
""")

conn.commit()


def data_atual():
    return datetime.now().strftime("%d/%m/%Y às %H:%M")


def limitar_texto(texto: str, limite: int = 900):
    if len(texto) <= limite:
        return texto

    return texto[:limite - 3] + "..."


def salvar_warn(guild_id, user_id, staff_id, motivo):
    data = data_atual()

    cursor.execute("""
    INSERT INTO warns (guild_id, user_id, staff_id, motivo, data)
    VALUES (?, ?, ?, ?, ?)
    """, (guild_id, user_id, staff_id, motivo, data))

    conn.commit()


def buscar_warns(guild_id, user_id):
    cursor.execute("""
    SELECT id, staff_id, motivo, data
    FROM warns
    WHERE guild_id = ? AND user_id = ?
    ORDER BY id DESC
    """, (guild_id, user_id))

    return cursor.fetchall()


def remover_warn_db(warn_id):
    cursor.execute("""
    DELETE FROM warns
    WHERE id = ?
    """, (warn_id,))

    conn.commit()
    return cursor.rowcount > 0


def limpar_warns(guild_id, user_id):
    cursor.execute("""
    DELETE FROM warns
    WHERE guild_id = ? AND user_id = ?
    """, (guild_id, user_id))

    conn.commit()
    return cursor.rowcount


# ==================================================
# 🎲 COG DE MODERAÇÃO
# ==================================================

class Moderacao(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ==================================================
    # 📜 LOGS
    # ==================================================

    async def enviar_log(self, guild: discord.Guild, embed: discord.Embed):
        canal = guild.get_channel(CANAL_LOGS_ID)

        if canal:
            try:
                await canal.send(embed=embed)
            except discord.HTTPException:
                pass

    def criar_embed_base(self, titulo: str, descricao: str, cor: int):
        embed = discord.Embed(
            title=titulo,
            description=descricao,
            color=cor,
            timestamp=datetime.now()
        )

        embed.set_footer(
            text="Família Sant's • Cuphead Moderation"
        )

        return embed

    # ==================================================
    # ⚠️ WARN
    # ==================================================

    @app_commands.command(
        name="warn",
        description="Aplica um aviso em um membro."
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        motivo: str
    ):
        if membro.bot:
            return await interaction.response.send_message(
                "❌ Você não pode aplicar warn em bots.",
                ephemeral=True
            )

        if membro == interaction.user:
            return await interaction.response.send_message(
                "❌ Você não pode aplicar warn em si mesmo.",
                ephemeral=True
            )

        if membro.top_role >= interaction.user.top_role and interaction.guild.owner_id != interaction.user.id:
            return await interaction.response.send_message(
                "❌ Esse membro possui cargo igual ou superior ao seu.",
                ephemeral=True
            )

        salvar_warn(
            interaction.guild.id,
            membro.id,
            interaction.user.id,
            motivo
        )

        warns = buscar_warns(
            interaction.guild.id,
            membro.id
        )

        total_warns = len(warns)

        embed = self.criar_embed_base(
            "⚠️ WARN APLICADO • CUPHEAD CASINO",
            (
                "Um aviso foi registrado pela equipe.\n"
                "A infração foi enviada para os registros oficiais do servidor."
            ),
            COR_CUPHEAD
        )

        embed.add_field(
            name="👤 Membro",
            value=f"{membro.mention}\n`{membro.id}`",
            inline=True
        )

        embed.add_field(
            name="🛡️ Staff",
            value=interaction.user.mention,
            inline=True
        )

        embed.add_field(
            name="📌 Total de Warns",
            value=f"`{total_warns}`",
            inline=True
        )

        embed.add_field(
            name="📄 Motivo",
            value=limitar_texto(motivo),
            inline=False
        )

        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_image(url=BANNER_WARN)

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

        await self.enviar_log(interaction.guild, embed)

        try:
            dm = discord.Embed(
                title="⚠️ Você recebeu um warn",
                description=(
                    f"Você recebeu um aviso em **{interaction.guild.name}**.\n\n"
                    f"📄 **Motivo:** {motivo}\n"
                    f"📌 **Total de warns:** `{total_warns}`"
                ),
                color=COR_CUPHEAD
            )

            dm.set_footer(text="Família Sant's • Cuphead Moderation")
            await membro.send(embed=dm)

        except discord.HTTPException:
            pass

    # ==================================================
    # 📋 VER WARNS
    # ==================================================

    @app_commands.command(
        name="warnings",
        description="Mostra os warns de um membro."
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warnings(
        self,
        interaction: discord.Interaction,
        membro: discord.Member
    ):
        warns = buscar_warns(
            interaction.guild.id,
            membro.id
        )

        if not warns:
            embed = self.criar_embed_base(
                "✅ FICHA LIMPA",
                f"{membro.mention} não possui warns registrados.",
                COR_VERDE
            )

            embed.set_thumbnail(url=membro.display_avatar.url)

            return await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

        embed = self.criar_embed_base(
            f"📋 HISTÓRICO DE WARNS • {membro.display_name}",
            (
                "Abaixo estão os últimos registros disciplinares do membro.\n"
                "Exibindo no máximo os **10 warns mais recentes**."
            ),
            COR_CUPHEAD
        )

        for warn_id, staff_id, motivo, data in warns[:10]:

            staff = interaction.guild.get_member(staff_id)
            staff_texto = staff.mention if staff else f"`{staff_id}`"

            embed.add_field(
                name=f"⚠️ Warn #{warn_id}",
                value=(
                    f"🛡️ **Staff:** {staff_texto}\n"
                    f"📅 **Data:** `{data}`\n"
                    f"📄 **Motivo:** {limitar_texto(motivo, 300)}"
                ),
                inline=False
            )

        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_footer(
            text=f"Família Sant's • Total de warns: {len(warns)}"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    # ==================================================
    # 🧹 REMOVER WARN
    # ==================================================

    @app_commands.command(
        name="removewarn",
        description="Remove um warn pelo ID."
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def removewarn(
        self,
        interaction: discord.Interaction,
        warn_id: int
    ):
        removido = remover_warn_db(warn_id)

        if not removido:
            return await interaction.response.send_message(
                "❌ Nenhum warn foi encontrado com esse ID.",
                ephemeral=True
            )

        embed = self.criar_embed_base(
            "🧹 WARN REMOVIDO",
            "Um registro disciplinar foi removido pela equipe.",
            COR_VERDE
        )

        embed.add_field(
            name="🆔 Warn ID",
            value=f"`{warn_id}`",
            inline=True
        )

        embed.add_field(
            name="🛡️ Staff",
            value=interaction.user.mention,
            inline=True
        )

        embed.set_image(url=BANNER_CLEAR)

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

        await self.enviar_log(interaction.guild, embed)

    # ==================================================
    # 🧽 LIMPAR WARNS
    # ==================================================

    @app_commands.command(
        name="clearwarns",
        description="Remove todos os warns de um membro."
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clearwarns(
        self,
        interaction: discord.Interaction,
        membro: discord.Member
    ):
        quantidade = limpar_warns(
            interaction.guild.id,
            membro.id
        )

        embed = self.criar_embed_base(
            "🧽 WARNS LIMPOS",
            "Todos os registros disciplinares do membro foram removidos.",
            COR_VERDE
        )

        embed.add_field(
            name="👤 Membro",
            value=f"{membro.mention}\n`{membro.id}`",
            inline=True
        )

        embed.add_field(
            name="🛡️ Staff",
            value=interaction.user.mention,
            inline=True
        )

        embed.add_field(
            name="📌 Warns Removidos",
            value=f"`{quantidade}`",
            inline=True
        )

        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_image(url=BANNER_CLEAR)

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

        await self.enviar_log(interaction.guild, embed)

    # ==================================================
    # 🔨 BAN
    # ==================================================

    @app_commands.command(
        name="ban",
        description="Bane um membro do servidor."
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        motivo: str
    ):
        if membro == interaction.user:
            return await interaction.response.send_message(
                "❌ Você não pode banir a si mesmo.",
                ephemeral=True
            )

        if membro == interaction.guild.owner:
            return await interaction.response.send_message(
                "❌ Você não pode banir o dono do servidor.",
                ephemeral=True
            )

        if membro.top_role >= interaction.user.top_role and interaction.guild.owner_id != interaction.user.id:
            return await interaction.response.send_message(
                "❌ Esse membro possui cargo igual ou superior ao seu.",
                ephemeral=True
            )

        if membro.top_role >= interaction.guild.me.top_role:
            return await interaction.response.send_message(
                "❌ Eu não consigo banir esse membro porque o cargo dele está acima ou igual ao meu.",
                ephemeral=True
            )

        try:
            dm = discord.Embed(
                title="🔨 Você foi banido",
                description=(
                    f"Você foi banido de **{interaction.guild.name}**.\n\n"
                    f"📄 **Motivo:** {motivo}"
                ),
                color=COR_VERMELHO
            )

            dm.set_footer(text="Família Sant's • Cuphead Moderation")
            await membro.send(embed=dm)

        except discord.HTTPException:
            pass

        await membro.ban(
            reason=f"{motivo} | Staff: {interaction.user}"
        )

        embed = self.criar_embed_base(
            "🔨 MEMBRO BANIDO • CUPHEAD CASINO",
            "Uma punição máxima foi executada pela equipe.",
            COR_VERMELHO
        )

        embed.add_field(
            name="👤 Membro",
            value=f"{membro.mention}\n`{membro.id}`",
            inline=True
        )

        embed.add_field(
            name="🛡️ Staff",
            value=interaction.user.mention,
            inline=True
        )

        embed.add_field(
            name="📄 Motivo",
            value=limitar_texto(motivo),
            inline=False
        )

        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_image(url=BANNER_BAN)

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

        await self.enviar_log(interaction.guild, embed)

    # ==================================================
    # 🕊️ UNBAN
    # ==================================================

    @app_commands.command(
        name="unban",
        description="Remove o banimento de um usuário."
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(
        self,
        interaction: discord.Interaction,
        user_id: str,
        motivo: str = "Não informado"
    ):
        try:
            user_id_int = int(user_id)
        except ValueError:
            return await interaction.response.send_message(
                "❌ Informe um ID válido de usuário.",
                ephemeral=True
            )

        try:
            user = await self.bot.fetch_user(user_id_int)

            await interaction.guild.unban(
                user,
                reason=f"{motivo} | Staff: {interaction.user}"
            )

            embed = self.criar_embed_base(
                "🕊️ USUÁRIO DESBANIDO",
                "O acesso do usuário ao servidor foi restaurado.",
                COR_VERDE
            )

            embed.add_field(
                name="👤 Usuário",
                value=f"{user.mention}\n`{user.id}`",
                inline=True
            )

            embed.add_field(
                name="🛡️ Staff",
                value=interaction.user.mention,
                inline=True
            )

            embed.add_field(
                name="📄 Motivo",
                value=limitar_texto(motivo),
                inline=False
            )

            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_image(url=BANNER_UNBAN)

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            await self.enviar_log(interaction.guild, embed)

        except discord.NotFound:
            await interaction.response.send_message(
                "❌ Esse usuário não está banido ou não foi encontrado.",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Eu não tenho permissão para desbanir esse usuário.",
                ephemeral=True
            )

        except discord.HTTPException:
            await interaction.response.send_message(
                "❌ Não consegui desbanir esse usuário.",
                ephemeral=True
            )

    # ==================================================
    # ❌ ERROS
    # ==================================================

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        mensagem = "❌ Ocorreu um erro ao executar esse comando."

        if isinstance(error, app_commands.MissingPermissions):
            mensagem = "❌ Você não possui permissão para usar esse comando."

        elif isinstance(error, app_commands.BotMissingPermissions):
            mensagem = "❌ Eu não tenho permissão suficiente para executar essa ação."

        try:
            if interaction.response.is_done():
                await interaction.followup.send(
                    mensagem,
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    mensagem,
                    ephemeral=True
                )
        except discord.HTTPException:
            pass


# ==================================================
# ⚙️ SETUP
# ==================================================

async def setup(bot):
    await bot.add_cog(Moderacao(bot))