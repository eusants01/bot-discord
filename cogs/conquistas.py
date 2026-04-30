import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime

ARQUIVO_DADOS = "dados_conquistas.json"
ARQUIVO_MSG = "contador_msgs.json"
COR_JUJUTSU = 0x7B2CFF

CONQUISTAS = {
    "primeiro_selo": {"emoji": "🩸", "nome": "Primeiro Selo", "descricao": "Despertou sua primeira marca dentro do domínio."},
    "dominio_revelado": {"emoji": "🌀", "nome": "Domínio Revelado", "descricao": "Visualizou suas conquistas pela primeira vez."},
    "contrato_aberto": {"emoji": "📜", "nome": "Contrato Aberto", "descricao": "Abriu seu primeiro ticket amaldiçoado."},
    "voz_do_dominio": {"emoji": "📢", "nome": "Voz do Domínio", "descricao": "Enviou 50 mensagens dentro da Família."},
    "presenca_constante": {"emoji": "👁️", "nome": "Presença Constante", "descricao": "Enviou 100 mensagens dentro do domínio."},
    "exorcista_vitorioso": {"emoji": "⚔️", "nome": "Exorcista Vitorioso", "descricao": "Venceu um evento da Família Sant’s."},
    "sangue_familia": {"emoji": "🩸", "nome": "Sangue da Família", "descricao": "Entrou na Família Sant’s."},
    "alianca_amaldicoada": {"emoji": "🤝", "nome": "Aliança Amaldiçoada", "descricao": "Criou laços dentro do domínio."},
    "observador_silencioso": {"emoji": "👁️", "nome": "Observador Silencioso", "descricao": "Acompanhou o domínio sem se expor."},
    "energia_instavel": {"emoji": "🔥", "nome": "Energia Instável", "descricao": "Enviou 200 mensagens no servidor."},
    "portador_do_caos": {"emoji": "💀", "nome": "Portador do Caos", "descricao": "Causou impacto dentro do domínio."},
    "herdeiro_do_dominio": {"emoji": "👑", "nome": "Herdeiro do Domínio", "descricao": "Alcançou reconhecimento na Família."},
    "sombra_oculta": {"emoji": "🔒", "nome": "???", "descricao": "Apenas os escolhidos descobrirão."},
    "lenda_proibida": {"emoji": "🕯️", "nome": "???", "descricao": "Uma presença que não deveria existir..."}
}


