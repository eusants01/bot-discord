import discord
from discord.ext import commands

COR_ROXA_JUJUTSU = 0x7B2CFF

PARCEIROS = [
    {
        "nome": "Família Celeste",
        "descricao": "Uma aliança elevada, protegida pelas nuvens do domínio.",
        "emoji": "🌥️",
        "link": "https://discord.gg/TsUKsMgsz"
    },
    {
        "nome": "Instruções Delta",
        "descricao": "Um pacto estratégico selado por energia amaldiçoada.",
        "emoji": "📜",
        "link": "https://discord.gg/4yaUuGCuG"
    },
    {
        "nome": "Base de Eventos Delta",
        "descricao": "Território onde desafios e rituais são iniciados.",
        "emoji": "🏯",
        "link": "https://discord.gg/4yaUuGCuG"
    },
    {
        "nome": "Konoha Network",
        "descricao": "Uma vila aliada conectada por antigos selos.",
        "emoji": "🍃",
        "link": "https://discord.gg/4yaUuGCuG"
    },
    {
        "nome": "Time Anti Praças",
        "descricao": "Guerreiros marcados por um juramento sombrio.",
        "emoji": "⚔️",
        "link": "https://discord.gg/4yaUuGCuG"
    },
    {
        "nome": "Família Shelby",
        "descricao": "Aliados envoltos por sombras e lealdade.",
        "emoji": "🐦‍⬛",
        "link": "https://discord.gg/5kd5mpyt"
    },
    {
        "nome": "Polícia Militar",
        "descricao": "A ordem que vigia os limites deste território.",
        "emoji": "🚓",
        "link": "https://discord.gg/8HzSqvJju"
    }
]


class SelectParceiros(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=p["nome"],
                description=p["descricao"][:100],
                emoji=p["emoji"]
            )
            for p in PARCEIROS
        ]

        super().__init__(
            placeholder="⛩️ Escolha uma aliança selada no domínio...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="select_parceiros_jujutsu"
        )

    async def callback(self, interaction: discord.Interaction):
        escolhido = self.values[0]
        parceiro = next(p for p in PARCEIROS if p["nome"] == escolhido)

        embed = discord.Embed(
            title=f"{parceiro['emoji']} {parceiro['nome']}",
            description=(
                "☯️ **ALIANÇA INVOCADA COM SUCESSO**\n\n"
                "Uma conexão foi aberta dentro do domínio da **Família Sant's**.\n\n"
                f"📖 **Registro da Aliança:**\n"
                f"{parceiro['descricao']}\n\n"
                f"🔗 **Portal Amaldiçoado:**\n"
                f"{parceiro['link']}"
            ),
            color=COR_ROXA_JUJUTSU
        )

        embed.set_footer(text="領域展開 • Família Sant's")

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
            title="⛩️ 領域展開 — DOMÍNIO DOS PARCEIROS",
            description=(
                "A barreira foi erguida.\n"
                "Dentro deste território, apenas alianças reconhecidas pela "
                "**Família Sant's** podem ser invocadas.\n\n"
                "☯️ **Selecione abaixo um pacto oficial** e abra o portal "
                "para o servidor aliado."
            ),
            color=COR_ROXA_JUJUTSU
        )

        embed.set_image(url="https://i.imgur.com/aINwFAT.png")
        embed.set_footer(text="Energia amaldiçoada detectada • Família Sant's")

        await ctx.send(embed=embed, view=ViewParceiros())

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass


async def setup(bot):
    await bot.add_cog(Parceiros(bot))