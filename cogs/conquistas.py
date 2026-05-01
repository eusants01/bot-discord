import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from utils.db import conn, cursor

COR_JUJUTSU = 0x7B2CFF
CANAL_CONQUISTAS_ID = 1498134533839650838

CONQUISTAS = {
    "primeiro_selo": {"emoji": "🩸", "nome": "Primeiro Selo", "descricao": "Despertou sua primeira marca dentro do domínio."},
    "dominio_revelado": {"emoji": "🌀", "nome": "Domínio Revelado", "descricao": "Visualizou suas conquistas pela primeira vez."},
    "contrato_aberto": {"emoji": "📜", "nome": "Contrato Aberto", "descricao": "Abriu seu primeiro ticket amaldiçoado."},
    "voz_do_dominio": {"emoji": "📢", "nome": "Voz do Domínio", "descricao": "Enviou 50 mensagens dentro da Família."},
    "presenca_constante": {"emoji": "👁️", "nome": "Presença Constante", "descricao": "Enviou 100 mensagens dentro do domínio."},
    "energia_instavel": {"emoji": "🔥", "nome": "Energia Instável", "descricao": "Enviou 200 mensagens no servidor."},
    "sangue_familia": {"emoji": "🩸", "nome": "Sangue da Família", "descricao": "Entrou na Família Sant’s."},
    "alianca_amaldicoada": {"emoji": "🤝", "nome": "Aliança Amaldiçoada", "descricao": "Criou laços dentro do domínio."},
    "observador_silencioso": {"emoji": "👁️", "nome": "Observador Silencioso", "descricao": "Acompanhou o domínio sem se expor."},
    "portador_do_caos": {"emoji": "💀", "nome": "Portador do Caos", "descricao": "Causou impacto dentro do domínio."},
    "herdeiro_do_dominio": {"emoji": "👑", "nome": "Herdeiro do Domínio", "descricao": "Alcançou reconhecimento na Família."},
    "exorcista_vitorioso": {"emoji": "⚔️", "nome": "Exorcista Vitorioso", "descricao": "Venceu um evento especial."},
    "sombra_oculta": {"emoji": "🔒", "nome": "???", "descricao": "Apenas os escolhidos descobrirão."},
    "lenda_proibida": {"emoji": "🕯️", "nome": "???", "descricao": "Uma presença que não deveria existir..."}
}


async def liberar_conquista(bot, usuario, conquista_id, canal=None):
    if conquista_id not in CONQUISTAS:
        return False

    cursor.execute(
        "SELECT 1 FROM conquistas WHERE user_id=? AND conquista_id=?",
        (str(usuario.id), conquista_id)
    )

    if cursor.fetchone():
        return False

    data = datetime.now().strftime("%d/%m/%Y %H:%M")

    cursor.execute(
        "INSERT INTO conquistas (user_id, conquista_id, data) VALUES (?, ?, ?)",
        (str(usuario.id), conquista_id, data)
    )
    conn.commit()

    conquista = CONQUISTAS[conquista_id]
    canal_conquistas = bot.get_channel(CANAL_CONQUISTAS_ID)

    if canal_conquistas:
        embed = discord.Embed(
            title="🏆 Nova Conquista Desbloqueada",
            description=(
                f"{usuario.mention} despertou uma nova conquista!\n\n"
                f"{conquista['emoji']} **{conquista['nome']}**\n"
                f"{conquista['descricao']}"
            ),
            color=COR_JUJUTSU
        )

        embed.set_thumbnail(url=usuario.display_avatar.url)
        embed.set_footer(text="Família Sant’s • Sistema de Conquistas")

        await canal_conquistas.send(embed=embed)

    return True


