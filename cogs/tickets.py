import discord
from discord.ext import commands
from discord import app_commands
from io import BytesIO
import asyncio
import re
from datetime import datetime, timezone


CATEGORIA_TICKETS_ID = 1495288098010169574
CANAL_LOG_ID = 1495272331558391818

# 🔮 CARGOS QUE PODEM ATENDER / FECHAR TICKETS
CARGOS_ATENDIMENTO_IDS = [
    1487560221202321600,  # STAFF
    1501356975491907664,  # SUPORTE
    1500545846427652166,  # NOVO CARGO
    1480381506064093225,  # NOVO CARGO
]

COR_ROXA = discord.Color.from_rgb(90, 0, 150)
COR_VERMELHA = discord.Color.from_rgb(150, 0, 0)
COR_DOURADA = discord.Color.from_rgb(180, 120, 0)
COR_ESCURA = discord.Color.from_rgb(40, 0, 65)

BANNER_TICKET_FECHADO = "https://i.imgur.com/ynK8fwA.png"


def limpar_nome(texto: str) -> str:
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9-]", "-", texto)
    texto = re.sub(r"-+", "-", texto)
    return texto.strip("-")


def formatar_duracao(segundos: int) -> str:
    minutos, seg = divmod(segundos, 60)
    horas, min = divmod(minutos, 60)
    dias, horas = divmod(horas, 24)

    partes = []

    if dias:
        partes.append(f"{dias}d")
    if horas:
        partes.append(f"{horas}h")
    if min:
        partes.append(f"{min}min")
    if seg and not partes:
        partes.append(f"{seg}s")

    return " ".join(partes) if partes else "0s"


async def gerar_transcricao(channel: discord.TextChannel):
    mensagens = []
    total_mensagens = 0

    async for msg in channel.history(limit=None, oldest_first=True):
        total_mensagens += 1

        autor = f"{msg.author} ({msg.author.id})"
        data = msg.created_at.strftime("%d/%m/%Y %H:%M")
        conteudo = msg.content if msg.content else "[Sem texto]"

        if msg.attachments:
            anexos = "\n".join([a.url for a in msg.attachments])
            conteudo += f"\nAnexos:\n{anexos}"

        mensagens.append(f"[{data}] {autor}: {conteudo}")

    if not mensagens:
        mensagens.append("Nenhuma mensagem registrada neste domínio.")

    arquivo = BytesIO("\n".join(mensagens).encode("utf-8"))
    arquivo.seek(0)

    nome_arquivo = f"registro-do-dominio-{limpar_nome(channel.name)}.txt"

    return discord.File(arquivo, filename=nome_arquivo), total_mensagens


class BotaoDownload(discord.ui.View):
    def __init__(self, url):
        super().__init__(timeout=None)

        self.add_item(
            discord.ui.Button(
                label="📥 Baixar Registro",
                url=url
            )
        )

        self.add_item(
            discord.ui.Button(
                label="🩸 Domínio Encerrado",
                style=discord.ButtonStyle.gray,
                disabled=True
            )
        )


