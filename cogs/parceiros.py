import discord
from discord.ext import commands

# 🟣 Energia Amaldiçoada
COR_ROXA_JUJUTSU = 0x6A00FF

# 🌀 REGISTRO DE PACTOS
PARCEIROS = [
    {
        "nome": "Família Celeste",
        "descricao": "Entidade superior que observa o domínio dos céus, além da compreensão humana.",
        "emoji": "🌥️",
        "link": "https://discord.gg/TsUKsMgsz"
    },
    {
        "nome": "Instruções Delta",
        "descricao": "Ordem selada por técnicas proibidas e controle absoluto do campo de batalha.",
        "emoji": "📜",
        "link": "https://discord.gg/W5mQvup4T"
    },
    {
        "nome": "Base de Eventos Delta",
        "descricao": "Território onde rituais e confrontos são executados sob regras desconhecidas.",
        "emoji": "🏯",
        "link": "https://discord.gg/ua2mZzBzA5"
    },
    {
        "nome": "BIDEX",
        "descricao": "Zona caótica onde apenas feiticeiros de elite sobrevivem.",
        "emoji": "🔥",
        "link": "https://discord.gg/HGvEQ8mn7b"
    },
    {
        "nome": "Irmandade Roleplay",
        "descricao": "Grupo envolto em ilusões e narrativas moldadas pela energia espiritual.",
        "emoji": "🎪",
        "link": "https://discord.gg/J3VfQfgqHN"
    },
    {
        "nome": "Família Ghost",
        "descricao": "Dimensão das maldições.",
        "emoji": "👻",
        "link": "https://discord.gg/uJhDsRMV4"
    },
    {
        "nome": "Gangue anti Bisonhos",
        "descricao": "Dimensão onde maldições caminham livremente entre os vivos.",
        "emoji": "🎩",
        "link": "https://discord.gg/rS9gTbYsV"
    },
    {
        "nome": "BiscoiteX Community",
        "descricao": "Campo instável onde alianças são testadas e quebradas.",
        "emoji": "🔥",
        "link": "https://discord.gg/dRE4QTh6mN"
    },
    {
        "nome": "Konoha Network",
        "descricao": "Uma vila conectada por contratos antigos e energia espiritual ancestral.",
        "emoji": "🍃",
        "link": "https://discord.gg/RYsFkXqCS"
    },
    {
        "nome": "Time Anti Praças",
        "descricao": "Combatentes ligados por um juramento sombrio e inquebrável.",
        "emoji": "⚔️",
        "link": "https://discord.gg/4yaUuGCuG"
    },
    {
        "nome": "Cidadela da Hayley",
        "descricao": "Entre agora e esteja conosco nessa aventura",
        "emoji": "🌸",
        "link": "https://discord.gg/YMGvwm74y"
    },
    {
        "nome": "Polícia Militar",
        "descricao": "Força que mantém a ordem dentro do território controlado.",
        "emoji": "🚓",
        "link": "https://discord.gg/Q94PvtNCs"
    }
]


# 🌀 SELECT - INVOCAR PACTO
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
            placeholder="🌀 Escolha um pacto dentro da Expansão de Domínio...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="jujutsu_parceiros_select"
        )

    async def callback(self, interaction: discord.Interaction):
        escolhido = self.values[0]
        parceiro = next(p for p in PARCEIROS if p["nome"] == escolhido)

        embed = discord.Embed(
            title=f"{parceiro['emoji']} {parceiro['nome']}",
            description=(
                "🌀 **PACTO INVOCADO**\n\n"
                "A barreira foi rompida...\n"
                "Sua energia amaldiçoada respondeu ao chamado.\n\n"
                f"📖 **Registro Espiritual:**\n{parceiro['descricao']}\n\n"
                f"🔗 **Abrir Portal:**\n{parceiro['link']}"
            ),
            color=COR_ROXA_JUJUTSU
        )

        embed.add_field(
            name="⚡ Classificação",
            value="Classe Especial",
            inline=True
        )

        embed.add_field(
            name="☠️ Risco Espiritual",
            value="Extremo",
            inline=True
        )

        embed.set_footer(text="領域展開 • Família Sant's")

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# 🌀 VIEW
class ViewParceiros(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectParceiros())


# 🌀 COG
class Parceiros(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="painel_parceiros")
    @commands.has_permissions(administrator=True)
    async def painel_parceiros(self, ctx):

        embed = discord.Embed(
            title="🌀 領域展開 — EXPANSÃO DE DOMÍNIO",
            description=(
                "**A realidade foi distorcida.**\n\n"
                "Você entrou em um território onde regras não existem.\n"
                "Apenas aqueles com energia suficiente podem formar pactos.\n\n"
                "🔮 Cada escolha abre um portal.\n"
                "☠️ Nem todos sobrevivem ao outro lado."
            ),
            color=COR_ROXA_JUJUTSU
        )

        embed.add_field(
            name="☯️ Sistema de Pactos",
            value="Selecione abaixo e invoque uma aliança ativa.",
            inline=False
        )

        embed.set_image(url="https://i.imgur.com/aINwFAT.png")
        embed.set_footer(text="Energia amaldiçoada detectada • Família Sant's")

        await ctx.send(embed=embed, view=ViewParceiros())

        try:
            await ctx.message.delete()
        except:
            pass


async def setup(bot):
    bot.add_view(ViewParceiros())
    await bot.add_cog(Parceiros(bot))