import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
from datetime import datetime, timedelta, timezone

COR_CUPHEAD = 0xC48A3A
COR_VERDE = 0x2ECC71
COR_VERMELHO = 0x8B3A3A
COR_ESCURO = 0x2B1B12

GIF_SORTEIO = "https://cdn.discordapp.com/attachments/1502524697907302562/1505792889530355792/content.png?ex=6a0bea69&is=6a0a98e9&hm=bdeba034cd37d7c4919036e74c7c924f80a8f2a2a40edcc0a210a14cf0953fb5&"

CARGOS_ADMIN_SORTEIO = [
    1492220245996343377,
    1480334545944449024,
    1485706762765074544,
    1483191687927828766,
    1480349452744265759,
    1501356975491907664,
]


def formatar_tempo(segundos: int):
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60

    if horas > 0 and minutos > 0:
        return f"{horas}h {minutos}min"
    if horas > 0:
        return f"{horas}h"
    if minutos > 0:
        return f"{minutos}min"
    return "menos de 1 minuto"


class AdminSorteioView(discord.ui.View):
    def __init__(self, sorteio_view):
        super().__init__(timeout=180)
        self.sorteio_view = sorteio_view

    @discord.ui.button(label="Participantes", emoji="👥", style=discord.ButtonStyle.primary)
    async def ver_participantes(self, interaction: discord.Interaction, button: discord.ui.Button):
        participantes = self.sorteio_view.participantes

        if not participantes:
            texto = "Nenhum jogador entrou nessa rodada ainda."
        else:
            texto = "\n".join(
                f"`{i + 1}.` {m.mention}" for i, m in enumerate(participantes)
            )

        embed = discord.Embed(
            title="👥 Participantes da Rodada",
            description=texto,
            color=COR_CUPHEAD
        )
        embed.set_footer(text=f"Total: {len(participantes)} participante(s)")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Reroll", emoji="🎲", style=discord.ButtonStyle.success)
    async def reroll(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.sorteio_view.finalizado:
            return await interaction.response.send_message(
                "❌ O reroll só pode ser feito depois que o sorteio for finalizado.",
                ephemeral=True
            )

        if len(self.sorteio_view.participantes) < self.sorteio_view.ganhadores:
            return await interaction.response.send_message(
                "❌ Não há participantes suficientes para fazer reroll.",
                ephemeral=True
            )

        vencedores = random.sample(
            self.sorteio_view.participantes,
            self.sorteio_view.ganhadores
        )

        mencoes = ", ".join(v.mention for v in vencedores)

        embed = discord.Embed(
            title="🎲 REROLL DO CASSINO!",
            description=(
                "A roleta girou novamente...\n\n"
                f"🎁 **Prêmio:** `{self.sorteio_view.premio}`\n"
                f"👑 **Novo(s) vencedor(es):** {mencoes}"
            ),
            color=COR_VERDE
        )
        embed.set_image(url=GIF_SORTEIO)
        embed.set_footer(text="Família Sant's • Cassino Retrô")

        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Finalizar", emoji="🏁", style=discord.ButtonStyle.success)
    async def finalizar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        if self.sorteio_view.finalizado:
            return await interaction.followup.send(
                "❌ Este sorteio já foi finalizado.",
                ephemeral=True
            )

        await self.sorteio_view.finalizar_sorteio(self.sorteio_view.mensagem)

        await interaction.followup.send(
            "🏁 Sorteio finalizado com sucesso.",
            ephemeral=True
        )

    @discord.ui.button(label="Cancelar", emoji="❌", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        if self.sorteio_view.finalizado:
            return await interaction.followup.send(
                "❌ Este sorteio já foi encerrado.",
                ephemeral=True
            )

        await self.sorteio_view.cancelar_sorteio(self.sorteio_view.mensagem)

        await interaction.followup.send(
            "❌ Sorteio cancelado com sucesso.",
            ephemeral=True
        )


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
        self.cancelado = False
        self.mensagem = None

        self.inicio = datetime.now(timezone.utc)
        self.fim = self.inicio + timedelta(seconds=tempo_segundos)

    def requisito_texto(self):
        if self.requisito is None:
            return "`Nenhum requisito`"
        return self.requisito.mention

    def timestamp_fim(self):
        return f"<t:{int(self.fim.timestamp())}:R>"

    def criar_embed(self, status="🎬 RODADA EM ANDAMENTO"):
        embed = discord.Embed(
            title="🎰 『 SORTEIO DO CASSINO RETRÔ 』 🎰",
            description=(
                "A mesa está aberta, os dados estão girando e a sorte está lançada!\n\n"
                "🎟️ Clique em **Participar** para entrar na rodada.\n"
                "🚪 Clique em **Sair** caso queira abandonar o jogo.\n"
                "⚙️ O botão **Admin** é exclusivo para a equipe.\n\n"
                "━━━━━━━━━━━━━━━━━━━━"
            ),
            color=COR_CUPHEAD
        )

        embed.add_field(
            name="🎁 PRÊMIO",
            value=f"```{self.premio}```",
            inline=False
        )

        embed.add_field(
            name="📜 DESCRIÇÃO",
            value=f"{self.descricao}",
            inline=False
        )

        embed.add_field(
            name="👑 GANHADORES",
            value=f"`{self.ganhadores}`",
            inline=True
        )

        embed.add_field(
            name="🎟️ PARTICIPANTES",
            value=f"`{len(self.participantes)}` jogador(es)",
            inline=True
        )

        embed.add_field(
            name="🎯 REQUISITO",
            value=self.requisito_texto(),
            inline=True
        )

        embed.add_field(
            name="⏳ ENCERRA",
            value=self.timestamp_fim(),
            inline=True
        )

        embed.add_field(
            name="📌 STATUS",
            value=f"```{status}```",
            inline=False
        )

        embed.set_image(url=GIF_SORTEIO)
        embed.set_footer(text="Família Sant's • Cuphead Casino")

        return embed

    async def atualizar_embed(self):
        if not self.mensagem:
            return

        try:
            await self.mensagem.edit(
                embed=self.criar_embed(),
                view=self
            )
        except discord.NotFound:
            self.finalizado = True
        except discord.HTTPException:
            pass

    def tem_requisito(self, membro: discord.Member):
        if self.requisito is None:
            return True

        return self.requisito in membro.roles

    def tem_admin(self, membro: discord.Member):
        if membro.guild_permissions.administrator:
            return True

        return any(cargo.id in CARGOS_ADMIN_SORTEIO for cargo in membro.roles)

    @discord.ui.button(label="Participar", emoji="🎟️", style=discord.ButtonStyle.danger)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.finalizado:
            return await interaction.response.send_message(
                "🎬 Este sorteio já foi encerrado.",
                ephemeral=True
            )

        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message(
                "❌ Não consegui verificar seus cargos.",
                ephemeral=True
            )

        if not self.tem_requisito(interaction.user):
            return await interaction.response.send_message(
                f"❌ Você precisa do cargo {self.requisito.mention} para participar.",
                ephemeral=True
            )

        if interaction.user in self.participantes:
            return await interaction.response.send_message(
                "🎟️ Você já está participando dessa rodada.",
                ephemeral=True
            )

        self.participantes.append(interaction.user)

        await interaction.response.send_message(
            "🎰 Você entrou na rodada! Boa sorte no cassino.",
            ephemeral=True
        )

        await self.atualizar_embed()

    @discord.ui.button(label="Sair", emoji="🚪", style=discord.ButtonStyle.secondary)
    async def sair(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.finalizado:
            return await interaction.response.send_message(
                "🎬 Este sorteio já foi encerrado.",
                ephemeral=True
            )

        if interaction.user not in self.participantes:
            return await interaction.response.send_message(
                "🚪 Você não está participando desse sorteio.",
                ephemeral=True
            )

        self.participantes.remove(interaction.user)

        await interaction.response.send_message(
            "🚪 Você saiu da rodada.",
            ephemeral=True
        )

        await self.atualizar_embed()

    @discord.ui.button(label="Admin", emoji="⚙️", style=discord.ButtonStyle.primary)
    async def admin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message(
                "❌ Não consegui verificar suas permissões.",
                ephemeral=True
            )

        if not self.tem_admin(interaction.user):
            return await interaction.response.send_message(
                "❌ Você não pode acessar este painel.",
                ephemeral=True
            )

        await interaction.response.send_message(
            "⚙️ Painel administrativo do sorteio:",
            view=AdminSorteioView(self),
            ephemeral=True
        )

    async def cancelar_sorteio(self, message: discord.Message):
        if self.finalizado:
            return

        self.finalizado = True
        self.cancelado = True

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(
            title="❌ 『 SORTEIO CANCELADO 』",
            description=(
                "━━━━━━━━━━━━━━━━━━━━\n"
                "A rodada foi cancelada pela equipe.\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🎁 **Prêmio:** `{self.premio}`\n"
                f"🎟️ **Participantes:** `{len(self.participantes)}`"
            ),
            color=COR_VERMELHO
        )

        embed.set_image(url=GIF_SORTEIO)
        embed.set_footer(text="Família Sant's • Sorteio cancelado")

        try:
            await message.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass

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
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "A roleta parou, mas ninguém levou o prêmio.\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🎁 **Prêmio:** `{self.premio}`\n"
                    f"👥 **Participantes:** `{len(self.participantes)}`\n"
                    f"👑 **Ganhadores necessários:** `{self.ganhadores}`\n\n"
                    "❌ Não houve participantes suficientes."
                ),
                color=COR_VERMELHO
            )

            embed.set_image(url=GIF_SORTEIO)
            embed.set_footer(text="Família Sant's • Sem vencedores")

            try:
                await message.edit(embed=embed, view=self)
            except discord.HTTPException:
                pass

            return

        vencedores = random.sample(
            self.participantes,
            self.ganhadores
        )

        mencoes = ", ".join(v.mention for v in vencedores)

        embed = discord.Embed(
            title="🏆 『 A ROLETA ESCOLHEU! 』 🏆",
            description=(
                "━━━━━━━━━━━━━━━━━━━━\n"
                "O cassino fechou as portas e a sorte falou mais alto!\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🎁 **Prêmio:** `{self.premio}`\n\n"
                f"👑 **Vencedor(es):**\n{mencoes}\n\n"
                f"🎟️ **Total de participantes:** `{len(self.participantes)}`\n\n"
                "☕ Obrigado a todos que participaram da rodada."
            ),
            color=COR_VERDE
        )

        embed.set_image(url=GIF_SORTEIO)
        embed.set_footer(text="Família Sant's • Cuphead Casino")

        try:
            await message.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass

        try:
            await message.reply(
                f"🏆 Parabéns {mencoes}! Vocês venceram o sorteio de **{self.premio}**!"
            )
        except discord.HTTPException:
            pass


class Sorteio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="sorteio",
        description="Cria um sorteio no tema Cuphead."
    )
    @app_commands.describe(
        premio="Prêmio do sorteio",
        descricao="Descrição do prêmio",
        ganhadores="Quantidade de ganhadores",
        horas="Duração em horas",
        requisito="Cargo necessário para participar"
    )
    async def sorteio(
        self,
        interaction: discord.Interaction,
        premio: str,
        descricao: str,
        ganhadores: int,
        horas: int,
        requisito: discord.Role = None
    ):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ Apenas administradores podem criar sorteios.",
                ephemeral=True
            )

        if ganhadores <= 0:
            return await interaction.response.send_message(
                "❌ A quantidade de ganhadores precisa ser maior que 0.",
                ephemeral=True
            )

        if horas <= 0:
            return await interaction.response.send_message(
                "❌ A duração precisa ser maior que 0.",
                ephemeral=True
            )

        if horas > 720:
            return await interaction.response.send_message(
                "❌ A duração máxima permitida é de 720 horas.",
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

        await interaction.response.defer(ephemeral=True)

        mensagem = await interaction.channel.send(
            embed=view.criar_embed(),
            view=view
        )

        view.mensagem = mensagem

        await interaction.followup.send(
            "🎰 Sorteio criado com sucesso!",
            ephemeral=True
        )

        await asyncio.sleep(tempo_segundos)

        if not view.finalizado:
            await view.finalizar_sorteio(mensagem)


async def setup(bot):
    await bot.add_cog(Sorteio(bot))