import discord
from discord.ext import commands

# ==================================================
# 🎩 CONFIGURAÇÕES — CUPHEAD THEME
# ==================================================

COR_CUPHEAD = 0xB8322A
COR_DOURADO = 0xD6A84F

BANNER_PARCEIROS = "https://cdn.discordapp.com/attachments/961677475191078992/1507537963326902349/content.png?ex=6a1243a3&is=6a10f223&hm=845cc97dfde1435e7a69459d7da66f5ba0f90f37b5d1cd8bf11a58316fc7315e&"
THUMBNAIL_CUPHEAD = "https://cdn.discordapp.com/attachments/961677475191078992/1507538793564213508/content.png?ex=6a124469&is=6a10f2e9&hm=b88813ac57f1c9df96a115a083c11e7dd4193bae939ace8077750411fa32dc90&"

# ==================================================
# 🎪 LISTA DE PARCEIROS
# ==================================================

PARCEIROS = [

    {
        "nome": "Família Celeste",
        "emoji": "🌥️",
        "categoria": "Comunidade",
        "status": "⭐ Verificado",
        "link": "https://discord.gg/TsUKsMgsz",
        "banner": None,
        "descricao_curta": "Comunidade parceira oficial da Família Sant's.",
        "divulgacao": """
🌥️ **FAMÍLIA CELESTE**

Um salão elevado entre nuvens, onde alianças são firmadas sob holofotes dourados.

🎪 Comunidade ativa  
🎮 Diversão e interação  
🎁 Eventos e novidades  
⭐ Parceria oficial da Família Sant's

Venha conhecer esse grande palco parceiro!
"""
    },

    {
        "nome": "Base de Eventos Delta",
        "emoji": "🎪",
        "categoria": "Eventos",
        "status": "⭐ Verificado",
        "link": "https://discord.gg/ua2mZzBzA5",
        "banner": None,
        "descricao_curta": "Palco de eventos e diversão.",
        "divulgacao": """
🎪 **BASE DE EVENTOS DELTA**

Um palco de eventos onde cada rodada parece saída de um desenho antigo.

🎁 Sorteios  
🏆 Competições  
🎮 Eventos especiais  
🎬 Diversão garantida

As cortinas estão abertas. Venha participar!
"""
    },

    {
        "nome": "Irmandade Roleplay",
        "emoji": "🎭",
        "categoria": "Roleplay",
        "status": "⭐ Verificado",
        "link": "https://discord.gg/J3VfQfgqHN",
        "banner": None,
        "descricao_curta": "Servidor focado em histórias e interpretações.",
        "divulgacao": """
🎭 **IRMANDADE ROLEPLAY**

Um teatro vivo de histórias, personagens e grandes interpretações.

🎬 Roleplay  
📖 Histórias  
🎭 Personagens  
🎩 Comunidade criativa

Entre no palco e crie sua própria aventura!
"""
    },


    {
        "nome": "Gangue anti Bisonhos",
        "emoji": "🎩",
        "categoria": "Comunidade",
        "status": "⭐ Verificado",
        "link": "https://discord.gg/rS9gTbYsV",
        "banner": None,
        "descricao_curta": "Gangue com energia cartoon clássica.",
        "divulgacao": """
🎩 **GANGUE ANTI BISONHOS**

Uma gangue de rua com estilo, confusão e energia de desenho clássico.

🎲 Resenha  
🎮 Jogos  
🔥 Movimento  
🎪 Parceria no grande palco

Entre e faça parte dessa bagunça animada!
"""
    },

    {
        "nome": "BiscoiteX Community",
        "emoji": "🍪",
        "categoria": "Comunidade",
        "status": "⭐ Verificado",
        "link": "https://discord.gg/dRE4QTh6mN",
        "banner": None,
        "descricao_curta": "Comunidade divertida e movimentada.",
        "divulgacao": """
🍪 **BISCOITEX COMMUNITY**

Uma confeitaria caótica onde alianças são servidas com diversão e movimento.

🍪 Comunidade acolhedora  
🎁 Sorteios  
🎮 Jogos  
🎪 Eventos

Pegue seu ingresso e venha conhecer!
"""
    
    },

    {
        "nome": "Time Anti Praças",
        "emoji": "⚔️",
        "categoria": "Equipe",
        "status": "⭐ Verificado",
        "link": "https://discord.gg/4yaUuGCuG",
        "banner": None,
        "descricao_curta": "Grupo preparado para ação.",
        "divulgacao": """
⚔️ **TIME ANTI PRAÇAS**

Um grupo de combate pronto para entrar em cena quando o show começar.

⚔️ Equipe ativa  
🎮 Jogos  
🔥 Movimento  
🎪 Parceria oficial

O palco está pronto para a próxima rodada!
"""
    },

    {
        "nome": "Love Empire",
        "emoji": "🏵️",
        "categoria": "Comunidade",
        "status": "⭐ Verificado",
        "link": "https://discord.gg/TBj4xjXanG",
        "banner": None,
        "descricao_curta": "Servidor de aventura e diversão.",
        "divulgacao": """
# ᘏ﹒⌗ [Love Empire](https://discord.gg/TBj4xjXanG)

┈ ┈ ┈ ┈ ┈ ᶻz -┈ ┈ ┈ ┈ ┈

>  ꖛ🗣️: Você procura uma comunidade ativa e acolhedora? te apresento a Love empire!! 

>  ꖛ📢: Somos uma comunidade bastante ativa, com vários sorteios diários, eventos, brincadeiras várias outras coisas! venha fazer parte da nossa família ♡.

┈ ┈ ┈ ┈ ┈ ᶻz -┈ ┈ ┈ ┈ ┈

> # ꖛ 📬: ***Aqui nós temos :***

> **「👋」 ・`Chat de apresentαções ;`**
> **「💬」 ・`Chat  interativo ;`**
> **「💼」 ・`Vagas Stαff ;`**
> **「💎」 ・`Beneficíos Vip ;`**
> **「🚀」 ・`Benefícios Boost ;`**
> **「🎊」 ・`Sorteios ;`**
> **「🎶」 ・`Bots de músicas ;`**
> **「🎮」 ・`Bots de minigames.`**

┈ ┈ ┈ ┈ ┈ ᶻz -┈ ┈ ┈ ┈ ┈

"""
    },

    {
        "nome": "Cidadela da Hayley",
        "emoji": "🌸",
        "categoria": "Comunidade",
        "status": "⭐ Verificado",
        "link": "https://discord.gg/YMGvwm74y",
        "banner": "https://i.imgur.com/o4sd5kF.png",
        "descricao_curta": "Comunidade acolhedora e divertida.",
        "divulgacao": """
🌸 **CIDADELA DA HAYLEY**

Uma cidadela acolhedora para quem busca amizade, movimento e diversão.

🌸 Comunidade amigável  
🎮 Jogos  
🎪 Interações  
⭐ Parceria oficial

Entre e conheça essa cidadela parceira!
"""
    },

    {
        "nome": "Polícia Militar",
        "emoji": "🚓",
        "categoria": "Organização",
        "status": "⭐ Verificado",
        "link": "https://discord.gg/Q94PvtNCs",
        "banner": None,
        "descricao_curta": "Servidor focado em ordem e organização.",
        "divulgacao": """
🚓 **POLÍCIA MILITAR**

A patrulha responsável por manter a ordem quando o caos tenta tomar o palco.

🚓 Organização  
📌 Comunidade  
🎮 Atividade  
⭐ Parceria oficial

A sirene tocou. O convite está aberto!
"""
    },

    {
        "nome": "Yakuza Community",
        "emoji": "🎌",
        "categoria": "Comunidade",
        "status": "⭐ Verificado",
        "link": "https://discord.gg/yCx3BFW4R",
        "banner": None,
        "descricao_curta": "Servidor de jogos, eventos e amizades.",
        "divulgacao": """
🎌 **YAKUZA COMMUNITY**

> - ╭╴**SOBRE NÓS**
> - `✅` Servidor de jogos ativo
> - `🚀` Sorteios frequentes
> - `📈` Eventos para a comunidade
> - `👥` Espaço para fazer amizades
> - `🔥` Parcerias automáticas
> - `⭐` Mais alcance para servidores

> __INFORMAÇÕES IMPORTANTES__
> - `📌` Staff aberta
> - `💎` Regras organizadas
> - `🌐` Comunidade ativa
> - `⚙️` Jogos e eventos

> __SERVIÇOS__
> - `🛒` Produtos VIP
> - `🎮` Boost
> - `💻` Benefícios exclusivos

✨ Uma comunidade feita para jogar e se divertir.
"""
    }

]

