
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

COR_ATIVA = 0x6EC6FF       
COR_ENCERRADA = 0x2B2F77   
COR_EMPATE = 0x9B5DE5     

EMOJI_OPCOES = ["❄️", "🐺", "🌌", "⚔️", "✨", "🌙", "🔥", "💎", "🌊", "⚡"]
EMOJI_TROFEU = "🏆"
BARRA_CHEIA = "▰"
BARRA_VAZIA = "▱"
LARGURA_BARRA = 12

RODAPE_ATIVA = "❄️ FrostNova · vote clicando nos botões abaixo"
RODAPE_ENCERRADA = "🌌 FrostNova · enquete encerrada"


def _barra(pct: float) -> str:
    preenchido = round((pct / 100) * LARGURA_BARRA)
    return BARRA_CHEIA * preenchido + BARRA_VAZIA * (LARGURA_BARRA - preenchido)


def _montar_embed(
    pergunta: str,
    opcoes: list[str],
    votos: dict[str, list[int]],
    *,
    autor: discord.abc.User | None,
    expira_em: datetime,
    multiplas: bool,
    anonima: bool,
    encerrada: bool = False,
) -> discord.Embed:
    total = sum(len(v) for v in votos.values()) or 0

    embed = discord.Embed(
        title=f"❄️ {pergunta}",
        color=COR_ENCERRADA if encerrada else COR_ATIVA,
    )

    maior = max((len(v) for v in votos.values()), default=0)
    vencedores_idx = {i for i, v in votos.items() if len(v) == maior} if encerrada and maior > 0 else set()

    linhas = []
    for i, opcao in enumerate(opcoes):
        qtd = len(votos.get(str(i), []))
        pct = (qtd / total * 100) if total else 0
        emoji = EMOJI_OPCOES[i % len(EMOJI_OPCOES)]
        coroa = f" {EMOJI_TROFEU}" if str(i) in vencedores_idx else ""
        linhas.append(
            f"{emoji} **{opcao}**{coroa}\n`{_barra(pct)}` {pct:.0f}% ({qtd} voto{'s' if qtd != 1 else ''})"
        )

    embed.description = "\n\n".join(linhas)

    tipo = "Múltipla escolha" if multiplas else "Escolha única"
    sigilo = "Votos anônimos" if anonima else "Votos identificados"
    embed.add_field(name="Tipo", value=f"{tipo} · {sigilo}", inline=False)

    if encerrada:
        embed.add_field(name="Total de votos", value=str(total), inline=True)
        embed.set_footer(text=RODAPE_ENCERRADA)
    else:
        embed.add_field(
            name="Encerra",
            value=discord.utils.format_dt(expira_em, style="R"),
            inline=True,
        )
        embed.set_footer(text=RODAPE_ATIVA)

    if autor:
        embed.set_author(name=f"Enquete de {autor.display_name}", icon_url=autor.display_avatar.url)

    return embed


class VotoButton(discord.ui.Button["EnqueteView"]):
    def __init__(self, poll_id: int, indice: int, texto: str):
        emoji = EMOJI_OPCOES[indice % len(EMOJI_OPCOES)]
        super().__init__(
            label=texto[:70],
            emoji=emoji,
            style=discord.ButtonStyle.secondary,
            custom_id=f"enquete_voto:{poll_id}:{indice}",
            row=indice // 5,
        )
        self.poll_id = poll_id
        self.indice = indice

    async def callback(self, interaction: discord.Interaction):
        await self.view.registrar_voto(interaction, self.indice)


class EnqueteView(discord.ui.View):
    """View persistente. Recriada no cog_load a partir do banco para sobreviver a restart."""

    def __init__(self, cog: "Enquetes", poll_id: int, opcoes: list[str]):
        super().__init__(timeout=None)
        self.cog = cog
        self.poll_id = poll_id
        for i, opcao in enumerate(opcoes):
            self.add_item(VotoButton(poll_id, i, opcao))

    async def registrar_voto(self, interaction: discord.Interaction, indice: int):
        pool = self.cog.bot.pool
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT opcoes, votos, multiplas, encerrada, expira_em FROM enquetes WHERE id = $1",
                self.poll_id,
            )
            if not row or row["encerrada"] or row["expira_em"] <= datetime.now(timezone.utc):
                await interaction.response.send_message(
                    "❄️ Essa enquete já foi encerrada.", ephemeral=True
                )
                return

            votos: dict[str, list[int]] = json.loads(row["votos"])
            opcoes: list[str] = json.loads(row["opcoes"])
            uid = interaction.user.id
            chave = str(indice)
            multiplas = row["multiplas"]

            ja_votou_aqui = uid in votos.get(chave, [])

            if multiplas:
                lista = votos.setdefault(chave, [])
                if ja_votou_aqui:
                    lista.remove(uid)
                else:
                    lista.append(uid)
            else:
                for k in list(votos.keys()):
                    if uid in votos[k]:
                        votos[k].remove(uid)
                if not ja_votou_aqui:
                    votos.setdefault(chave, []).append(uid)

            await conn.execute(
                "UPDATE enquetes SET votos = $1 WHERE id = $2",
                json.dumps(votos),
                self.poll_id,
            )

        embed = _montar_embed(
            pergunta=interaction.message.embeds[0].title.removeprefix("❄️ ").strip(),
            opcoes=opcoes,
            votos=votos,
            autor=None,
            expira_em=row["expira_em"],
            multiplas=multiplas,
            anonima=False,
        )
        embed.set_author(
            name=interaction.message.embeds[0].author.name,
            icon_url=interaction.message.embeds[0].author.icon_url,
        )

        await interaction.response.edit_message(embed=embed, view=self)


