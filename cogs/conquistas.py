import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from utils.db import conn, cursor

COR_JUJUTSU = 0x7B2CFF

# 🏆 CONQUISTAS COMPLETAS
CONQUISTAS = {
    # COMUM
    "despertar": {"emoji": "🧿", "nome": "Despertar"},
    "eco_no_dominio": {"emoji": "📢", "nome": "Eco no Domínio"},
    "marca_inicial": {"emoji": "🩸", "nome": "Marca Inicial"},

    # RARO
    "tecnica_formada": {"emoji": "🌀", "nome": "Técnica Formada"},
    "quebra_barreira": {"emoji": "💥", "nome": "Quebra de Barreira"},
    "energia_densa": {"emoji": "🌑", "nome": "Energia Densa"},

    # ÉPICO
    "expansao_dominio": {"emoji": "🌌", "nome": "Expansão de Domínio"},
    "olhos_do_infinito": {"emoji": "👁️", "nome": "Olhos do Infinito"},
    "ritual_perfeito": {"emoji": "🕯️", "nome": "Ritual Perfeito"},

    # SECRETA
    "voz_da_sombra": {"emoji": "🔒", "nome": "???"},
    "pacto_proibido": {"emoji": "🔒", "nome": "???"},
    "alma_transfigurada": {"emoji": "🧠", "nome": "???"},

    # LENDÁRIA
    "herdeiro_do_caos": {"emoji": "🔥", "nome": "Herdeiro do Caos"},
    "rei_das_maldicoes": {"emoji": "👑", "nome": "Rei das Maldições"},
    "membro_da_familia": {"emoji": "🏠", "nome": "Membro da Família"},
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
    @app_commands.command(name="darconquista", description="Dar conquista a um membro")
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

    # 📜 VER CONQUISTAS (ESTILO PAGINADO)
    @app_commands.command(name="conquistas", description="Veja suas conquistas")
    async def conquistas(self, interaction: discord.Interaction):

        cursor.execute(
            "SELECT conquista_id FROM conquistas WHERE user_id=?",
            (str(interaction.user.id),)
        )

        dados = [cid for (cid,) in cursor.fetchall()]

        lista = list(CONQUISTAS.items())
        total = len(lista)
        conquistadas = len(dados)

        itens_por_pagina = 4
        paginas = [lista[i:i+itens_por_pagina] for i in range(0, total, itens_por_pagina)]

        pagina_atual = 0

        def criar_embed(pagina):
            embed = discord.Embed(
                title=f"🌀 Domínio de {interaction.user.display_name}",
                description=f"🌀 **Todas as Conquistas [{conquistadas}/{total}]**",
                color=COR_JUJUTSU
            )

            for cid, c in paginas[pagina]:
                if cid in dados:
                    embed.add_field(
                        name=f"{c['emoji']} {c['nome']}",
                        value="Conquista desbloqueada.",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="🔒 Conquista Bloqueada",
                        value="Continue explorando o domínio para revelar.",
                        inline=False
                    )

            embed.set_footer(text=f"Página {pagina+1}/{len(paginas)} • Família Sant’s")
            return embed

        class ViewPaginada(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=120)

            @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
            async def voltar(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                nonlocal pagina_atual
                if pagina_atual > 0:
                    pagina_atual -= 1
                await interaction_btn.response.edit_message(embed=criar_embed(pagina_atual), view=self)

            @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
            async def avancar(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                nonlocal pagina_atual
                if pagina_atual < len(paginas) - 1:
                    pagina_atual += 1
                await interaction_btn.response.edit_message(embed=criar_embed(pagina_atual), view=self)

        await interaction.response.send_message(
            embed=criar_embed(pagina_atual),
            view=ViewPaginada(),
            ephemeral=True
        )

    # 🔑 CODIGO
    @app_commands.command(name="codigo", description="Resgatar código secreto")
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


async def setup(bot):
    await bot.add_cog(Conquistas(bot))