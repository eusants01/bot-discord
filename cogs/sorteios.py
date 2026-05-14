import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random

COR_CUPHEAD = 0xC48A3A
COR_FINALIZADO = 0x8B3A3A

GIF_SORTEIO = "https://i.imgur.com/82XpPJu.png"

# 🔥 CARGO QUE PODE ACESSAR O PAINEL ADMIN
CARGOS_ADMIN_SORTEIO = [
    1501356975491907664,
    1500545846427652166,
    12345678901234567890
]


class AdminSorteioView(discord.ui.View):
    def __init__(self, sorteio_view):
        super().__init__(timeout=120)
        self.sorteio_view = sorteio_view

    @discord.ui.button(
        label="Participantes",
        emoji="👥",
        style=discord.ButtonStyle.primary
    )
    async def ver_participantes(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        participantes = self.sorteio_view.participantes

        if not participantes:
            texto = "Nenhum participante."
        else:
            texto = "\n".join(
                [f"{i+1}. {m.mention}" for i, m in enumerate(participantes)]
            )

        embed = discord.Embed(
            title="👥 Participantes do Sorteio",
            description=texto,
            color=COR_CUPHEAD
        )

        embed.set_footer(
            text=f"Total: {len(participantes)} participante(s)"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    @discord.ui.button(
        label="Reroll",
        emoji="🎲",
        style=discord.ButtonStyle.primary
    )
    async def reroll(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if len(self.sorteio_view.participantes) < self.sorteio_view.ganhadores:
            return await interaction.response.send_message(
                "❌ Não há participantes suficientes.",
                ephemeral=True
            )

        vencedores = random.sample(
            self.sorteio_view.participantes,
            self.sorteio_view.ganhadores
        )

        mencoes = ", ".join(
            v.mention for v in vencedores
        )

        await interaction.response.send_message(
            f"🎲 **REROLL REALIZADO!**\n\n"
            f"🎁 Prêmio: **{self.sorteio_view.premio}**\n"
            f"👑 Novo vencedor: {mencoes}"
        )

    @discord.ui.button(
        label="Finalizar",
        emoji="🏁",
        style=discord.ButtonStyle.success
    )
    async def finalizar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.defer(
            ephemeral=True
        )

        await self.sorteio_view.finalizar_sorteio(
            self.sorteio_view.mensagem
        )

    @discord.ui.button(
        label="Cancelar",
        emoji="❌",
        style=discord.ButtonStyle.danger
    )
    async def cancelar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.defer(
            ephemeral=True
        )

        await self.sorteio_view.cancelar_sorteio(
            self.sorteio_view.mensagem
        )


class SorteioView(discord.ui.View):
    def __init__(
        self,
        premio,
        descricao,
        ganhadores,
        requisito,
        tempo_segundos
    ):

        super().__init__(timeout=None)

        self.premio = premio
        self.descricao = descricao
        self.ganhadores = ganhadores
        self.requisito = requisito
        self.tempo_segundos = tempo_segundos

        self.participantes = []
        self.finalizado = False
        self.mensagem = None

    def requisito_texto(self):
        if self.requisito is None:
            return "`Nenhum`"

        return self.requisito.mention

    def criar_embed(
        self,
        status="🎬 EM ANDAMENTO"
    ):

        embed = discord.Embed(
            title="🎞️ 『 SORTEIO DO CASSINO 』 🎞️",
            description=(
                "🎟️ Clique em **Participar** para entrar na rodada.\n"
                "🎯 Apenas quem cumprir os requisitos poderá concorrer.\n\n"
                "━━━━━━━━━━━━━━━━━━"
            ),
            color=COR_CUPHEAD
        )

        embed.add_field(
            name="🎁 PRÊMIO",
            value=f"╰➤ `{self.premio}`",
            inline=True
        )

        embed.add_field(
            name="📜 DESCRIÇÃO",
            value=f"╰➤ `{self.descricao}`",
            inline=True
        )

        embed.add_field(
            name="👑 GANHADORES",
            value=f"╰➤ `{self.ganhadores}`",
            inline=True
        )

        embed.add_field(
            name="🎟️ PARTICIPANTES",
            value=f"╰➤ `{len(self.participantes)} jogadores`",
            inline=True
        )

        embed.add_field(
            name="🎯 REQUISITO",
            value=f"╰➤ {self.requisito_texto()}",
            inline=True
        )

        embed.add_field(
            name="⏳ TERMINA EM",
            value=f"╰➤ `{self.tempo_segundos // 3600} horas`",
            inline=True
        )

        embed.add_field(
            name="📌 STATUS DA RODADA",
            value=f"```{status}```",
            inline=False
        )

        embed.set_image(
            url=GIF_SORTEIO
        )

        embed.set_footer(
            text="Família Sant's • Cassino Retrô"
        )

        return embed

    async def atualizar_embed(self):

        if self.mensagem:
            await self.mensagem.edit(
                embed=self.criar_embed(),
                view=self
            )

    def tem_requisito(
        self,
        membro: discord.Member
    ):

        if self.requisito is None:
            return True

        return self.requisito in membro.roles

    # 🎟️ PARTICIPAR
    @discord.ui.button(
        label="Participar",
        emoji="🎟️",
        style=discord.ButtonStyle.danger
    )
    async def participar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if self.finalizado:
            return await interaction.response.send_message(
                "🎬 Este sorteio já foi finalizado.",
                ephemeral=True
            )

        if not self.tem_requisito(
            interaction.user
        ):

            return await interaction.response.send_message(
                f"❌ Você precisa do cargo {self.requisito.mention} para participar.",
                ephemeral=True
            )

        if interaction.user in self.participantes:
            return await interaction.response.send_message(
                "🎟️ Você já está participando.",
                ephemeral=True
            )

        self.participantes.append(
            interaction.user
        )

        await interaction.response.send_message(
            "🎰 Você entrou na rodada!",
            ephemeral=True
        )

        await self.atualizar_embed()

    # 🚪 SAIR
    @discord.ui.button(
        label="Sair",
        emoji="🚪",
        style=discord.ButtonStyle.secondary
    )
    async def sair(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user not in self.participantes:
            return await interaction.response.send_message(
                "🚪 Você não participa deste sorteio.",
                ephemeral=True
            )

        self.participantes.remove(
            interaction.user
        )

        await interaction.response.send_message(
            "🚪 Você saiu da rodada.",
            ephemeral=True
        )

        await self.atualizar_embed()

    # ⚙️ ADMIN
    @discord.ui.button(
        label="Admin",
        emoji="⚙️",
        style=discord.ButtonStyle.primary
    )
    async def admin(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        cargo_admin = interaction.guild.get_role(
            CARGOS_ADMIN_SORTEIO
        )

        if cargo_admin not in interaction.user.roles:
            return await interaction.response.send_message(
                "❌ Você não pode acessar este painel.",
                ephemeral=True
            )

        await interaction.response.send_message(
            "⚙️ Painel administrativo do sorteio",
            view=AdminSorteioView(self),
            ephemeral=True
        )

    async def cancelar_sorteio(
        self,
        message: discord.Message
    ):

        if self.finalizado:
            return

        self.finalizado = True

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(
            title="❌ 『 SORTEIO CANCELADO 』",
            description=(
                "━━━━━━━━━━━━━━━━━━\n"
                "A rodada foi cancelada pela equipe.\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                f"🎁 **Prêmio:** `{self.premio}`"
            ),
            color=COR_FINALIZADO
        )

        embed.set_image(
            url=GIF_SORTEIO
        )

        embed.set_footer(
            text="Família Sant's • Cassino Retrô"
        )

        await message.edit(
            embed=embed,
            view=self
        )

    async def finalizar_sorteio(
        self,
        message: discord.Message
    ):

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
                    "mas não teve participantes suficientes."
                ),
                color=COR_FINALIZADO
            )

            embed.set_image(
                url=GIF_SORTEIO
            )

            embed.set_footer(
                text="Família Sant's • Cassino Retrô"
            )

            return await message.edit(
                embed=embed,
                view=self
            )

        vencedores = random.sample(
            self.participantes,
            self.ganhadores
        )

        mencoes = ", ".join(
            v.mention for v in vencedores
        )

        embed = discord.Embed(
            title="🏆 『 VENCEDOR DEFINIDO 』",
            description=(
                "━━━━━━━━━━━━━━━━━━\n"
                "A roleta parou!\n"
                "━━━━━━━━━━━━━━━━━━\n\n"

                f"🎁 **Prêmio:** `{self.premio}`\n\n"

                f"👑 **Vencedor(es):**\n"
                f"{mencoes}\n\n"

                "🎰 Obrigado por participar."
            ),
            color=COR_CUPHEAD
        )

        embed.set_image(
            url=GIF_SORTEIO
        )

        embed.set_footer(
            text="Família Sant's • Cassino Retrô"
        )

        await message.edit(
            embed=embed,
            view=self
        )


class Sorteio(commands.Cog):
    def __init__(
        self,
        bot
    ):

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

        view.mensagem = mensagem

        await asyncio.sleep(
            tempo_segundos
        )

        if not view.finalizado:
            await view.finalizar_sorteio(
                mensagem
            )


async def setup(bot):
    await bot.add_cog(
        Sorteio(bot)
    )