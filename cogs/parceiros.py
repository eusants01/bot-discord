import discord
from discord.ext import commands

COR_ROXA_JUJUTSU = 0x7B2CFF

PARCEIROS = [
    {
        "nome": "Família Celeste",
        "descricao": "Aliança reconhecida dentro do domínio.",
        "emoji": "🌥️",
        "link": "https://discord.gg/TsUKsMgsz"
    },
    {
        "nome": "Time Anti Praças",
        "descricao": "Pacto firmado sob energia amaldiçoada.",
        "emoji": "⚔️",
        "link": "https://discord.gg/4yaUuGCuG"
    },
    {
        "nome": "Família Shelby",
        "descricao": "Aliados marcados pelo selo da Família Sant's.",
        "emoji": "🐦‍⬛",
        "link": "https://discord.gg/5kd5mpyt"
    },
    {
        "nome": "Polícia Militar",
        "descricao": "Ordem aliada dentro deste território.",
        "emoji": "🚓",
        "link": "https://discord.gg/8HzSqvJju"
    }
]


class SelectParceiros(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=p["nome"],
                description=p["descricao"],
                emoji=p["emoji"]
            )
            for p in PARCEIROS
        ]

        super().__init__(
            placeholder="Escolha uma aliança dentro do domínio...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        escolhido = self.values[0]
        parceiro = next(p for p in PARCEIROS if p["nome"] == escolhido)

        embed = discord.Embed(
            title=f"{parceiro['emoji']} {parceiro['nome']}",
            description=(
                "☯️ **Aliança invocada com sucesso.**\n\n"
                f"**Descrição:** {parceiro['descricao']}\n\n"
                f"🔗 **Portal do servidor:**\n{parceiro['link']}"
            ),
            color=COR_ROXA_JUJUTSU
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


class ViewParceiros(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectParceiros())


class Parceiros(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="painel_parceiros")
    @commands.has_permissions(administrator=True)
    async def painel_parceiros(self, ctx):
        embed = discord.Embed(
            title="⛩️ DOMÍNIO DOS PARCEIROS",
            description=(
                "A energia amaldiçoada revela as alianças oficiais da **Família Sant's**.\n\n"
                "Escolha abaixo qual portal deseja acessar."
            ),
            color=COR_ROXA_JUJUTSU
        )

        embed.set_image(url="https://i.imgur.com/aINwFAT.png")
        embed.set_footer(text="領域展開 • Escolha seu destino")

        await ctx.send(embed=embed, view=ViewParceiros())

        # apaga o comando pra ninguém ver
        await ctx.message.delete()


async def setup(bot):
    await bot.add_cog(Parceiros(bot))