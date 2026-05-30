import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
from datetime import datetime, timezone
from collections import Counter

# ══════════════════════════════════════════════
#              🎨 CORES DO TEMA
# ══════════════════════════════════════════════
COR_CUPHEAD   = 0xC48A3A
COR_DOURADA   = 0xFFD700
COR_VERDE     = 0x2ECC71
COR_VERMELHO  = 0x8B3A3A
COR_ROXO      = 0x9B59B6


BANNERS = {
    # Aparece no embed principal enquanto o sorteio está ativo
    "ativo":      "https://media.discordapp.net/attachments/961677475191078992/1510111531243933716/RgGXAAAABklEQVQDAEZvdQlgAtWFAAAAAElFTkSuQmCC.png?ex=6a1ba075&is=6a1a4ef5&hm=07e0f157f5e9f534d9e72201ca68dce09a2dcb6f886bc6bc305d89bdde80c8b2&=&format=webp&quality=lossless",

    # Aparece quando o sorteio é encerrado com vencedores
    "vencedor":   "https://media.discordapp.net/attachments/961677475191078992/1510111530731966554/4m1Yc4AAAAGSURBVAMAIhJq0lQ0SxAAAAAASUVORK5CYII.png?ex=6a1ba075&is=6a1a4ef5&hm=e199e8cd1fd4c9d6334564dfc3e9ea68fcd4e2e045d60c3f918fce39b8a47fb1&=&format=webp&quality=lossless",

    # Aparece quando o sorteio é cancelado
    "cancelado":  "https://media.discordapp.net/attachments/961677475191078992/1510111531595989183/8n20PEAAAABklEQVQDAKLuoNzTHmVcAAAAAElFTkSuQmCC.png?ex=6a1ba075&is=6a1a4ef5&hm=7db8a9a2a649bb9dd53af3c23535159f4a826e0f81948a24df9d15ef1c87743a&=&format=webp&quality=lossless",

    # Aparece quando não há participantes suficientes
    "sem_ganho":  "https://media.discordapp.net/attachments/961677475191078992/1510111531969544222/9nqs7uAAAABklEQVQDAKFdrWaYqa4kAAAAAElFTkSuQmCC.png?ex=6a1ba075&is=6a1a4ef5&hm=07331996899d4e43ad5904c402ab2abded31749295fc251403267abcc86c396e&=&format=webp&quality=lossless",

    # Aparece no reroll
    "reroll":     "https://media.discordapp.net/attachments/961677475191078992/1510111532720062645/kudHpAAAAAZJREFUAwBzE3bm4YTgCAAAAABJRU5ErkJggg.png?ex=6a1ba075&is=6a1a4ef5&hm=d6a686124710b250e77b0669a9f75b41e2380f81a164498ed7852809c11a831d&=&format=webp&quality=lossless",
}

CARGOS_BONUS = {
    # 1486411238513836052: 3,   # ⭐ Cargo de Patrocinador da Família Sant's — 3 entradas extras rsrs
    # 1480334522053558465: 1,   # 🚀 Cargo de Booster do Servidor - Toma 2 ai
    # 1111111111111111111: 3,   # 👑 Sem ideia 
    # 2222222222222222222: 1,   # 🎖️ Sem ideia
}

# ══════════════════════════════════════════════
#         🔐 CARGOS ADMINISTRATIVOS
# ══════════════════════════════════════════════
CARGOS_ADMIN_SORTEIO = [
    1492220245996343377,
    1480334545944449024,
    1485706762765074544,
    1483191687927828766,
    1480349452744265759,
    1501356975491907664,
]

FRAMES_ANIMACAO = [
    "🎰 ▓░░░░░░░░░ Sorteando...",
    "🎰 ▓▓▓░░░░░░░ Sorteando...",
    "🎰 ▓▓▓▓▓░░░░░ Sorteando...",
    "🎰 ▓▓▓▓▓▓▓░░░ Quase lá...",
    "🎰 ▓▓▓▓▓▓▓▓▓░ Quase lá...",
    "🎰 ▓▓▓▓▓▓▓▓▓▓ Resultado!",
]

DELAY_FRAME = 0.5