class ViewConquistas(discord.ui.View):
    def __init__(self, usuario, paginas):
        super().__init__(timeout=60)
        self.usuario = usuario
        self.paginas = paginas
        self.pagina = 0

    async def atualizar(self, interaction):
        await interaction.response.edit_message(
            embed=self.paginas[self.pagina],
            view=self
        )

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.usuario.id:
            return await interaction.response.send_message(
                "Esse painel não é seu.",
                ephemeral=True
            )

        if self.pagina > 0:
            self.pagina -= 1

        await self.atualizar(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def proxima(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.usuario.id:
            return await interaction.response.send_message(
                "Esse painel não é seu.",
                ephemeral=True
            )

        if self.pagina < len(self.paginas) - 1:
            self.pagina += 1

        await self.atualizar(interaction)


class Conquistas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        user_id = str(message.author.id)

        cursor.execute(
            "SELECT total FROM mensagens WHERE user_id=?",
            (user_id,)
        )
        row = cursor.fetchone()

        if row:
            total = row[0] + 1
            cursor.execute(
                "UPDATE mensagens SET total=? WHERE user_id=?",
                (total, user_id)
            )
        else:
            total = 1
            cursor.execute(
                "INSERT INTO mensagens (user_id, total) VALUES (?, ?)",
                (user_id, total)
            )

        conn.commit()

        if total == 1:
            await liberar_conquista(self.bot, message.author, "primeiro_selo")
        elif total == 50:
            await liberar_conquista(self.bot, message.author, "voz_do_dominio")
        elif total == 100:
            await liberar_conquista(self.bot, message.author, "presenca_constante")
        elif total == 200:
            await liberar_conquista(self.bot, message.author, "energia_instavel")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await liberar_conquista(self.bot, member, "sangue_familia")

    @app_commands.command(
        name="conquistas",
        description="Veja suas conquistas dentro do domínio."
    )
    async def conquistas(self, interaction: discord.Interaction):
        await liberar_conquista(self.bot, interaction.user, "dominio_revelado")

        cursor.execute(
            "SELECT conquista_id, data FROM conquistas WHERE user_id=?",
            (str(interaction.user.id),)
        )

        user_data = {cid: data for cid, data in cursor.fetchall()}

        total = len(CONQUISTAS)
        conquistadas = len(user_data)

        lista = []

        for conquista_id, conquista in CONQUISTAS.items():
            if conquista_id in user_data:
                texto = (
                    f"{conquista['emoji']} **{conquista['nome']}**\n"
                    f"{conquista['descricao']}\n"
                    f"**Conquistado em:** {user_data[conquista_id]}"
                )
            else:
                texto = (
                    f"🔒 **Conquista Bloqueada**\n"
                    f"Continue explorando o domínio para revelar."
                )

            lista.append(texto)

        paginas = []
        por_pagina = 4

        for i in range(0, len(lista), por_pagina):
            embed = discord.Embed(
                title=f"🌀 Todas as Conquistas [{conquistadas}/{total}]",
                description="\n\n".join(lista[i:i + por_pagina]),
                color=COR_JUJUTSU
            )

            embed.set_author(
                name=f"Domínio de {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )

            embed.set_footer(
                text=f"Página {(i // por_pagina) + 1}/{(len(lista) - 1) // por_pagina + 1} • Família Sant’s"
            )

            paginas.append(embed)

        await interaction.response.send_message(
            embed=paginas[0],
            view=ViewConquistas(interaction.user, paginas),
            ephemeral=True
        )

    @app_commands.command(
        name="darconquista",
        description="Dar uma conquista para um membro."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def darconquista(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        conquista_id: str
    ):
        if conquista_id not in CONQUISTAS:
            ids = "\n".join(CONQUISTAS.keys())
            return await interaction.response.send_message(
                f"Conquista não encontrada.\n\nIDs disponíveis:\n```{ids}```",
                ephemeral=True
            )

        ganhou = await liberar_conquista(
            self.bot,
            membro,
            conquista_id
        )

        if not ganhou:
            return await interaction.response.send_message(
                f"{membro.mention} já possui essa conquista.",
                ephemeral=True
            )

        await interaction.response.send_message(
            f"✅ Conquista entregue para {membro.mention}.",
            ephemeral=True
        )

    @app_commands.command(
        name="codigo",
        description="Resgate um código secreto amaldiçoado."
    )
    @app_commands.describe(
        codigo="Digite o código secreto amaldiçoado."
    )
    async def codigo(self, interaction: discord.Interaction, codigo: str):
        codigos_secretos = {
            "MAHORAGA": {
                "conquista": "sombra_oculta",
                "limite": 1,
                "tipo": "LENDÁRIO 🔥"
            },
            "SUKUNAHEIAN": {
                "conquista": "lenda_proibida",
                "limite": 5,
                "tipo": "RARO ⚡"
            }
        }

        codigo = codigo.upper().replace(" ", "")

        if codigo not in codigos_secretos:
            return await interaction.response.send_message(
                "❌ Código inválido. A barreira rejeitou sua tentativa.",
                ephemeral=True
            )

        user_id = str(interaction.user.id)

        cursor.execute(
            "SELECT 1 FROM codigos WHERE codigo=? AND user_id=?",
            (codigo, user_id)
        )

        if cursor.fetchone():
            return await interaction.response.send_message(
                "❌ Você já resgatou esse código.",
                ephemeral=True
            )

        limite = codigos_secretos[codigo]["limite"]

        cursor.execute(
            "SELECT COUNT(*) FROM codigos WHERE codigo=?",
            (codigo,)
        )

        usos = cursor.fetchone()[0]

        if usos >= limite:
            return await interaction.response.send_message(
                "❌ Esse código já atingiu o limite máximo de resgates.",
                ephemeral=True
            )

        conquista_id = codigos_secretos[codigo]["conquista"]

        ganhou = await liberar_conquista(
            self.bot,
            interaction.user,
            conquista_id
        )

        if not ganhou:
            return await interaction.response.send_message(
                "❌ Você já possui essa conquista.",
                ephemeral=True
            )

        cursor.execute(
            "INSERT INTO codigos (codigo, user_id) VALUES (?, ?)",
            (codigo, user_id)
        )
        conn.commit()

        restantes = limite - (usos + 1)
        tipo = codigos_secretos[codigo]["tipo"]

        await interaction.response.send_message(
            f"✅ Código aceito!\n\n"
            f"🏆 Tipo: **{tipo}**\n"
            f"🔢 Restantes: **{restantes}/{limite}**",
            ephemeral=True
        )

        if limite == 1:
            canal_conquistas = self.bot.get_channel(CANAL_CONQUISTAS_ID)

            if canal_conquistas:
                embed_lenda = discord.Embed(
                    title="👑 O ESCOLHIDO DESPERTOU",
                    description=(
                        f"{interaction.user.mention} foi o **único** capaz de romper a barreira.\n\n"
                        f"🔥 Código Lendário: **{codigo}**\n"
                        f"🏆 Conquista exclusiva liberada.\n\n"
                        f"Uma lenda proibida acaba de nascer dentro da Família Sant’s."
                    ),
                    color=0xFF0000
                )

                embed_lenda.set_thumbnail(url=interaction.user.display_avatar.url)
                embed_lenda.set_footer(text="Família Sant’s • Evento Lendário")

                await canal_conquistas.send(embed=embed_lenda)


async def setup(bot):
    await bot.add_cog(Conquistas(bot))