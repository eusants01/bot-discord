import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
from datetime import datetime

# ==================================================
# CONFIGURAÇÕES
# ==================================================

GUILD_ID = 123456789012345678
CANAL_LOGS_ID = 123456789012345678

COR_ROXA = 0x7B2CFF
COR_VERMELHA = 0xFF0000
COR_VERDE = 0x00FF88

# ==================================================
# BANNERS
# ==================================================

BANNER_WARN = "https://i.imgur.com/7VCFn76.png"
BANNER_BAN = "https://i.imgur.com/UqFKdTL.png"
BANNER_UNBAN = "https://i.imgur.com/SEU_BANNER_UNBAN.png"
BANNER_CLEAR = "https://i.imgur.com/SEU_BANNER_CLEAR.png"

# ==================================================
# BANCO DE DADOS
# ==================================================

conn = sqlite3.connect("moderacao.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS warns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER,
    user_id INTEGER,
    staff_id INTEGER,
    motivo TEXT,
    data TEXT
)
""")

conn.commit()


def salvar_warn(guild_id, user_id, staff_id, motivo):
    data = datetime.now().strftime("%d/%m/%Y %H:%M")

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
# COG
# ==================================================

class Moderacao(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ==================================================
    # LOGS
    # ==================================================

    async def enviar_log(self, guild, embed):
        canal = guild.get_channel(CANAL_LOGS_ID)

        if canal:
            await canal.send(embed=embed)

    # ==================================================
    # WARN
    # ==================================================

    @app_commands.command(
        name="warn",
        description="Aplica um warn em um membro."
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        motivo: str
    ):

        if membro.bot:
            await interaction.response.send_message(
                "❌ Você não pode aplicar warn em bots.",
                ephemeral=True
            )
            return

        if membro == interaction.user:
            await interaction.response.send_message(
                "❌ Você não pode aplicar warn em si mesmo.",
                ephemeral=True
            )
            return

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

        embed = discord.Embed(
            title="⚠️ WARN REGISTRADO",
            description="Um novo aviso foi aplicado dentro do domínio.",
            color=COR_ROXA
        )

        embed.add_field(
            name="👤 Membro",
            value=membro.mention,
            inline=True
        )

        embed.add_field(
            name="🛡️ Staff",
            value=interaction.user.mention,
            inline=True
        )

        embed.add_field(
            name="📌 Total de Warns",
            value=str(total_warns),
            inline=True
        )

        embed.add_field(
            name="📄 Motivo",
            value=motivo,
            inline=False
        )

        embed.set_thumbnail(
            url=membro.display_avatar.url
        )

        embed.set_image(
            url=BANNER_WARN
        )

        embed.set_footer(
            text=f"ID do membro: {membro.id}"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

        await self.enviar_log(
            interaction.guild,
            embed
        )

        try:
            await membro.send(
                f"⚠️ Você recebeu um warn em {interaction.guild.name}\n\n"
                f"📄 Motivo: {motivo}\n"
                f"📌 Total de warns: {total_warns}"
            )
        except:
            pass

    # ==================================================
    # VER WARNS
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
            await interaction.response.send_message(
                f"✅ {membro.mention} não possui warns.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"⚠️ Warns de {membro.display_name}",
            color=COR_ROXA
        )

        for warn_id, staff_id, motivo, data in warns[:10]:

            staff = interaction.guild.get_member(staff_id)

            if staff:
                staff_texto = staff.mention
            else:
                staff_texto = f"`{staff_id}`"

            embed.add_field(
                name=f"Warn ID: {warn_id}",
                value=(
                    f"🛡️ Staff: {staff_texto}\n"
                    f"📄 Motivo: {motivo}\n"
                    f"📅 Data: {data}"
                ),
                inline=False
            )

        embed.set_thumbnail(
            url=membro.display_avatar.url
        )

        embed.set_footer(
            text=f"Total de warns: {len(warns)}"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    # ==================================================
    # REMOVER WARN
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
            await interaction.response.send_message(
                "❌ Nenhum warn encontrado com esse ID.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="✅ WARN REMOVIDO",
            description=f"O warn `{warn_id}` foi removido.",
            color=COR_VERDE
        )

        embed.add_field(
            name="🛡️ Staff",
            value=interaction.user.mention,
            inline=False
        )

        embed.set_image(
            url=BANNER_CLEAR
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

        await self.enviar_log(
            interaction.guild,
            embed
        )

    # ==================================================
    # LIMPAR WARNS
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

        embed = discord.Embed(
            title="🧹 WARNS LIMPOS",
            description="Todos os warns do membro foram removidos.",
            color=COR_VERDE
        )

        embed.add_field(
            name="👤 Membro",
            value=membro.mention,
            inline=True
        )

        embed.add_field(
            name="🛡️ Staff",
            value=interaction.user.mention,
            inline=True
        )

        embed.add_field(
            name="📌 Warns removidos",
            value=str(quantidade),
            inline=False
        )

        embed.set_thumbnail(
            url=membro.display_avatar.url
        )

        embed.set_image(
            url=BANNER_CLEAR
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

        await self.enviar_log(
            interaction.guild,
            embed
        )

    # ==================================================
    # BAN
    # ==================================================

    @app_commands.command(
        name="ban",
        description="Bane um membro."
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        motivo: str
    ):

        if membro == interaction.user:
            await interaction.response.send_message(
                "❌ Você não pode banir a si mesmo.",
                ephemeral=True
            )
            return

        if membro.top_role >= interaction.user.top_role:
            await interaction.response.send_message(
                "❌ Esse membro possui cargo igual ou superior ao seu.",
                ephemeral=True
            )
            return

        try:
            await membro.send(
                f"🔨 Você foi banido de {interaction.guild.name}\n\n"
                f"📄 Motivo: {motivo}"
            )
        except:
            pass

        await membro.ban(
            reason=f"{motivo} | Staff: {interaction.user}"
        )

        embed = discord.Embed(
            title="🔨 MEMBRO BANIDO",
            description="Uma expulsão foi executada dentro do domínio.",
            color=COR_VERMELHA
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
            value=motivo,
            inline=False
        )

        embed.set_thumbnail(
            url=membro.display_avatar.url
        )

        embed.set_image(
            url=BANNER_BAN
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

        await self.enviar_log(
            interaction.guild,
            embed
        )

    # ==================================================
    # UNBAN
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

            user = await self.bot.fetch_user(
                int(user_id)
            )

            await interaction.guild.unban(
                user,
                reason=f"{motivo} | Staff: {interaction.user}"
            )

            embed = discord.Embed(
                title="✅ USUÁRIO DESBANIDO",
                description="O selo de expulsão foi removido.",
                color=COR_VERDE
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
                value=motivo,
                inline=False
            )

            embed.set_thumbnail(
                url=user.display_avatar.url
            )

            embed.set_image(
                url=BANNER_UNBAN
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            await self.enviar_log(
                interaction.guild,
                embed
            )

        except:
            await interaction.response.send_message(
                "❌ Não consegui desbanir esse usuário.",
                ephemeral=True
            )

    # ==================================================
    # ERROS
    # ==================================================

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):

        if isinstance(error, app_commands.MissingPermissions):

            await interaction.response.send_message(
                "❌ Você não possui permissão para usar esse comando.",
                ephemeral=True
            )

        else:

            await interaction.response.send_message(
                "❌ Ocorreu um erro ao executar esse comando.",
                ephemeral=True
            )


# ==================================================
# SETUP
# ==================================================

async def setup(bot):
    await bot.add_cog(Moderacao(bot))