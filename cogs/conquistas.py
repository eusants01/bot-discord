import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from utils.db import conn, cursor

COR_JUJUTSU = 0x7B2CFF

# 🏆 CONQUISTAS
CONQUISTAS = {
    "voz_da_sombra": {"emoji": "🔒", "nome": "???"},
    "rei_das_maldicoes": {"emoji": "👑", "nome": "Rei das Maldições"}
}

# 🔓 LIBERAR CONQUISTA
async def liberar_conquista(bot, usuario, conquista_id):

    cursor.execute(
        "SELECT 1 FROM conquistas WHERE user_id=? AND conquista_id=?",
        (str(usuario.id), conquista_id)
    )

    if cursor.fetchone():
        return False

    cursor.execute(
        "INSERT INTO conquistas VALUES (?, ?, ?)",
        (str(usuario.id), conquista_id, datetime.now().strftime("%d/%m/%Y"))
    )
    conn.commit()

    return True

# 🔍 AUTOCOMPLETE
async def autocomplete_conquista(interaction, current):
    return [
        app_commands.Choice(name=f"{c['nome']} ({cid})", value=cid)
        for cid, c in CONQUISTAS.items()
        if current.lower() in cid.lower()
    ][:25]


class Conquistas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 🎁 DAR CONQUISTA
    @app_commands.command(name="darconquista")
    @app_commands.autocomplete(conquista_id=autocomplete_conquista)
    async def darconquista(self, interaction: discord.Interaction, membro: discord.Member, conquista_id: str):

        if conquista_id not in CONQUISTAS:
            return await interaction.response.send_message("Conquista inválida.", ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Sem permissão.", ephemeral=True)

        ganhou = await liberar_conquista(self.bot, membro, conquista_id)

        if not ganhou:
            return await interaction.response.send_message("Já possui.", ephemeral=True)

        await interaction.response.send_message("✅ Conquista entregue.", ephemeral=True)

    # 📜 VER CONQUISTAS
    @app_commands.command(name="conquistas")
    async def conquistas(self, interaction: discord.Interaction):

        cursor.execute(
            "SELECT conquista_id FROM conquistas WHERE user_id=?",
            (str(interaction.user.id),)
        )

        dados = [cid for (cid,) in cursor.fetchall()]

        texto = ""
        for cid, c in CONQUISTAS.items():
            if cid in dados:
                texto += f"{c['emoji']} **{c['nome']}**\n"
            else:
                texto += "🔒 ???\n"

        embed = discord.Embed(
            title="🌀 Suas Conquistas",
            description=texto,
            color=COR_JUJUTSU
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # 🔑 CODIGO
    @app_commands.command(name="codigo")
    async def codigo(self, interaction: discord.Interaction, codigo: str):

        codigos = {
            "MAHORAGA": {"c": "voz_da_sombra", "limite": 1},
            "SUKUNAHEIAN": {"c": "rei_das_maldicoes", "limite": 5}
        }

        codigo = codigo.upper()

        if codigo not in codigos:
            return await interaction.response.send_message("❌ Código inválido.", ephemeral=True)

        user_id = str(interaction.user.id)

        cursor.execute("SELECT 1 FROM codigos WHERE codigo=? AND user_id=?", (codigo, user_id))
        if cursor.fetchone():
            return await interaction.response.send_message("Já usou.", ephemeral=True)

        cursor.execute("SELECT COUNT(*) FROM codigos WHERE codigo=?", (codigo,))
        usos = cursor.fetchone()[0]

        if usos >= codigos[codigo]["limite"]:
            return await interaction.response.send_message("Esgotado.", ephemeral=True)

        await liberar_conquista(self.bot, interaction.user, codigos[codigo]["c"])

        cursor.execute("INSERT INTO codigos VALUES (?, ?)", (codigo, user_id))
        conn.commit()

        await interaction.response.send_message("✅ Código aceito.", ephemeral=True)


# 🔥 ESSENCIAL
async def setup(bot):
    await bot.add_cog(Conquistas(bot))