class ConfirmarFechamento(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(
        label="Confirmar Encerramento",
        style=discord.ButtonStyle.red,
        emoji="🔒"
    )
    async def confirmar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "🩸 O domínio será encerrado em instantes...",
            ephemeral=True
        )

        log = interaction.guild.get_channel(CANAL_LOG_ID)

        criado_em = interaction.channel.created_at
        fechado_em = datetime.now(timezone.utc)
        duracao_segundos = int((fechado_em - criado_em).total_seconds())
        duracao = formatar_duracao(duracao_segundos)

        arquivo, total_mensagens = await gerar_transcricao(interaction.channel)

        if log:
            msg = await log.send(file=arquivo)
            link = msg.attachments[0].url

            embed_log = discord.Embed(
                title="🩸 Domínio Encerrado",
                description=(
                    "O ritual foi finalizado com sucesso.\n"
                    "A barreira amaldiçoada foi desfeita e os registros foram selados."
                ),
                color=COR_ROXA
            )

            embed_log.add_field(
                name="👁️ Responsável",
                value=interaction.user.mention,
                inline=True
            )

            embed_log.add_field(
                name="📁 Canal",
                value=f"`{interaction.channel.name}`",
                inline=True
            )

            embed_log.add_field(
                name="🕒 Encerrado em",
                value=f"<t:{int(interaction.created_at.timestamp())}:f>",
                inline=False
            )

            embed_log.add_field(
                name="⏳ Duração do Ritual",
                value=f"`{duracao}`",
                inline=True
            )

            embed_log.add_field(
                name="💬 Mensagens Registradas",
                value=f"`{total_mensagens}`",
                inline=True
            )

            embed_log.add_field(
                name="📜 Registro",
                value="Use o botão abaixo para baixar o transcript.",
                inline=False
            )

            embed_log.set_thumbnail(
                url=interaction.user.display_avatar.url
            )

            embed_log.set_image(
                url=BANNER_TICKET_FECHADO
            )

            embed_log.set_footer(
                text="Família Sant's • Sistema de Tickets"
            )

            await msg.edit(
                embed=embed_log,
                view=BotaoDownload(link)
            )

        aviso = discord.Embed(
            title="🌑 Colapso do Domínio",
            description=(
                "A energia amaldiçoada está se dissipando...\n"
                "Este canal será apagado em **5 segundos**."
            ),
            color=COR_ESCURA
        )

        await interaction.channel.send(embed=aviso)

        await asyncio.sleep(5)

        await interaction.channel.delete()

    @discord.ui.button(
        label="Cancelar",
        style=discord.ButtonStyle.gray,
        emoji="🛑"
    )
    async def cancelar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "🛑 O ritual foi interrompido. O domínio permanece ativo.",
            ephemeral=True
        )


class FecharTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fechar Ticket",
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="fechar_ticket_sants"
    )
    async def fechar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.defer(ephemeral=True)

        tem_permissao = interaction.user.guild_permissions.administrator or any(
            role.id in CARGOS_ATENDIMENTO_IDS
            for role in interaction.user.roles
        )

        if not tem_permissao:
            await interaction.followup.send(
                "❌ Você não possui permissão para encerrar este domínio.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🔒 Confirmar Encerramento",
            description=(
                "Tem certeza que deseja encerrar este domínio?\n\n"
                "Após confirmar, o registro será enviado ao canal de logs "
                "e este ticket será apagado."
            ),
            color=COR_VERMELHA
        )

        await interaction.followup.send(
            embed=embed,
            view=ConfirmarFechamento(),
            ephemeral=True
        )


