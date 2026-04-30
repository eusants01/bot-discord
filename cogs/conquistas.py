import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime

ARQUIVO_DADOS = "dados_conquistas.json"
COR_JUJUTSU = 0x7B2CFF

CONQUISTAS = {
    "primeiro_selo": {
        "emoji": "🩸",
        "nome": "Primeiro Selo",
        "descricao": "Despertou sua primeira marca dentro do domínio."
    },
    "contrato_aberto": {
        "emoji": "📜",
        "nome": "Contrato Aberto",
        "descricao": "Abriu seu primeiro ticket amaldiçoado."
    },
    "exorcista_vitorioso": {
        "emoji": "⚔️",
        "nome": "Exorcista Vitorioso",
        "descricao": "Venceu um evento da Família Sant’s."
    },
    "sombra_oculta": {
        "emoji": "🔒",
        "nome": "???",
        "descricao": "Apenas os escolhidos descobrirão."
    },
    "dominio_revelado": {
        "emoji": "🌀",
        "nome": "Domínio Revelado",
        "descricao": "Visualizou suas conquistas pela primeira vez."
    }
}


def carregar_dados():
    if not os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4, ensure_ascii=False)

    with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


def liberar_conquista_usuario(user_id: int, conquista_id: str):
    if conquista_id not in CONQUISTAS:
        return False

    dados = carregar_dados()
    user_id = str(user_id)

    if user_id not in dados:
        dados[user_id] = {}

    if conquista_id in dados[user_id]:
        return False

    dados[user_id][conquista_id] = datetime.now().strftime("%d/%m/%Y %H:%M")
    salvar_dados(dados)
    return True


class ViewConquistas(discord.ui.View):
    def __init__(self, usuario: discord.User, paginas):
        super().__init__(timeout=60)
        self.usuario = usuario
        self.paginas = paginas
        self.pagina = 0

    async def atualizar(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=self.paginas[self.pagina],
            view=self
        )

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.usuario.id:
            return await interaction.response.send_message(
                "Esse painel não é seu.",
                ephemeral=True
            )

        if self.pagina > 0:
            self.pagina -= 1

        await self.atualizar(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def proxima(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.usuario.id:
            return await interaction.response.send_message(
                "Esse painel não é seu.",
                ephemeral=True
            )

        if self.pagina < len(self.paginas) - 1:
            self.pagina += 1

        await self.atualizar(interaction)


class Conquistas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="conquistas",
        description="Veja suas conquistas dentro do domínio."
    )
    async def conquistas(self, interaction: discord.Interaction):
        liberar_conquista_usuario(interaction.user.id, "dominio_revelado")

        dados = carregar_dados()
        user_data = dados.get(str(interaction.user.id), {})

        total = len(CONQUISTAS)
        conquistadas = len(user_data)

        lista = []

        for conquista_id, conquista in CONQUISTAS.items():
            desbloqueada = conquista_id in user_data

            if desbloqueada:
                texto = (
                    f"{conquista['emoji']} **{conquista['nome']}**\n"
                    f"{conquista['descricao']}\n"
                    f"**Conquistado em:** {user_data[conquista_id]}"
                )
            else:
                texto = (
                    f"🔒 **Conquista Bloqueada**\n"
                    f"Continue explorando o domínio para revelar."
                )

            lista.append(texto)

        paginas = []
        por_pagina = 4

        for i in range(0, len(lista), por_pagina):
            embed = discord.Embed(
                title=f"🌀 Todas as Conquistas [{conquistadas}/{total}]",
                description="\n\n".join(lista[i:i + por_pagina]),
                color=COR_JUJUTSU
            )

            embed.set_author(
                name=f"Domínio de {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )

            embed.set_footer(
                text=f"Página {(i // por_pagina) + 1}/{(len(lista) - 1) // por_pagina + 1} • Família Sant’s"
            )

            paginas.append(embed)

        view = ViewConquistas(interaction.user, paginas)

        await interaction.response.send_message(
            embed=paginas[0],
            view=view
        )

    @app_commands.command(
        name="darconquista",
        description="Dar uma conquista para um membro."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def darconquista(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        conquista_id: str
    ):
        if conquista_id not in CONQUISTAS:
            ids = "\n".join(CONQUISTAS.keys())
            return await interaction.response.send_message(
                f"Conquista não encontrada.\n\nIDs disponíveis:\n```{ids}```",
                ephemeral=True
            )

        ganhou = liberar_conquista_usuario(membro.id, conquista_id)

        if not ganhou:
            return await interaction.response.send_message(
                f"{membro.mention} já possui essa conquista.",
                ephemeral=True
            )

        conquista = CONQUISTAS[conquista_id]

        embed = discord.Embed(
            title="🏆 Nova Conquista Desbloqueada",
            description=(
                f"{membro.mention} despertou uma nova conquista!\n\n"
                f"{conquista['emoji']} **{conquista['nome']}**\n"
                f"{conquista['descricao']}"
            ),
            color=COR_JUJUTSU
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Conquistas(bot))