class Enquetes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        await self._garantir_tabela()
        await self._reidratar_views()
        self.checar_expiradas.start()

    async def cog_unload(self):
        self.checar_expiradas.cancel()

    async def _garantir_tabela(self):
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS enquetes (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    channel_id BIGINT NOT NULL,
                    message_id BIGINT NOT NULL,
                    pergunta TEXT NOT NULL,
                    opcoes JSONB NOT NULL,
                    votos JSONB NOT NULL DEFAULT '{}',
                    multiplas BOOLEAN NOT NULL DEFAULT FALSE,
                    anonima BOOLEAN NOT NULL DEFAULT FALSE,
                    autor_id BIGINT NOT NULL,
                    criada_em TIMESTAMPTZ NOT NULL DEFAULT now(),
                    expira_em TIMESTAMPTZ NOT NULL,
                    encerrada BOOLEAN NOT NULL DEFAULT FALSE
                )
                """
            )

    async def _reidratar_views(self):
        """Re-registra os botões das enquetes ainda ativas após um restart."""
        async with self.bot.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, opcoes FROM enquetes WHERE encerrada = FALSE"
            )
        for row in rows:
            opcoes = json.loads(row["opcoes"])
            view = EnqueteView(self, row["id"], opcoes)
            self.bot.add_view(view)

    @tasks.loop(minutes=1)
    async def checar_expiradas(self):
        agora = datetime.now(timezone.utc)
        async with self.bot.pool.acquire() as conn:
            expiradas = await conn.fetch(
                "SELECT * FROM enquetes WHERE encerrada = FALSE AND expira_em <= $1",
                agora,
            )
            for row in expiradas:
                await conn.execute("UPDATE enquetes SET encerrada = TRUE WHERE id = $1", row["id"])
        for row in expiradas:
            await self._encerrar_mensagem(row)

    @checar_expiradas.before_loop
    async def _antes_de_checar(self):
        await self.bot.wait_until_ready()

    async def _encerrar_mensagem(self, row):
        canal = self.bot.get_channel(row["channel_id"])
        if canal is None:
            return
        try:
            msg = await canal.fetch_message(row["message_id"])
        except discord.NotFound:
            return

        opcoes = json.loads(row["opcoes"])
        votos = json.loads(row["votos"])

        embed = _montar_embed(
            pergunta=row["pergunta"],
            opcoes=opcoes,
            votos=votos,
            autor=None,
            expira_em=row["expira_em"],
            multiplas=row["multiplas"],
            anonima=row["anonima"],
            encerrada=True,
        )
        if msg.embeds and msg.embeds[0].author:
            embed.set_author(name=msg.embeds[0].author.name, icon_url=msg.embeds[0].author.icon_url)

        view = discord.ui.View()
        for item in EnqueteView(self, row["id"], opcoes).children:
            item.disabled = True
            view.add_item(item)

        await msg.edit(embed=embed, view=view)

    @app_commands.command(
        name="enquete",
        description="Cria uma enquete temática com votação por botões.",
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(
        pergunta="A pergunta da enquete",
        opcao_1="Primeira opção",
        opcao_2="Segunda opção",
        opcao_3="Terceira opção (opcional)",
        opcao_4="Quarta opção (opcional)",
        opcao_5="Quinta opção (opcional)",
        multiplas_escolhas="Permitir votar em mais de uma opção",
        anonima="Ocultar quem votou em relatórios futuros",
        duracao_horas="Duração da enquete em horas (1 a 168)",
    )
    async def enquete(
        self,
        interaction: discord.Interaction,
        pergunta: str,
        opcao_1: str,
        opcao_2: str,
        opcao_3: str | None = None,
        opcao_4: str | None = None,
        opcao_5: str | None = None,
        multiplas_escolhas: bool = False,
        anonima: bool = False,
        duracao_horas: app_commands.Range[int, 1, 168] = 24,
    ):
        opcoes = [o for o in [opcao_1, opcao_2, opcao_3, opcao_4, opcao_5] if o]
        expira_em = datetime.now(timezone.utc) + timedelta(hours=duracao_horas)

        async with self.bot.pool.acquire() as conn:
            poll_id = await conn.fetchval(
                """
                INSERT INTO enquetes
                    (guild_id, channel_id, message_id, pergunta, opcoes, votos,
                     multiplas, anonima, autor_id, expira_em)
                VALUES ($1, $2, 0, $3, $4, '{}', $5, $6, $7, $8)
                RETURNING id
                """,
                interaction.guild_id,
                interaction.channel_id,
                pergunta,
                json.dumps(opcoes),
                multiplas_escolhas,
                anonima,
                interaction.user.id,
                expira_em,
            )

        embed = _montar_embed(
            pergunta=pergunta,
            opcoes=opcoes,
            votos={},
            autor=interaction.user,
            expira_em=expira_em,
            multiplas=multiplas_escolhas,
            anonima=anonima,
        )
        view = EnqueteView(self, poll_id, opcoes)

        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE enquetes SET message_id = $1 WHERE id = $2", msg.id, poll_id
            )

    @app_commands.command(
        name="enquete-encerrar",
        description="Encerra a enquete mais recente do canal antes da hora.",
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def enquete_encerrar(self, interaction: discord.Interaction):
        async with self.bot.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM enquetes
                WHERE channel_id = $1 AND encerrada = FALSE
                ORDER BY criada_em DESC LIMIT 1
                """,
                interaction.channel_id,
            )
            if not row:
                await interaction.response.send_message(
                    "❄️ Nenhuma enquete ativa neste canal.", ephemeral=True
                )
                return
            await conn.execute("UPDATE enquetes SET encerrada = TRUE WHERE id = $1", row["id"])

        await self._encerrar_mensagem(row)
        await interaction.response.send_message("🌌 Enquete encerrada.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Enquetes(bot))