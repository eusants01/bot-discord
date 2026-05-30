import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

COR_CUPHEAD  = 0xC48A3A
COR_VERDE    = 0x2ECC71
COR_VERMELHO = 0x8B3A3A

BANNER_PAINEL = "https://cdn.discordapp.com/attachments/961677475191078992/1510105651542626445/content.png?ex=6a1b9afb&is=6a1a497b&hm=7d4c589d18aee527f82555d419e7f97baa14b755a7915868833327eb3115fc2a&"

FICHAS = {
    "Sorteios do Cassino": {
        "id":        1481027666722164807,
        "emoji":     "🩸",
        "descricao": "Receba pings dos sorteios especiais.",
    },
    "Jornal do Cassino": {
        "id":        1493477718950674492,
        "emoji":     "📰",
        "descricao": "Novidades e atualizações do servidor.",
    },
    "Eventos da Mesa": {
        "id":        1488280417961378054,
        "emoji":     "🎲",
        "descricao": "Eventos temáticos e rodadas especiais.",
    },
    "Pactos & Parcerias": {
        "id":        1488280627617988659,
        "emoji":     "🤝",
        "descricao": "Alianças e acordos com outros cassinos.",
    },
    "Avisos do Dealer": {
        "id":        1481027884142432420,
        "emoji":     "📢",
        "descricao": "Comunicados oficiais da administração.",
    },
    # "Treinamentos de Feiticeiros": 
    #     "id":        1490898663374065785,
    #     "emoji":     "🛡️",
    #     "descricao": "Sessões de treino e desafios.",
    # },
}



class SelectFichas(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=nome,
                description=dados["descricao"],
                emoji=dados["emoji"],
                value=nome,
            )
            for nome, dados in FICHAS.items()
        ]

        super().__init__(
            placeholder="🎰 Escolha suas fichas de notificação...",
            min_values=1,
            max_values=len(options),
            options=options,
            custom_id="select_fichas_cuphead_v1",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        membro = interaction.user
        if not isinstance(membro, discord.Member):
            return await interaction.followup.send(
                "❌ Não foi possível verificar suas fichas.", ephemeral=True
            )

        adicionados = []
        removidos   = []
        erros       = []

        for nome in self.values:
            dados = FICHAS.get(nome)
            if not dados:
                continue

            cargo = interaction.guild.get_role(dados["id"])
            if cargo is None:
                erros.append(f"{dados['emoji']} **{nome}** — ficha não encontrada no servidor.")
                continue

            try:
                if cargo in membro.roles:
                    await membro.remove_roles(cargo, reason="Painel de fichas Cuphead")
                    removidos.append(f"{dados['emoji']} **{nome}**")
                else:
                    await membro.add_roles(cargo, reason="Painel de fichas Cuphead")
                    adicionados.append(f"{dados['emoji']} **{nome}**")
            except discord.Forbidden:
                erros.append(f"{dados['emoji']} **{nome}** — sem permissão para alterar.")

        linhas = []
        if adicionados:
            linhas.append("**🎟️ Fichas coletadas:**\n" + "\n".join(f"  ✅ {s}" for s in adicionados))
        if removidos:
            linhas.append("**🃏 Fichas devolvidas:**\n" + "\n".join(f"  ↩️ {s}" for s in removidos))
        if erros:
            linhas.append("**☠️ Erros na mesa:**\n" + "\n".join(f"  ⛔ {e}" for e in erros))
        if not linhas:
            linhas.append("Nenhuma alteração foi feita.")

        embed = discord.Embed(
            description="\n\n".join(linhas),
            color=COR_VERDE if not erros else COR_VERMELHO,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Família Sant's • Cuphead Casino")

        await interaction.followup.send(embed=embed, ephemeral=True)


class BotaoMinhasFichas(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Ver minhas fichas",
            emoji="🃏",
            style=discord.ButtonStyle.secondary,
            custom_id="btn_minhas_fichas_cuphead_v1",
        )

    async def callback(self, interaction: discord.Interaction):
        membro = interaction.user
        if not isinstance(membro, discord.Member):
            return await interaction.response.send_message(
                "❌ Não foi possível verificar suas fichas.", ephemeral=True
            )

        ativas   = []
        inativas = []

        for nome, dados in FICHAS.items():
            cargo = interaction.guild.get_role(dados["id"])
            if cargo and cargo in membro.roles:
                ativas.append(f"{dados['emoji']} **{nome}**")
            else:
                inativas.append(f"{dados['emoji']} {nome}")

        embed = discord.Embed(
            title="🃏 Suas Fichas na Mesa",
            color=COR_CUPHEAD,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(
            name=f"✅ Na mão ({len(ativas)})",
            value="\n".join(ativas) if ativas else "*Você não tem fichas na mão.*",
            inline=False
        )
        embed.add_field(
            name=f"⬜ Disponíveis ({len(inativas)})",
            value="\n".join(inativas) if inativas else "*Você pegou todas as fichas!*",
            inline=False
        )
        embed.set_footer(text="Família Sant's • Cuphead Casino")

        await interaction.response.send_message(embed=embed, ephemeral=True)




class ViewNotificacoes(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectFichas())
        self.add_item(BotaoMinhasFichas())

class NotificacoesCuphead(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="painel_notificacoes",
        description="🎰 Envia o painel de fichas de notificação."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_notificacoes(self, interaction: discord.Interaction):
        embed = _criar_embed_painel()
        await interaction.response.send_message(embed=embed, view=ViewNotificacoes())

    @commands.command(name="painel_notificacoes")
    @commands.has_permissions(administrator=True)
    async def painel_notificacoes_prefix(self, ctx: commands.Context):
        embed = _criar_embed_painel()
        await ctx.send(embed=embed, view=ViewNotificacoes())
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

    @painel_notificacoes.error
    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.response.send_message(
            "❌ Apenas administradores podem usar este comando.", ephemeral=True
        )


def _criar_embed_painel() -> discord.Embed:
    lista_fichas = "\n".join(
        f"{d['emoji']} **{nome}** — {d['descricao']}"
        for nome, d in FICHAS.items()
    )

    embed = discord.Embed(
        title="🎰 BEM-VINDO AO CUPHEAD CASINO",
        description=(
            "☕ **A casa sempre tem suas apostas...**\n\n"
            "Escolha quais fichas deseja carregar na manga.\n"
            "Selecione a mesma ficha novamente para devolvê-la.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{lista_fichas}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🃏 *Não aposte mais do que pode perder...*"
        ),
        color=COR_CUPHEAD,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_image(url=BANNER_PAINEL)
    embed.set_footer(text="Família Sant's • Cuphead Casino • A casa agradece sua visita")
    return embed


async def setup(bot):
    await bot.add_cog(NotificacoesCuphead(bot))