import discord
from discord.ext import commands

COR_ROXA_JUJUTSU = 0x6A00FF

# 🔴 IDS DOS CARGOS
CARGOS_NOTIFICACAO = {
    "🩸 Sorteios Amaldiçoados": 1481027666722164807,
    "📰 Jornal Jujutsu": 1493477718950674492,
    "🎁 Eventos de Domínio": 1488280417961378054,
    "🤝 Pactos / Parcerias": 1488280627617988659,
    "📢 Avisos da Barreira": 1481027884142432420,
    "🛡️ Treinamentos de Feiticeiros": 1490898663374065785,
}


# 🔘 BOTÃO
class BotaoCargo(discord.ui.Button):
    def __init__(self, nome_cargo, cargo_id):
        super().__init__(
            label=nome_cargo,
            style=discord.ButtonStyle.danger,  # 🔥 estilo Sukuna (vermelho)
            custom_id=f"jujutsu_cargo_{cargo_id}"
        )
        self.cargo_id = cargo_id

    async def callback(self, interaction: discord.Interaction):
        cargo = interaction.guild.get_role(self.cargo_id)

        if cargo is None:
            await interaction.response.send_message(
                "❌ A invocação falhou... selo inexistente.",
                ephemeral=True
            )
            return

        membro = interaction.user

        if cargo in membro.roles:
            await membro.remove_roles(cargo)
            await interaction.response.send_message(
                f"🩸 A energia amaldiçoada foi removida...\nVocê perdeu o selo **{cargo.name}**.",
                ephemeral=True
            )
        else:
            await membro.add_roles(cargo)
            await interaction.response.send_message(
                f"🌀 A energia flui em você...\nSelo **{cargo.name}** concedido.",
                ephemeral=True
            )


# 🧿 VIEW
class ViewCargosJujutsu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        for nome, cargo_id in CARGOS_NOTIFICACAO.items():
            self.add_item(BotaoCargo(nome, cargo_id))


# 🏯 COG
class NotificacoesJujutsu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="painel_notificacoes")
    @commands.has_permissions(administrator=True)
    async def painel_notificacoes(self, ctx):
        embed = discord.Embed(
            title="🌀 領域展開 — SISTEMA DE SELAGEM",
            description=(
                "**O domínio foi ativado.**\n\n"
                "Escolha quais selos deseja carregar.\n\n"
                "🔮 Cada selo libera um fluxo de energia amaldiçoada.\n"
                "☠️ Clique novamente para remover.\n\n"
                "⚠️ Alguns poderes cobram um preço..."
            ),
            color=COR_ROXA_JUJUTSU
        )

        # 🔥 TROQUE ESSE LINK PELA SUA IMAGEM
        embed.set_image(
            url="https://i.imgur.com/GyCDbdH.png"
        )

        embed.set_footer(text="Ryomen Sukuna • Família Sant's")

        await ctx.send(embed=embed, view=ViewCargosJujutsu())

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        except discord.NotFound:
            pass


async def setup(bot):
    await bot.add_cog(NotificacoesJujutsu(bot))