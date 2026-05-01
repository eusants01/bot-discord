import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from utils.db import conn, cursor

COR_JUJUTSU = 0x7B2CFF
CANAL_CONQUISTAS_ID = 1498134533839650838

# 🏆 CONQUISTAS
CONQUISTAS = {
    # COMUM
    "despertar": {"emoji": "🧿", "nome": "Despertar", "descricao": "Sua energia amaldiçoada começou a fluir.", "raridade": "COMUM"},
    "eco_no_dominio": {"emoji": "📢", "nome": "Eco no Domínio", "descricao": "Sua presença começou a ser notada.", "raridade": "COMUM"},
    "marca_inicial": {"emoji": "🩸", "nome": "Marca Inicial", "descricao": "Você deixou sua primeira marca.", "raridade": "COMUM"},

    # RARO
    "tecnica_formada": {"emoji": "🌀", "nome": "Técnica Formada", "descricao": "Você começou a dominar sua técnica.", "raridade": "RARO"},
    "quebra_barreira": {"emoji": "💥", "nome": "Quebra de Barreira", "descricao": "Você rompeu limites dentro do domínio.", "raridade": "RARO"},
    "energia_densa": {"emoji": "🌑", "nome": "Energia Densa", "descricao": "Sua presença se tornou pesada.", "raridade": "RARO"},

    # ÉPICO
    "expansao_dominio": {"emoji": "🌌", "nome": "Expansão de Domínio", "descricao": "Você abriu um domínio próprio.", "raridade": "EPICO"},
    "olhos_do_infinito": {"emoji": "👁️", "nome": "Olhos do Infinito", "descricao": "Você enxerga além do normal.", "raridade": "EPICO"},
    "ritual_perfeito": {"emoji": "🕯️", "nome": "Ritual Perfeito", "descricao": "Seu controle atingiu outro nível.", "raridade": "EPICO"},

    # SECRETA
    "voz_da_sombra": {"emoji": "🔒", "nome": "???", "descricao": "Algo respondeu do outro lado.", "raridade": "SECRETA"},
    "pacto_proibido": {"emoji": "🔒", "nome": "???", "descricao": "Um pacto foi feito…", "raridade": "SECRETA"},
    "alma_transfigurada": {"emoji": "🧠", "nome": "???", "descricao": "Sua alma foi moldada.", "raridade": "SECRETA"},

    # LENDÁRIA
    "herdeiro_do_caos": {"emoji": "🔥", "nome": "Herdeiro do Caos", "descricao": "Você não pertence a este mundo.", "raridade": "LENDARIA"},
    "rei_das_maldicoes": {"emoji": "👑", "nome": "Rei das Maldições", "descricao": "O domínio se curva a você.", "raridade": "LENDARIA"},
    "membro_da_familia": {"emoji": "🏠", "nome": "Membro da Família", "descricao": "Você faz parte da Família Sant’s.", "raridade": "LENDARIA"}
}

# 👑 TÍTULOS AUTOMÁTICOS
TITULOS = {
    "voz_da_sombra": "🔒 Portador da Sombra",
    "pacto_proibido": "🩸 Marcado pelo Pacto",
    "alma_transfigurada": "🧠 Alma Corrompida",
    "herdeiro_do_caos": "🔥 Herdeiro do Caos",
    "rei_das_maldicoes": "👑 O Escolhido",
    "membro_da_familia": "🏠 Membro Supremo"
}

# 🎯 FUNÇÃO PRINCIPAL
async def liberar_conquista(bot, usuario, conquista_id):

    cursor.execute(
        "SELECT 1 FROM conquistas WHERE user_id=? AND conquista_id=?",
        (str(usuario.id), conquista_id)
    )
    if cursor.fetchone():
        return False

    cursor.execute(
        "INSERT INTO conquistas VALUES (?, ?, ?)",
        (str(usuario.id), conquista_id, datetime.now().strftime("%d/%m/%Y %H:%M"))
    )
    conn.commit()

    # 👑 aplica título automático
    if conquista_id in TITULOS:
        cursor.execute(
            "INSERT OR REPLACE INTO titulos VALUES (?, ?)",
            (str(usuario.id), TITULOS[conquista_id])
        )
        conn.commit()

    canal = bot.get_channel(CANAL_CONQUISTAS_ID)
    if canal:
        await canal.send(f"🏆 {usuario.mention} desbloqueou **{CONQUISTAS[conquista_id]['nome']}**")

    return True


# 🔥 AUTOCOMPLETE
async def autocomplete_conquista(interaction, current):
    return [
        app_commands.Choice(name=f"{c['nome']} ({cid})", value=cid)
        for cid, c in CONQUISTAS.items()
        if current.lower() in cid.lower()
    ][:25]


class Conquistas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="darconquista")
    @app_commands.autocomplete(conquista_id=autocomplete_conquista)
    async def darconquista(self, interaction, membro: discord.Member, conquista_id: str):

        if conquista_id not in CONQUISTAS:
            return await interaction.response.send_message("Conquista inválida.", ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Sem permissão.", ephemeral=True)

        ganhou = await liberar_conquista(self.bot, membro, conquista_id)

        if not ganhou:
            return await interaction.response.send_message("Já possui.", ephemeral=True)

        await interaction.response.send_message("✅ Conquista entregue.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Conquistas(bot))
    