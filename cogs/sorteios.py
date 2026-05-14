import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random

COR_CUPHEAD = 0xC48A3A
COR_FINALIZADO = 0x8B3A3A

GIF_SORTEIO = "https://i.imgur.com/82XpPJu.png"


class SorteioView(discord.ui.View):
    def __init__(self, premio, descricao, ganhadores, requisito, tempo_segundos):
        super().__init__(timeout=None)

        self.premio = premio
        self.descricao = descricao
        self.ganhadores = ganhadores
        self.requisito = requisito
        self.tempo_segundos = tempo_segundos

        self.participantes = []
        self.finalizado = False

    def criar_embed(self, status="🎬 EM ANDAMENTO"):
        embed = discord.Embed(
            title="🎞️ 『 SORTEIO DO CASSINO 』 🎞️",
            description=(
                "━━━━━━━━━━━━━━━━━━\n"
                "🎰 UMA NOVA RODADA COMEÇOU\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "As cortinas se abriram.\n"
                "A roleta começou a girar.\n"
                "Agora, a sorte decidirá o próximo vencedor.\n\n"
                "🎟️ Clique em **Participar** para entrar na rodada.\n"
                "🎲 Apenas quem cumprir os requisitos poderá concorrer.\n\n"
                "━━━━━━━━━━━━━━━━━━"
            ),
            color=COR_CUPHEAD
        )

        embed.set_image(url=GIF_SORTEIO)

        embed.add_field(name="🎁 PRÊMIO", value=f"╰➤ `{self.premio}`", inline=True)
        embed.add_field(name="📜 DESCRIÇÃO", value=f"╰➤ `{self.descricao}`", inline=True)
        embed.add_field(name="👑 GANHADORES", value=f"╰➤ `{self.ganhadores}`", inline=True)
        embed.add_field(name="🎟️ PARTICIPANTES", value=f"╰➤ `{len(self.participantes)} jogadores`", inline=True)
        embed.add_field(name="🎯 REQUISITO", value=f"╰➤ `{self.requisito}`", inline=True)
        embed.add_field(name="⏳ TERMINA EM", value=f"╰➤ `{self.tempo_segundos // 3600} horas`", inline=True)

        embed.add_field(
            name="📌 STATUS DA RODADA",
            value=f"```{status}```",
            inline=False
        )

        embed.set_footer(text="Família Sant's • Cassino Retrô")
        return embed

    async def atualizar_embed(self, interaction: discord.Interaction):
        await interaction.message.edit(embed=self.criar_embed(), view=self)

    def usuario_tem_requisito(self, member: discord.Member):
        if self.requisito.lower() in ["nenhum", "não", "nao", "sem requisito"]:
            return True

        cargo = discord.utils.get(member.guild.roles, name=self.requisito)

        if cargo is None:
            return False

        return cargo in member.roles

    @discord.ui.button(label="Participar", emoji="🎟️", style=discord.ButtonStyle.danger)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.finalizado:
            return await interaction.response.send_message(
                "🎬 Este sorteio já foi finalizado.",
                ephemeral=True
            )

        if not self.usuario_tem_requisito(interaction.user):
            return await interaction.response.send_message(
                f"❌ Você precisa do cargo `{self.requisito}` para participar deste sorteio.",
                ephemeral=True
            )

        if interaction.user in self.participantes:
            return await interaction.response.send_message(
                "🎟️ Você já está participando desta rodada.",
                ephemeral=True
            )

        self.participantes.append(interaction.user)

        await interaction.response.send_message(
            "🎰 Você entrou na rodada do sorteio!",
            ephemeral=True
        )

        await self.atualizar_embed(interaction)

    @discord.ui.button(label="Sair", emoji="🚪", style=discord.ButtonStyle.secondary)
    async def sair(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participantes:
            return await interaction.response.send_message(
                "🚪 Você não está participando deste sorteio.",
                ephemeral=True
            )

        self.participantes.remove(interaction.user)

        await interaction.response.send_message(
            "🚪 Você saiu da rodada.",
            ephemeral=True
        )

        await self.atualizar_embed(interaction)

    @discord.ui.button(label="Reroll", emoji="🎲", style=discord.ButtonStyle.primary)
    async def reroll(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message(
                "❌ Apenas a equipe pode usar o reroll.",
                ephemeral=True
            )

        if len(self.participantes) < self.ganhadores:
            return await interaction.response.send_message(
                "❌ Não há participantes suficientes.",
                ephemeral=True
            )

        vencedores = random.sample(self.participantes, self.ganhadores)
        mencoes = ", ".join(v.mention for v in vencedores)

        await interaction.response.send_message(
            f"🎲 **REROLL REALIZADO!**\n\n"
            f"🎁 Prêmio: **{self.premio}**\n"
            f"👑 Novo vencedor: {mencoes}"
        )

    @discord.ui.button(label="Finalizar", emoji="🏁", style=discord.ButtonStyle.success)
    async def finalizar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message(
                "❌ Apenas a equipe pode finalizar.",
                ephemeral=True
            )

        await interaction.response.defer()
        await self.finalizar_sorteio(interaction.message)

    @discord.ui.button(label="Cancelar", emoji="❌", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message(
                "❌ Apenas a equipe pode cancelar.",
                ephemeral=True
            )

        self.finalizado = True

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(
            title="❌ 『 SORTEIO CANCELADO 』",
            description=(
                "━━━━━━━━━━━━━━━━━━\n"
                "A rodada foi interrompida pela equipe.\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                f"🎁 Prêmio cancelado:\n`{self.premio}`"
            ),
            color=COR_FINALIZADO
        )

        embed.set_image(url=GIF_SORTEIO)
        embed.set_footer(text="Família Sant's • Cassino Retrô")

        await interaction.response.edit_message(embed=embed, view=self)

    async def finalizar_sorteio(self, message: discord.Message):
        if self.finalizado:
            return

        self.finalizado = True

        for item in self.children:
            item.disabled = True

        if len(self.participantes) < self.ganhadores:
            embed = discord.Embed(
                title="🎬 『 FIM DA RODADA 』",
                description=(
                    "━━━━━━━━━━━━━━━━━━\n"
                    "A rodada foi encerrada.\n"
                    "━━━━━━━━━━━━━━━━━━\n\n"
                    f"🎭 O sorteio **{self.premio}** foi encerrado,\n"
                    "mas não teve participantes suficientes.\n\n"
                    "🕰️ Volte na próxima sessão."
                ),
                color=COR_FINALIZADO
            )

            embed.set_image(url=GIF_SORTEIO)
            embed.set_footer(text="Família Sant's • Cassino Retrô")

            return await message.edit(embed=embed, view=self)

        vencedores = random.sample(self.participantes, self.ganhadores)
        mencoes = ", ".join(v.mention for v in vencedores)

        embed = discord.Embed(
            title="🏆 『 VENCEDOR DEFINIDO 』",
            description=(
                "━━━━━━━━━━━━━━━━━━\n"
                "A roleta parou!\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                f"🎁 **Prêmio:** `{self.premio}`\n\n"
                f"👑 **Vencedor(es):** {mencoes}\n\n"
                "🎰 Obrigado por participar."
            ),
            color=COR_CUPHEAD
        )

        embed.set_image(url=GIF_SORTEIO)
        embed.set_footer(text="Família Sant's • Cassino Retrô")

        await message.edit(embed=embed, view=self)


class Sorteio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="sorteio",
        description="Cria um sorteio estilo Cuphead."
    )
    @app_commands.describe(
        premio="Prêmio do sorteio",
        descricao="Descrição do prêmio",
        ganhadores="Quantidade de ganhadores",
        horas="Duração em horas",
        requisito="Nome exato do cargo necessário para participar. Use Nenhum se não tiver requisito."
    )
    async def sorteio(
        self,
        interaction: discord.Interaction,
        premio: str,
        descricao: str,
        ganhadores: int,
        horas: int,
        requisito: str = "Nenhum"
    ):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message(
                "❌ Apenas a equipe pode criar sorteios.",
                ephemeral=True
            )

        if ganhadores <= 0:
            return await interaction.response.send_message(
                "❌ A quantidade de ganhadores precisa ser maior que 0.",
                ephemeral=True
            )

        if horas <= 0:
            return await interaction.response.send_message(
                "❌ A duração precisa ser maior que 0 horas.",
                ephemeral=True
            )

        tempo_segundos = horas * 3600

        view = SorteioView(
            premio=premio,
            descricao=descricao,
            ganhadores=ganhadores,
            requisito=requisito,
            tempo_segundos=tempo_segundos
        )

        await interaction.response.send_message(
            embed=view.criar_embed(),
            view=view
        )

        mensagem = await interaction.original_response()

        await asyncio.sleep(tempo_segundos)

        if not view.finalizado:
            await view.finalizar_sorteio(mensagem)


async def setup(bot):
    await bot.add_cog(Sorteio(bot))