# ==================================================
# 🔧 FUNÇÕES AUXILIARES
# ==================================================

def cortar_texto(texto, limite=95):
    if len(texto) <= limite:
        return texto

    return texto[:limite - 3] + "..."


def buscar_parceiro(nome):
    return next((p for p in PARCEIROS if p["nome"] == nome), None)

# ==================================================
# 🔗 BOTÃO DO SERVIDOR
# ==================================================

class ViewParceiro(discord.ui.View):
    def __init__(self, parceiro):
        super().__init__(timeout=180)

        self.add_item(
            discord.ui.Button(
                label="Entrar no Servidor",
                emoji="🔗",
                style=discord.ButtonStyle.link,
                url=parceiro["link"]
            )
        )

# ==================================================
# 🎟️ SELECT MENU
# ==================================================

class SelectParceiros(discord.ui.Select):
    def __init__(self):

        options = [
            discord.SelectOption(
                label=parceiro["nome"],
                description=cortar_texto(parceiro["descricao_curta"]),
                emoji=parceiro["emoji"],
                value=parceiro["nome"]
            )

            for parceiro in PARCEIROS[:25]
        ]

        super().__init__(
            placeholder="🎩 Escolha um parceiro no grande teatro...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="cuphead_select_parceiros"
        )

    async def callback(self, interaction: discord.Interaction):

        parceiro = buscar_parceiro(self.values[0])

        if not parceiro:
            await interaction.response.send_message(
                "❌ Parceiro não encontrado.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{parceiro['emoji']} {parceiro['nome']}",
            description=(
                "🎬 **AS CORTINAS SE ABRIRAM!**\n\n"
                "Um novo servidor parceiro apareceu no palco da Família Sant's.\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "📜 DIVULGAÇÃO OFICIAL\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                f"{parceiro['divulgacao']}"
            ),
            color=COR_CUPHEAD
        )

        embed.add_field(
            name="🎪 Categoria",
            value=parceiro["categoria"],
            inline=True
        )

        embed.add_field(
            name="⭐ Status",
            value=parceiro["status"],
            inline=True
        )

        embed.add_field(
            name="🎩 Sistema",
            value="Parceria Oficial",
            inline=True
        )

        embed.add_field(
            name="🔗 Convite",
            value=f"[Clique aqui para entrar]({parceiro['link']})",
            inline=False
        )

        if parceiro["banner"]:
            embed.set_image(url=parceiro["banner"])

        embed.set_thumbnail(url=THUMBNAIL_CUPHEAD)

        embed.set_footer(
            text="Cuphead Partners • Família Sant's"
        )

        await interaction.response.send_message(
            embed=embed,
            view=ViewParceiro(parceiro),
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
            title="🎩 GRANDE TEATRO DOS PARCEIROS",
            description=(
                "🎬 **Bem-vindo ao grande palco das alianças da Família Sant's!**\n\n"
                "Aqui ficam os servidores parceiros oficiais da comunidade.\n"
                "Cada parceria representa uma nova aventura.\n\n"

                "━━━━━━━━━━━━━━━━━━\n"
                "🎪 COMO FUNCIONA?\n"
                "━━━━━━━━━━━━━━━━━━\n\n"

                "🎟️ Escolha um parceiro abaixo.\n"
                "📜 Veja a divulgação completa.\n"
                "🔗 Receba o convite privado.\n\n"

                "━━━━━━━━━━━━━━━━━━\n"
                "📌 AVISO\n"
                "━━━━━━━━━━━━━━━━━━\n\n"

                "Respeite todos os servidores parceiros.\n"
                "Parcerias representam confiança entre comunidades.\n\n"

                "☕ Pegue seu ingresso e aproveite o espetáculo!"
            ),
            color=COR_CUPHEAD
        )

        embed.add_field(
            name="⭐ Parceiros Ativos",
            value=f"`{len(PARCEIROS)}` Servidores",
            inline=True
        )

        embed.add_field(
            name="🎩 Tema",
            value="Cuphead Cartoon",
            inline=True
        )

        embed.add_field(
            name="🎬 Sistema",
            value="Divulgação Privada",
            inline=True
        )

        embed.set_image(url=BANNER_PARCEIROS)

        embed.set_footer(
            text="Cuphead Partners • Família Sant's"
        )

        await ctx.send(
            embed=embed,
            view=ViewParceiros()
        )

        try:
            await ctx.message.delete()

        except:
            pass

# ==================================================
# 🔌 SETUP
# ==================================================

async def setup(bot):

    bot.add_view(ViewParceiros())

    await bot.add_cog(Parceiros(bot))