def carregar_json(arquivo):
    if not os.path.exists(arquivo):
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4, ensure_ascii=False)

    with open(arquivo, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_json(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


def carregar_dados():
    return carregar_json(ARQUIVO_DADOS)


def salvar_dados(dados):
    salvar_json(ARQUIVO_DADOS, dados)


def carregar_msgs():
    return carregar_json(ARQUIVO_MSG)


def salvar_msgs(dados):
    salvar_json(ARQUIVO_MSG, dados)


async def liberar_conquista(bot, usuario, conquista_id, canal=None):
    if conquista_id not in CONQUISTAS:
        return False

    dados = carregar_dados()
    user_id = str(usuario.id)

    if user_id not in dados:
        dados[user_id] = {}

    if conquista_id in dados[user_id]:
        return False

    dados[user_id][conquista_id] = datetime.now().strftime("%d/%m/%Y %H:%M")
    salvar_dados(dados)

    conquista = CONQUISTAS[conquista_id]

    if canal:
        embed = discord.Embed(
            title="🏆 Nova Conquista Desbloqueada",
            description=(
                f"{usuario.mention} despertou uma nova conquista!\n\n"
                f"{conquista['emoji']} **{conquista['nome']}**\n"
                f"{conquista['descricao']}"
            ),
            color=COR_JUJUTSU
        )
        await canal.send(embed=embed)

    return True


class ViewConquistas(discord.ui.View):
    def __init__(self, usuario, paginas):
        super().__init__(timeout=60)
        self.usuario = usuario
        self.paginas = paginas
        self.pagina = 0

    async def atualizar(self, interaction):
        await interaction.response.edit_message(
            embed=self.paginas[self.pagina],
            view=self
        )

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def anterior(self, interaction, button):
        if interaction.user.id != self.usuario.id:
            return await interaction.response.send_message("Esse painel não é seu.", ephemeral=True)

        if self.pagina > 0:
            self.pagina -= 1

        await self.atualizar(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def proxima(self, interaction, button):
        if interaction.user.id != self.usuario.id:
            return await interaction.response.send_message("Esse painel não é seu.", ephemeral=True)

        if self.pagina < len(self.paginas) - 1:
            self.pagina += 1

        await self.atualizar(interaction)


class Conquistas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        dados_msg = carregar_msgs()
        user_id = str(message.author.id)

        if user_id not in dados_msg:
            dados_msg[user_id] = 0

        dados_msg[user_id] += 1
        salvar_msgs(dados_msg)

        total = dados_msg[user_id]

        if total == 1:
            await liberar_conquista(self.bot, message.author, "primeiro_selo", message.channel)

        elif total == 50:
            await liberar_conquista(self.bot, message.author, "voz_do_dominio", message.channel)

        elif total == 100:
            await liberar_conquista(self.bot, message.author, "presenca_constante", message.channel)

        elif total == 200:
            await liberar_conquista(self.bot, message.author, "energia_instavel", message.channel)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        canal = member.guild.system_channel

        await liberar_conquista(
            self.bot,
            member,
            "sangue_familia",
            canal
        )

    @app_commands.command(name="conquistas", description="Veja suas conquistas dentro do domínio.")
    async def conquistas(self, interaction: discord.Interaction):
        await liberar_conquista(self.bot, interaction.user, "dominio_revelado")

        dados = carregar_dados()
        user_data = dados.get(str(interaction.user.id), {})

        total = len(CONQUISTAS)
        conquistadas = len(user_data)

        lista = []

        for conquista_id, conquista in CONQUISTAS.items():
            if conquista_id in user_data:
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

        await interaction.response.send_message(
            embed=paginas[0],
            view=ViewConquistas(interaction.user, paginas)
        )

    @app_commands.command(name="darconquista", description="Dar uma conquista para um membro.")
    @app_commands.checks.has_permissions(administrator=True)
    async def darconquista(self, interaction: discord.Interaction, membro: discord.Member, conquista_id: str):
        if conquista_id not in CONQUISTAS:
            ids = "\n".join(CONQUISTAS.keys())
            return await interaction.response.send_message(
                f"Conquista não encontrada.\n\nIDs disponíveis:\n```{ids}```",
                ephemeral=True
            )

        ganhou = await liberar_conquista(self.bot, membro, conquista_id, interaction.channel)

        if not ganhou:
            return await interaction.response.send_message(
                f"{membro.mention} já possui essa conquista.",
                ephemeral=True
            )

        await interaction.response.send_message(
            f"✅ Conquista entregue para {membro.mention}.",
            ephemeral=True
        )

    @app_commands.command(name="codigo", description="Resgate um código secreto amaldiçoado.")
    async def codigo(self, interaction: discord.Interaction, codigo: str):
        codigos_secretos = {
            "MAHORAGA": "sombra_oculta",
            "SUKUNAHEIAN": "lenda_proibida"
        }

        codigo = codigo.upper().replace(" ", "")

        if codigo not in codigos_secretos:
            return await interaction.response.send_message(
                "❌ Código inválido. A barreira rejeitou sua tentativa.",
                ephemeral=True
            )

        conquista_id = codigos_secretos[codigo]

        ganhou = await liberar_conquista(
            self.bot,
            interaction.user,
            conquista_id,
            interaction.channel
        )

        if not ganhou:
            return await interaction.response.send_message(
                "Você já possui essa conquista.",
                ephemeral=True
            )

        await interaction.response.send_message(
            "✅ Código aceito. Uma conquista secreta foi despertada.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Conquistas(bot))