class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Domínio de Dúvidas",
                description="Tem incertezas? Abra um chamado e obtenha respostas.",
                emoji="❓",
                value="duvida"
            ),
            discord.SelectOption(
                label="Relatório de Maldição",
                description="Presenciou algo suspeito? Traga provas da maldição.",
                emoji="🚨",
                value="denuncia"
            ),
            discord.SelectOption(
                label="Ritual de Acesso",
                description="Deseja ingressar na Família Sant's? Tributo: R$80,00.",
                emoji="💰",
                value="comprar_vaga"
            ),
            discord.SelectOption(
                label="Arquivo Restrito",
                description="Solicite seu cargo exclusivo preenchendo o modelo.",
                emoji="📜",
                value="cargo_exclusivo"
            )
        ]

        super().__init__(
            placeholder="Selecione um domínio...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_select_sants"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        user = interaction.user
        categoria = guild.get_channel(CATEGORIA_TICKETS_ID)

        if categoria is None:
            await interaction.followup.send(
                "❌ Categoria de tickets não encontrada.",
                ephemeral=True
            )
            return

        for channel in guild.text_channels:
            if channel.topic and str(user.id) in channel.topic:
                await interaction.followup.send(
                    f"❌ Você já possui um domínio ativo: {channel.mention}",
                    ephemeral=True
                )
                return

        tipo_ticket = self.values[0]

        tipos_ticket = {
            "duvida": {
                "nome": "duvida",
                "titulo": "❓ Domínio de Dúvidas",
                "descricao": "Tem incertezas? Abra um chamado e obtenha respostas.",
                "cor": COR_ROXA,
                "imagem": "https://i.imgur.com/4GQjoSb.png",
                "thumbnail": "https://i.imgur.com/AYs4N07.png",
                "grau": "🟣 Grau de Maldição: Dúvida"
            },
            "denuncia": {
                "nome": "denuncia",
                "titulo": "🚨 Relatório de Maldição",
                "descricao": "Traga provas e denuncie a maldição.",
                "cor": COR_VERMELHA,
                "imagem": "https://i.imgur.com/Bl79W4Y.png",
                "thumbnail": "https://i.imgur.com/zkIgP83.png",
                "grau": "🔴 Grau de Maldição: Alto Risco"
            },
            "cargo_exclusivo": {
                "nome": "cargo-exclusivo",
                "titulo": "📜 Arquivo Restrito",
                "descricao": "Solicite seu cargo exclusivo preenchendo o modelo.",
                "cor": COR_ESCURA,
                "imagem": "https://i.imgur.com/UP1k58c.png",
                "thumbnail": "https://i.imgur.com/4ZnTLm3.png",
                "grau": "⚫ Grau de Maldição: Restrito"
            },
            "comprar_vaga": {
                "nome": "ritual-acesso",
                "titulo": "💰 Ritual de Acesso",
                "descricao": "Deseja ingressar na Família Sant's? Tributo necessário: R$80,00.",
                "cor": COR_DOURADA,
                "imagem": "https://i.imgur.com/pB3mL7E.png",
                "thumbnail": "https://i.imgur.com/yw1FDpN.png",
                "grau": "🟡 Grau de Maldição: Pacto"
            }
        }

        info = tipos_ticket[tipo_ticket]

        nome_canal = limpar_nome(f"{info['nome']}-{user.name}")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                read_message_history=True
            ),
        }

        for cargo_id in CARGOS_ATENDIMENTO_IDS:
            cargo = guild.get_role(cargo_id)

            if cargo:
                overwrites[cargo] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                )

        canal = await guild.create_text_channel(
            name=nome_canal,
            category=categoria,
            overwrites=overwrites,
            topic=f"{user.id} | Ticket de {user} | Tipo: {tipo_ticket}"
        )

        mencoes_staff = " ".join(
            f"<@&{cargo_id}>"
            for cargo_id in CARGOS_ATENDIMENTO_IDS
        )

        embed_ticket = discord.Embed(
            title=info["titulo"],
            description=(
                f"👁️ {user.mention}, você entrou em um domínio.\n\n"
                f"**Detalhes:** {info['descricao']}\n"
                f"**Classificação:** {info['grau']}\n\n"
                "📌 **Orientação:**\n"
                "Explique sua solicitação com clareza e envie provas/imagens se necessário.\n\n"
                "⏳ **Status:** `Aguardando atendimento`\n\n"
                f"{mencoes_staff}"
            ),
            color=info["cor"]
        )

        embed_ticket.set_thumbnail(url=info["thumbnail"])
        embed_ticket.set_image(url=info["imagem"])
        embed_ticket.set_footer(
            text="Finalize o ritual quando o atendimento terminar."
        )

        await canal.send(
            content=user.mention,
            embed=embed_ticket,
            view=FecharTicketView()
        )

        await interaction.followup.send(
            f"✅ Domínio criado com sucesso: {canal.mention}",
            ephemeral=True
        )


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bot.add_view(TicketView())
        self.bot.add_view(FecharTicketView())

    @app_commands.command(
        name="ticket",
        description="Enviar painel de ticket"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🩸 Escola Jujutsu — Central de Rituais",
            description=(
                "Canalize sua energia amaldiçoada e escolha o domínio desejado.\n\n"
                "❓ **Domínio de Dúvidas** — suporte geral.\n"
                "🚨 **Relatório de Maldição** — denúncias e provas.\n"
                "💰 **Ritual de Acesso** — ingresso na Família Sant's.\n"
                "📜 **Arquivo Restrito** — solicitação de cargo exclusivo.\n\n"
                "Selecione uma opção abaixo para iniciar o atendimento."
            ),
            color=COR_ROXA
        )

        embed.set_image(
            url="https://i.imgur.com/s3Qvs9x.png"
        )

        embed.set_footer(
            text="Família Sant's • Painel oficial de atendimento"
        )

        await interaction.channel.send(
            embed=embed,
            view=TicketView()
        )

        await interaction.response.send_message(
            "✅ Painel enviado com sucesso.",
            ephemeral=True
        )

    @ticket.error
    async def ticket_error(
        self,
        interaction: discord.Interaction,
        error
    ):
        if interaction.response.is_done():
            await interaction.followup.send(
                "❌ Você não tem permissão para usar esse comando.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Você não tem permissão para usar esse comando.",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(TicketCog(bot))