import discord
from discord.ext import commands
from discord import app_commands

GUILD_ID = 1480334256763961465  # coloque aqui o ID do seu servidor

PARCEIROS = [
    {
        "nome": "Família Celeste",
        "descricao": "Parceiro oficial",
        "emoji": "🌥️",
        "link": "https://discord.gg/TsUKsMgsz"
    },
    {
        "nome": "Time Anti Praças",
        "descricao": "Comunidade parceira",
        "emoji": "⚔️",
        "link": "https://discord.gg/4yaUuGCuG"
    },
    {
        "nome": "Família Shelby",
        "descricao": "Comunidade parceira",
        "emoji": "🐦‍⬛",
        "link": "https://discord.gg/5kd5mpyt"
    },
    {
        "nome": "Polícia Militar",
        "descricao": "Comunidade parceira",
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
            placeholder="Selecione um servidor parceiro...",
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
                f"{parceiro['descricao']}\n\n"
                f"🔗 **Link:** {parceiro['link']}"
            ),
            color=discord.Color.purple()
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

    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(name="parceiros", description="Ver servidores parceiros")
    async def parceiros(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤝 SERVIDORES PARCEIROS",
            description="Escolha um servidor parceiro abaixo.",
            color=discord.Color.purple()
        )

        embed.set_image(url="LINK_DO_SEU_BANNER_AQUI")

        await interaction.response.send_message(
            embed=embed,
            view=ViewParceiros()
        )


async def setup(bot):
    await bot.add_cog(Parceiros(bot))