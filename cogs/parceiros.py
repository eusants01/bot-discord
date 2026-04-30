import discord
from discord.ext import commands

COR_ROXA_JUJUTSU = 0x6A00FF

PARCEIROS = [
    {
        "nome": "Família Celeste",
        "descricao": "Entidade que observa o domínio dos céus, acima das maldições.",
        "emoji": "🌥️",
        "link": "https://discord.gg/TsUKsMgsz"
    },
    {
        "nome": "Instruções Delta",
        "descricao": "Ordem estratégica baseada em selos e controle absoluto.",
        "emoji": "📜",
        "link": "https://discord.gg/W5mQvup4T"
    },
    {
        "nome": "Base de Eventos Delta",
        "descricao": "Campo onde rituais e confrontos são executados.",
        "emoji": "🏯",
        "link": "https://discord.gg/ua2mZzBzA5"
    },
    {
        "nome": "BIDEX",
        "descricao": "Zona instável onde apenas os mais fortes resistem.",
        "emoji": "🔥",
        "link": "https://discord.gg/HGvEQ8mn7b"
    },
    {
        "nome": "Konoha Network",
        "descricao": "Uma vila conectada por contratos antigos e energia espiritual.",
        "emoji": "🍃",
        "link": "https://discord.gg/RYsFkXqCS"
    },
    {
        "nome": "Time Anti Praças",
        "descricao": "Combatentes ligados por um juramento sombrio.",
        "emoji": "⚔️",
        "link": "https://discord.gg/4yaUuGCuG"
    },
    {
        "nome": "Família Shelby",
        "descricao": "Aliança envolta em estratégia e sombras.",
        "emoji": "🐦‍⬛",
        "link": "https://discord.gg/5kd5mpyt"
    },
    {
        "nome": "Polícia Militar",
        "descricao": "Força que mantém a ordem dentro do território.",
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
                "🔮 **PACTO ESTABELECIDO**\n\n"
                "A energia amaldiçoada respondeu ao seu chamado...\n\n"
                f"📖 **Registro Espiritual:**\n{parceiro['descricao']}\n\n"
                f"🌀 **Abrir Portal:**\n{parceiro['link']}"
            ),
            color=COR_ROXA_JUJUTSU
        )

        embed.add_field(
            name="⚡ Classe de Energia",
            value="Classe Especial",
            inline=True
        )

        embed.add_field(
            name="☠️ Nível de Ameaça",
            value="Alto",
            inline=True
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
            title="🌀 領域展開 — EXPANSÃO DE DOMÍNIO",
            description=(
                "**O domínio foi ativado.**\n\n"
                "A realidade foi distorcida...\n"
                "Apenas alianças reconhecidas podem ser acessadas.\n\n"
                "🔮 Cada escolha abrirá um portal.\n"
                "⚠️ Nem todos retornam do outro lado."
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
    await bot.add_cog(Parceiros(bot))