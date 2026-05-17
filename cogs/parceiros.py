import discord
from discord.ext import commands

# ==================================================
# 🎩 TEMA CUPHEAD
# ==================================================

COR_CUPHEAD = 0xC0392B
BANNER_PARCEIROS = "https://i.imgur.com/aINwFAT.png"

PARCEIROS = [
    {
        "nome": "Família Celeste",
        "descricao": "Um salão elevado entre nuvens, onde alianças são firmadas sob holofotes dourados.",
        "emoji": "🌥️",
        "link": "https://discord.gg/TsUKsMgsz"
    },
    {
        "nome": "Instruções Delta",
        "descricao": "Um antigo manual de regras, desafios e contratos assinados à moda clássica.",
        "emoji": "📜",
        "link": "https://discord.gg/W5mQvup4T"
    },
    {
        "nome": "Base de Eventos Delta",
        "descricao": "Um palco de eventos onde cada rodada parece saída de um desenho antigo.",
        "emoji": "🎪",
        "link": "https://discord.gg/ua2mZzBzA5"
    },
    {
        "nome": "BIDEX",
        "descricao": "Uma mesa de apostas onde apenas os mais ousados aceitam o desafio.",
        "emoji": "🔥",
        "link": "https://discord.gg/HGvEQ8mn7b"
    },
    {
        "nome": "Irmandade Roleplay",
        "descricao": "Um teatro vivo de histórias, personagens e grandes interpretações.",
        "emoji": "🎭",
        "link": "https://discord.gg/J3VfQfgqHN"
    },
    {
        "nome": "Família Ghost",
        "descricao": "Um salão assombrado onde pactos aparecem entre sombras e risadas antigas.",
        "emoji": "👻",
        "link": "https://discord.gg/uJhDsRMV4"
    },
    {
        "nome": "Gangue anti Bisonhos",
        "descricao": "Uma gangue de rua com estilo, confusão e energia de desenho clássico.",
        "emoji": "🎩",
        "link": "https://discord.gg/rS9gTbYsV"
    },
    {
        "nome": "BiscoiteX Community",
        "descricao": "Uma confeitaria caótica onde alianças são servidas com diversão e movimento.",
        "emoji": "🍪",
        "link": "https://discord.gg/dRE4QTh6mN"
    },
    {
        "nome": "Konoha Network",
        "descricao": "Uma vila animada onde aventuras e parcerias caminham lado a lado.",
        "emoji": "🍃",
        "link": "https://discord.gg/RYsFkXqCS"
    },
    {
        "nome": "Time Anti Praças",
        "descricao": "Um grupo de combate pronto para entrar em cena quando o show começar.",
        "emoji": "⚔️",
        "link": "https://discord.gg/4yaUuGCuG"
    },
    {
        "nome": "Família Yamato",
        "descricao": "Uma mesa de dados, sorte e alianças firmadas em clima de aventura.",
        "emoji": "🎲",
        "link": "https://discord.gg/Wk4ZHUUy2"
    },
    {
        "nome": "Cidadela da Hayley",
        "descricao": "Uma cidadela acolhedora para quem busca amizade, movimento e diversão.",
        "emoji": "🌸",
        "link": "https://discord.gg/YMGvwm74y"
    },
    {
        "nome": "Polícia Militar",
        "descricao": "A patrulha responsável por manter a ordem quando o caos tenta tomar o palco.",
        "emoji": "🚓",
        "link": "https://discord.gg/Q94PvtNCs"
    }
]


# ==================================================
# 🎟️ SELECT DE PARCEIROS
# ==================================================

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
            placeholder="🎩 Escolha um parceiro no grande palco...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="cuphead_parceiros_select"
        )

    async def callback(self, interaction: discord.Interaction):
        escolhido = self.values[0]
        parceiro = next(p for p in PARCEIROS if p["nome"] == escolhido)

        embed = discord.Embed(
            title=f"{parceiro['emoji']} {parceiro['nome']}",
            description=(
                "🎬 **PARCERIA SELECIONADA!**\n\n"
                "As cortinas se abriram e um novo portal apareceu no palco.\n"
                "Escolha com cuidado, pois cada parceria leva a uma nova aventura.\n\n"
                f"📜 **Descrição:**\n{parceiro['descricao']}\n\n"
                f"🔗 **Entrar no servidor:**\n{parceiro['link']}"
            ),
            color=COR_CUPHEAD
        )

        embed.add_field(
            name="🎪 Tipo",
            value="Servidor Parceiro",
            inline=True
        )

        embed.add_field(
            name="⭐ Status",
            value="Parceria ativa",
            inline=True
        )

        embed.set_footer(text="Cuphead Partners • Família Sant's")

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# ==================================================
# 🎪 VIEW
# ==================================================

class ViewParceiros(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectParceiros())


# ==================================================
# 🎩 COG
# ==================================================

class Parceiros(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="painel_parceiros")
    @commands.has_permissions(administrator=True)
    async def painel_parceiros(self, ctx):

        embed = discord.Embed(
            title="🎩 GRANDE PALCO DOS PARCEIROS",
            description=(
                "**Bem-vindo ao salão das alianças da Família Sant's!**\n\n"
                "Aqui ficam os servidores que caminham junto com a nossa comunidade.\n"
                "Cada parceiro abaixo representa uma nova porta, uma nova aventura "
                "e um novo palco para conhecer pessoas.\n\n"
                "🎟️ Escolha uma parceria no menu abaixo.\n"
                "🎬 As cortinas vão se abrir para o servidor selecionado."
            ),
            color=COR_CUPHEAD
        )

        embed.add_field(
            name="🎪 Como funciona?",
            value=(
                "Selecione um servidor parceiro no menu.\n"
                "O bot enviará o convite de forma privada para você."
            ),
            inline=False
        )

        embed.add_field(
            name="📌 Aviso",
            value=(
                "Respeite as regras dos servidores parceiros.\n"
                "Parcerias representam confiança entre comunidades."
            ),
            inline=False
        )

        embed.set_image(url=BANNER_PARCEIROS)
        embed.set_footer(text="Cuphead Partners • Família Sant's")

        await ctx.send(embed=embed, view=ViewParceiros())

        try:
            await ctx.message.delete()
        except:
            pass


async def setup(bot):
    bot.add_view(ViewParceiros())
    await bot.add_cog(Parceiros(bot))