class AdminSorteioView(discord.ui.View):
    def __init__(self, sorteio_view: "SorteioView"):
        super().__init__(timeout=180)
        self.sorteio_view = sorteio_view

    # ── Listar participantes ────────────────────────────────────────
    @discord.ui.button(label="Participantes", emoji="👥", style=discord.ButtonStyle.primary)
    async def ver_participantes(self, interaction: discord.Interaction, button: discord.ui.Button):
        pool = self.sorteio_view.pool_sorteio()
        contagem = Counter(p.id for p in pool)
        unicos = list({p.id: p for p in pool}.values())

        if not unicos:
            texto = "Nenhum participante entrou neste sorteio ainda."
        else:
            linhas = []
            for i, m in enumerate(unicos[:50]):
                entradas = contagem[m.id]
                bonus = entradas - 1
                sufixo = f" `+{bonus} bônus`" if bonus > 0 else ""
                linhas.append(f"`{i + 1}.` {m.mention} — 🎟️ `{entradas}`{sufixo}")
            texto = "\n".join(linhas)

            if len(unicos) > 50:
                texto += f"\n\n*+ `{len(unicos) - 50}` participante(s)...*"

        embed = discord.Embed(
            title="👥 Participantes do Sorteio",
            description=texto,
            color=COR_CUPHEAD,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(
            name="📊 Totais",
            value=(
                f"👤 **Únicos:** `{len(unicos)}`\n"
                f"🎟️ **Entradas totais:** `{len(pool)}`"
            )
        )
        embed.set_footer(text="Família Sant's • Painel Admin")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Estatísticas", emoji="📊", style=discord.ButtonStyle.primary)
    async def estatisticas(self, interaction: discord.Interaction, button: discord.ui.Button):
        sv = self.sorteio_view
        pool = sv.pool_sorteio()
        unicos = len(set(p.id for p in pool))
        contagem = Counter(p.id for p in pool)
        top3 = contagem.most_common(3)

        agora = datetime.now(timezone.utc)
        tempo_restante = max(sv.fim - agora, __import__("datetime").timedelta(0))
        horas, resto = divmod(int(tempo_restante.total_seconds()), 3600)
        minutos = resto // 60

        top_texto = "\n".join(
            f"`{i + 1}.` <@{uid}> — 🎟️ `{qtd}`"
            for i, (uid, qtd) in enumerate(top3)
        ) if top3 else "Nenhum participante ainda."

        embed = discord.Embed(
            title="📊 Estatísticas do Sorteio",
            color=COR_ROXO,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="🎁 Prêmio", value=sv.premio, inline=False)
        embed.add_field(name="👤 Participantes únicos", value=f"`{unicos}`", inline=True)
        embed.add_field(name="🎟️ Entradas totais", value=f"`{len(pool)}`", inline=True)
        embed.add_field(name="👑 Ganhadores", value=f"`{sv.ganhadores}`", inline=True)
        embed.add_field(name="⏳ Tempo restante", value=f"`{horas}h {minutos}m`", inline=True)
        embed.add_field(name="🏆 Top entradas", value=top_texto, inline=False)
        embed.set_footer(text="Família Sant's • Painel Admin")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Reroll ──────────────────────────────────────────────────────
    @discord.ui.button(label="Reroll", emoji="🎲", style=discord.ButtonStyle.secondary)
    async def reroll(self, interaction: discord.Interaction, button: discord.ui.Button):
        sv = self.sorteio_view

        if not sv.finalizado:
            return await interaction.response.send_message(
                "❌ O reroll só pode ser feito após o sorteio ser finalizado.",
                ephemeral=True
            )

        pool = sv.pool_sorteio()
        if len(set(p.id for p in pool)) < sv.ganhadores:
            return await interaction.response.send_message(
                "❌ Não há participantes únicos suficientes para reroll.",
                ephemeral=True
            )

        await interaction.response.defer()

        # Animação de reroll
        msg = await interaction.followup.send("🎲 Rerolando...", ephemeral=False)
        for frame in FRAMES_ANIMACAO:
            await msg.edit(content=frame)
            await asyncio.sleep(DELAY_FRAME)

        vencedores = _sortear_unicos(pool, sv.ganhadores)
        mencoes = ", ".join(v.mention for v in vencedores)

        embed = discord.Embed(
            title="🎲 REROLL • CUPHEAD CASINO",
            description=(
                "A roleta girou novamente e um novo destino foi traçado.\n\n"
                f"🎁 **Prêmio:** {sv.premio}\n"
                f"👑 **Novo(s) vencedor(es):** {mencoes}"
            ),
            color=COR_DOURADA,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_image(url=BANNERS["reroll"])
        embed.set_footer(text="Família Sant's • Cuphead Casino")

        await msg.edit(content=None, embed=embed)

    # ── Finalizar ───────────────────────────────────────────────────
    @discord.ui.button(label="Finalizar", emoji="🏁", style=discord.ButtonStyle.success)
    async def finalizar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        if self.sorteio_view.finalizado:
            return await interaction.followup.send("❌ Este sorteio já foi finalizado.", ephemeral=True)

        await self.sorteio_view.finalizar_sorteio(self.sorteio_view.mensagem)
        await interaction.followup.send("🏁 Sorteio finalizado com sucesso.", ephemeral=True)

    # ── Cancelar ────────────────────────────────────────────────────
    @discord.ui.button(label="Cancelar", emoji="❌", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        if self.sorteio_view.finalizado:
            return await interaction.followup.send("❌ Este sorteio já foi encerrado.", ephemeral=True)

        await self.sorteio_view.cancelar_sorteio(self.sorteio_view.mensagem)
        await interaction.followup.send("❌ Sorteio cancelado com sucesso.", ephemeral=True)



def _sortear_unicos(pool: list[discord.Member], quantidade: int) -> list[discord.Member]:
    """Sorteia membros únicos a partir de uma pool com entradas duplicadas (ponderadas)."""
    vencedores = []
    pool_restante = pool.copy()
    ids_sorteados = set()

    while len(vencedores) < quantidade and pool_restante:
        escolhido = random.choice(pool_restante)
        if escolhido.id not in ids_sorteados:
            vencedores.append(escolhido)
            ids_sorteados.add(escolhido.id)
        # Remove todas as entradas do membro já sorteado
        pool_restante = [p for p in pool_restante if p.id not in ids_sorteados]

    return vencedores


class SorteioView(discord.ui.View):
    def __init__(self, premio, descricao, ganhadores, requisito, fim):
        super().__init__(timeout=None)

        self.premio      = premio
        self.descricao   = descricao
        self.ganhadores  = ganhadores
        self.requisito   = requisito
        self.fim         = fim

        # Armazena apenas membros únicos; a pool ponderada é gerada dinamicamente
        self.participantes: list[discord.Member] = []
        self.finalizado  = False
        self.cancelado   = False
        self.mensagem: discord.Message | None = None
        self.inicio      = datetime.now(timezone.utc)

    # ── Pool ponderada ──────────────────────────────────────────────
    def pool_sorteio(self) -> list[discord.Member]:
        """Retorna uma lista onde cada membro aparece N vezes (entradas totais)."""
        pool = []
        for membro in self.participantes:
            entradas = 1 + sum(
                bonus
                for cargo_id, bonus in CARGOS_BONUS.items()
                if any(c.id == cargo_id for c in membro.roles)
            )
            pool.extend([membro] * entradas)
        return pool

    def entradas_membro(self, membro: discord.Member) -> int:
        return 1 + sum(
            bonus
            for cargo_id, bonus in CARGOS_BONUS.items()
            if any(c.id == cargo_id for c in membro.roles)
        )

    # ── Helpers ─────────────────────────────────────────────────────
    def requisito_texto(self) -> str:
        return "`Nenhum requisito`" if self.requisito is None else self.requisito.mention

    def timestamp_fim(self) -> str:
        ts = int(self.fim.timestamp())
        return f"<t:{ts}:F>\n⏳ <t:{ts}:R>"

    def barra_progresso(self) -> str:
        agora = datetime.now(timezone.utc)
        total = (self.fim - self.inicio).total_seconds()
        decorrido = (agora - self.inicio).total_seconds()
        pct = min(decorrido / total, 1.0) if total > 0 else 0
        cheios = int(pct * 10)
        vazios = 10 - cheios
        return f"[{'█' * cheios}{'░' * vazios}] `{int(pct * 100)}%`"

    def resumo_bonus(self) -> str:
        if not CARGOS_BONUS:
            return "`Nenhum cargo bônus configurado`"
        linhas = [f"<@&{cid}> → `+{b}` entrada(s)" for cid, b in CARGOS_BONUS.items()]
        return "\n".join(linhas)

    # ── Embed principal ─────────────────────────────────────────────
    def criar_embed(self, status: str = "🎬 RODADA EM ANDAMENTO") -> discord.Embed:
        pool = self.pool_sorteio()

        embed = discord.Embed(
            title="🎰 SORTEIO OFICIAL • CUPHEAD CASINO",
            description=(
                "👑 Atençao ao Cargos com Beneficios.\n"
                "<a:Z10_coin:1487490583625728213> <@&1486411238513836052> 3x Entradas\n"
                "<a:D1_PurpleSpinningPixelHeart:1490559444227194902> <@&1480334522053558465> 2x Entrada\n"
    
            ),
            color=COR_CUPHEAD,
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(
            name="🎁 Prêmio",
            value=f"**{self.premio}**",
            inline=False
        )

        embed.add_field(
            name="📜 Descrição",
            value=f"{self.descricao}\n\n🎯 **Requisito:** {self.requisito_texto()}",
            inline=False
        )

        embed.add_field(
            name="👑 Ganhadores",
            value=f"`{self.ganhadores}`",
            inline=True
        )

        embed.add_field(
            name="👤 Participantes",
            value=f"`{len(self.participantes)}`",
            inline=True
        )

        embed.add_field(
            name="🎟️ Entradas totais",
            value=f"`{len(pool)}`",
            inline=True
        )

        embed.add_field(
            name="⭐ Cargos Bônus",
            value=self.resumo_bonus(),
            inline=False
        )

        embed.add_field(
            name="⏳ Encerramento",
            value=self.timestamp_fim(),
            inline=False
        )

        embed.add_field(
            name="📈 Progresso",
            value=self.barra_progresso(),
            inline=False
        )

        embed.add_field(
            name="📌 Status",
            value=f"```{status}```",
            inline=False
        )

        embed.set_image(url=BANNERS["ativo"])
        embed.set_footer(text="Família Sant's • Cuphead Casino • As entradas bônus aumentam suas chances!")
        return embed

    # ── Atualizar embed ─────────────────────────────────────────────
    async def atualizar_embed(self):
        if not self.mensagem:
            return
        try:
            await self.mensagem.edit(embed=self.criar_embed(), view=self)
        except discord.NotFound:
            self.finalizado = True
        except discord.HTTPException:
            pass

    # ── Verificações ────────────────────────────────────────────────
    def tem_requisito(self, membro: discord.Member) -> bool:
        return self.requisito is None or self.requisito in membro.roles

    def tem_admin(self, membro: discord.Member) -> bool:
        return membro.guild_permissions.administrator or any(
            cargo.id in CARGOS_ADMIN_SORTEIO for cargo in membro.roles
        )

    # ════════════════════════════════════════
    #              BOTÕES
    # ════════════════════════════════════════

    @discord.ui.button(label="Entrar no Sorteio", emoji="🎟️", style=discord.ButtonStyle.success, row=0)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.finalizado:
            return await interaction.response.send_message("🎬 Este sorteio já foi encerrado.", ephemeral=True)

        if datetime.now(timezone.utc) >= self.fim:
            self.finalizado = True
            return await interaction.response.send_message("⏳ O prazo deste sorteio já acabou.", ephemeral=True)

        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("❌ Não consegui verificar seus cargos.", ephemeral=True)

        if not self.tem_requisito(interaction.user):
            return await interaction.response.send_message(
                f"❌ Você precisa do cargo {self.requisito.mention} para participar.",
                ephemeral=True
            )

        if interaction.user in self.participantes:
            return await interaction.response.send_message(
                "🎟️ Você já está participando deste sorteio.", ephemeral=True
            )

        self.participantes.append(interaction.user)
        entradas = self.entradas_membro(interaction.user)
        bonus = entradas - 1

        if bonus > 0:
            msg_bonus = f"\n✨ **Bônus de cargo aplicado!** Você tem `{entradas}` entradas no total."
        else:
            msg_bonus = ""

        await interaction.response.send_message(
            f"🎰 Você entrou no sorteio! Boa sorte!{msg_bonus}",
            ephemeral=True
        )
        await self.atualizar_embed()

    @discord.ui.button(label="Sair do Sorteio", emoji="🚪", style=discord.ButtonStyle.secondary, row=0)
    async def sair(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.finalizado:
            return await interaction.response.send_message("🎬 Este sorteio já foi encerrado.", ephemeral=True)

        if interaction.user not in self.participantes:
            return await interaction.response.send_message("🚪 Você não está participando.", ephemeral=True)

        self.participantes.remove(interaction.user)
        await interaction.response.send_message("🚪 Você saiu do sorteio.", ephemeral=True)
        await self.atualizar_embed()

    @discord.ui.button(label="Minhas Entradas", emoji="📋", style=discord.ButtonStyle.primary, row=0)
    async def minhas_entradas(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("❌ Não consegui verificar seus dados.", ephemeral=True)

        esta_participando = interaction.user in self.participantes
        entradas = self.entradas_membro(interaction.user) if esta_participando else 0
        bonus = entradas - 1 if esta_participando else 0
        pool = self.pool_sorteio()
        chance = f"`{(entradas / len(pool) * 100):.1f}%`" if pool else "`0%`"

        cargos_ativos = [
            f"<@&{cid}> (`+{b}` entrada(s))"
            for cid, b in CARGOS_BONUS.items()
            if any(c.id == cid for c in interaction.user.roles)
        ]

        embed = discord.Embed(
            title="📋 Suas Entradas",
            color=COR_CUPHEAD,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="✅ Participando", value="`Sim`" if esta_participando else "`Não`", inline=True)
        embed.add_field(name="🎟️ Entradas", value=f"`{entradas}`", inline=True)
        embed.add_field(name="✨ Bônus", value=f"`+{bonus}`", inline=True)
        embed.add_field(name="📈 Chance estimada", value=chance, inline=True)
        embed.add_field(
            name="⭐ Cargos bônus ativos",
            value="\n".join(cargos_ativos) if cargos_ativos else "`Nenhum`",
            inline=False
        )
        embed.set_footer(text="Família Sant's • Cuphead Casino")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Painel Admin", emoji="⚙️", style=discord.ButtonStyle.danger, row=1)
    async def admin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("❌ Não consegui verificar suas permissões.", ephemeral=True)

        if not self.tem_admin(interaction.user):
            return await interaction.response.send_message("❌ Você não pode acessar este painel.", ephemeral=True)

        await interaction.response.send_message(
            "⚙️ Painel administrativo do sorteio:",
            view=AdminSorteioView(self),
            ephemeral=True
        )

   
    async def _animar_sorteio(self) -> discord.Message | None:
        """Envia mensagem de animação no canal e retorna o objeto da mensagem."""
        if not self.mensagem:
            return None
        try:
            msg = await self.mensagem.channel.send("🎰 Iniciando o sorteio...")
            for frame in FRAMES_ANIMACAO:
                await msg.edit(content=frame)
                await asyncio.sleep(DELAY_FRAME)
            return msg
        except discord.HTTPException:
            return None

    async def cancelar_sorteio(self, message: discord.Message):
        if self.finalizado:
            return

        self.finalizado = True
        self.cancelado = True

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(
            title="❌ SORTEIO CANCELADO",
            description=(
                "A rodada foi encerrada pela equipe antes do prazo.\n\n"
                f"🎁 **Prêmio:** {self.premio}\n"
                f"🎟️ **Participantes:** `{len(self.participantes)}`\n\n"
                "*Fique atento aos próximos sorteios!*"
            ),
            color=COR_VERMELHO,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_image(url=BANNERS["cancelado"])
        embed.set_footer(text="Família Sant's • Sorteio cancelado")

        try:
            await message.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass

    async def finalizar_sorteio(self, message: discord.Message):
        if self.finalizado:
            return

        self.finalizado = True

        for item in self.children:
            item.disabled = True

        pool = self.pool_sorteio()
        unicos = len(set(p.id for p in pool))

        if unicos < self.ganhadores:
            embed = discord.Embed(
                title="🎬 SORTEIO ENCERRADO",
                description=(
                    "A roleta parou, mas não houve participantes suficientes.\n\n"
                    f"🎁 **Prêmio:** {self.premio}\n"
                    f"👥 **Participantes únicos:** `{unicos}`\n"
                    f"👑 **Ganhadores necessários:** `{self.ganhadores}`"
                ),
                color=COR_VERMELHO,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_image(url=BANNERS["sem_ganho"])
            embed.set_footer(text="Família Sant's • Sem vencedores")

            try:
                await message.edit(embed=embed, view=self)
            except discord.HTTPException:
                pass
            return

        # ── Animação ───────────────────────────────────────────────
        msg_anim = await self._animar_sorteio()

        # ── Sorteio ponderado ──────────────────────────────────────
        vencedores = _sortear_unicos(pool, self.ganhadores)
        mencoes = ", ".join(v.mention for v in vencedores)

        # ── Embed de resultado ─────────────────────────────────────
        embed = discord.Embed(
            title="🏆 RESULTADO DO SORTEIO • CUPHEAD CASINO",
            description=(
                "A roleta parou e a sorte escolheu os seus eleitos.\n\n"
                f"🎁 **Prêmio:** {self.premio}\n\n"
                f"👑 **Vencedor(es):**\n{mencoes}\n\n"
                f"🎟️ **Participantes únicos:** `{unicos}`\n"
                f"📊 **Entradas totais:** `{len(pool)}`\n\n"
                "☕ Obrigado a todos que participaram!"
            ),
            color=COR_VERDE,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_image(url=BANNERS["vencedor"])
        embed.set_footer(text="Família Sant's • Cuphead Casino")

        try:
            await message.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass

       
        if msg_anim:
            try:
                await msg_anim.delete()
            except discord.HTTPException:
                pass

        try:
            await message.reply(
                f"🏆 Parabéns {mencoes}! "
                f"{'Você venceu' if self.ganhadores == 1 else 'Vocês venceram'} "
                f"o sorteio de **{self.premio}**! 🎉"
            )
        except discord.HTTPException:
            pass


class Sorteio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="sorteio",
        description="🎰 Cria um sorteio profissional no tema Cuphead Casino."
    )
    @app_commands.describe(
        premio="Prêmio do sorteio",
        descricao="Descrição detalhada do prêmio",
        ganhadores="Quantidade de ganhadores",
        data="Data de encerramento (Ex: 31/05/2026)",
        hora="Hora de encerramento (Ex: 18:00)",
        requisito="Cargo obrigatório para participar (opcional)"
    )
    async def sorteio(
        self,
        interaction: discord.Interaction,
        premio: str,
        descricao: str,
        ganhadores: int,
        data: str,
        hora: str,
        requisito: discord.Role = None
    ):
        # ── Permissão ──────────────────────────────────────────────
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ Apenas administradores podem criar sorteios.", ephemeral=True
            )

        # ── Validação dos ganhadores ───────────────────────────────
        if ganhadores <= 0:
            return await interaction.response.send_message(
                "❌ A quantidade de ganhadores precisa ser maior que 0.", ephemeral=True
            )

        # ── Validação da data/hora ─────────────────────────────────
        try:
            data_hora = datetime.strptime(f"{data} {hora}", "%d/%m/%Y %H:%M")
            data_hora = data_hora.replace(tzinfo=timezone.utc)
        except ValueError:
            return await interaction.response.send_message(
                "❌ Formato inválido.\n\n"
                "📅 **Data:** `31/05/2026`\n"
                "🕒 **Hora:** `18:00`",
                ephemeral=True
            )

        agora = datetime.now(timezone.utc)

        if data_hora <= agora:
            return await interaction.response.send_message(
                "❌ Você não pode criar sorteios no passado.", ephemeral=True
            )

        tempo_segundos = int((data_hora - agora).total_seconds())

        if tempo_segundos > 60 * 60 * 24 * 90:
            return await interaction.response.send_message(
                "❌ O sorteio não pode ultrapassar 90 dias.", ephemeral=True
            )

        # ── Criar sorteio ──────────────────────────────────────────
        view = SorteioView(
            premio=premio,
            descricao=descricao,
            ganhadores=ganhadores,
            requisito=requisito,
            fim=data_hora
        )

        await interaction.response.defer(ephemeral=True)

        mensagem = await interaction.channel.send(embed=view.criar_embed(), view=view)
        view.mensagem = mensagem

        await interaction.followup.send(
            f"🎰 Sorteio **{premio}** criado com sucesso! Encerrará <t:{int(data_hora.timestamp())}:R>.",
            ephemeral=True
        )

        # ── Timer automático ───────────────────────────────────────
        await asyncio.sleep(tempo_segundos)

        if not view.finalizado:
            await view.finalizar_sorteio(mensagem)


async def setup(bot):
    await bot.add_cog(Sorteio(bot))