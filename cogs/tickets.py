import discord
from discord.ext import commands
from discord import app_commands
from io import BytesIO
import asyncio
import re
from datetime import datetime, timezone


CATEGORIA_TICKETS_ID = 1495288098010169574
CANAL_LOG_ID = 1495272331558391818

CARGOS_ATENDIMENTO_IDS = [
    1487560221202321600,
    1501356975491907664,
    1500545846427652166,
    1480381506064093225,
]

COR_ROXA = discord.Color.from_rgb(90, 0, 150)
COR_VERMELHA = discord.Color.from_rgb(150, 0, 0)
COR_DOURADA = discord.Color.from_rgb(180, 120, 0)
COR_ESCURA = discord.Color.from_rgb(40, 0, 65)
COR_VERDE = discord.Color.from_rgb(0, 150, 80)

BANNER_TICKET_FECHADO = "https://i.imgur.com/ynK8fwA.png"


def limpar_nome(texto: str) -> str:
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9-]", "-", texto)
    texto = re.sub(r"-+", "-", texto)
    return texto.strip("-")


def tem_permissao_ticket(member: discord.Member) -> bool:
    return member.guild_permissions.administrator or any(
        role.id in CARGOS_ATENDIMENTO_IDS for role in member.roles
    )


def formatar_duracao(segundos: int) -> str:
    minutos, segundos = divmod(segundos, 60)
    horas, minutos = divmod(minutos, 60)
    dias, horas = divmod(horas, 24)

    partes = []

    if dias:
        partes.append(f"{dias}d")
    if horas:
        partes.append(f"{horas}h")
    if minutos:
        partes.append(f"{minutos}min")
    if segundos and not partes:
        partes.append(f"{segundos}s")

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
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not tem_permissao_ticket(interaction.user):
            await interaction.response.send_message(
                "❌ Você não possui permissão para encerrar este domínio.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🩸 O domínio será encerrado em instantes...",
            ephemeral=True
        )

        log = interaction.guild.get_channel(CANAL_LOG_ID)

        criado_em = interaction.channel.created_at
        fechado_em = datetime.now(timezone.utc)
        duracao = formatar_duracao(int((fechado_em - criado_em).total_seconds()))

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
                name="⏳ Duração",
                value=f"`{duracao}`",
                inline=True
            )

            embed_log.add_field(
                name="💬 Mensagens",
                value=f"`{total_mensagens}`",
                inline=True
            )

            embed_log.add_field(
                name="📜 Registro",
                value="Use o botão abaixo para baixar o transcript.",
                inline=False
            )

            embed_log.set_thumbnail(url=interaction.user.display_avatar.url)
            embed_log.set_image(url=BANNER_TICKET_FECHADO)
            embed_log.set_footer(text="Família Sant's • Sistema de Tickets")

            await msg.edit(embed=embed_log, view=BotaoDownload(link))

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
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🛑 O ritual foi interrompido. O domínio permanece ativo.",
            ephemeral=True
        )


class TicketActionsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Assumir Ritual",
        style=discord.ButtonStyle.green,
        emoji="🩸",
        custom_id="sants_assumir_ritual"
    )
    async def assumir(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not tem_permissao_ticket(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas a equipe pode assumir este domínio.",
                ephemeral=True
            )
            return

        mensagem = interaction.message

        if not mensagem.embeds:
            await interaction.response.send_message(
                "❌ Não consegui encontrar o painel deste ticket.",
                ephemeral=True
            )
            return

        embed = mensagem.embeds[0]

        novo_embed = discord.Embed(
            title=embed.title,
            description=(
                embed.description
                .replace(
                    "⏳ **Status do Ritual:** `Aguardando atendimento`",
                    f"🟢 **Status do Ritual:** `Em atendimento por {interaction.user.display_name}`"
                )
            ),
            color=COR_VERDE
        )

        if embed.thumbnail:
            novo_embed.set_thumbnail(url=embed.thumbnail.url)

        if embed.image:
            novo_embed.set_image(url=embed.image.url)

        novo_embed.set_footer(
            text=f"Ritual assumido por {interaction.user.display_name}"
        )

        button.disabled = True
        button.label = "Ritual Assumido"

        await mensagem.edit(embed=novo_embed, view=self)

        await interaction.response.send_message(
            f"🩸 {interaction.user.mention} assumiu este ritual.",
            ephemeral=False
        )

    @discord.ui.button(
        label="Painel Restrito",
        style=discord.ButtonStyle.blurple,
        emoji="⚙️",
        custom_id="sants_painel_restrito"
    )
    async def painel_admin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not tem_permissao_ticket(interaction.user):
            await interaction.response.send_message(
                "❌ Você não possui acesso ao painel restrito.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="⚙️ Painel Restrito",
            description=(
                "Informações administrativas deste domínio.\n\n"
                f"📁 **Canal:** {interaction.channel.mention}\n"
                f"👤 **Atendente:** {interaction.user.mention}\n"
                f"🕒 **Criado em:** <t:{int(interaction.channel.created_at.timestamp())}:f>\n\n"
                "Use os botões principais para assumir, notificar ou encerrar o atendimento."
            ),
            color=COR_ROXA
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    @discord.ui.button(
        label="Encerrar Domínio",
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="sants_encerrar_dominio"
    )
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not tem_permissao_ticket(interaction.user):
            await interaction.response.send_message(
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

        await interaction.response.send_message(
            embed=embed,
            view=ConfirmarFechamento(),
            ephemeral=True
        )

    @discord.ui.button(
        label="Invocar Feiticeiro",
        style=discord.ButtonStyle.primary,
        emoji="📢",
        custom_id="sants_invocar_feiticeiro"
    )
    async def notificar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not tem_permissao_ticket(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas a equipe pode invocar atendentes.",
                ephemeral=True
            )
            return

        mencoes_staff = " ".join(
            f"<@&{cargo_id}>"
            for cargo_id in CARGOS_ATENDIMENTO_IDS
        )

        embed = discord.Embed(
            title="📢 Feiticeiros Invocados",
            description=(
                f"{mencoes_staff}\n\n"
                "A barreira detectou que este domínio precisa de atenção."
            ),
            color=COR_DOURADA
        )

        await interaction.response.send_message(
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True)
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
                "grau": "🟣 Monitorado"
            },
            "denuncia": {
                "nome": "denuncia",
                "titulo": "🚨 Relatório de Maldição",
                "descricao": "Traga provas e denuncie a maldição.",
                "cor": COR_VERMELHA,
                "imagem": "https://i.imgur.com/Bl79W4Y.png",
                "thumbnail": "https://i.imgur.com/zkIgP83.png",
                "grau": "🔴 Alto Risco"
            },
            "cargo_exclusivo": {
                "nome": "cargo-exclusivo",
                "titulo": "📜 Arquivo Restrito",
                "descricao": "Solicite seu cargo exclusivo preenchendo o modelo.",
                "cor": COR_ESCURA,
                "imagem": "https://i.imgur.com/UP1k58c.png",
                "thumbnail": "https://i.imgur.com/4ZnTLm3.png",
                "grau": "⚫ Restrito"
            },
            "comprar_vaga": {
                "nome": "ritual-acesso",
                "titulo": "💰 Ritual de Acesso",
                "descricao": "Deseja ingressar na Família Sant's? Tributo necessário: R$80,00.",
                "cor": COR_DOURADA,
                "imagem": "https://i.imgur.com/pB3mL7E.png",
                "thumbnail": "https://i.imgur.com/yw1FDpN.png",
                "grau": "🟡 Pacto"
            }
        }

        info = tipos_ticket[tipo_ticket]
        nome_canal = limpar_nome(f"{info['nome']}-{user.name}")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
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
                f"👁️ Olá {user.mention}\n\n"
                "🩸 **Seu domínio foi aberto pela barreira da Família Sant's.**\n"
                "Descreva sua solicitação enquanto aguarda um feiticeiro responsável.\n\n"
                "📜 **Orientações da Escola Jujutsu:**\n"
                "• Explique claramente sua solicitação.\n"
                "• Envie provas/imagens se necessário.\n"
                "• Evite spam ou menções desnecessárias.\n\n"
                f"📌 **Categoria:** {info['titulo']}\n"
                f"☠️ **Nível da Maldição:** `{info['grau']}`\n"
                "⏳ **Status do Ritual:** `Aguardando atendimento`\n"
                "🌑 **Barreira:** `Ativa`\n\n"
                f"{mencoes_staff}"
            ),
            color=info["cor"]
        )

        embed_ticket.set_thumbnail(url=info["thumbnail"])
        embed_ticket.set_image(url=info["imagem"])
        embed_ticket.set_footer(
            text="Família Sant's • Aguarde atendimento da equipe"
        )

        await canal.send(
            content=user.mention,
            embed=embed_ticket,
            view=TicketActionsView()
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
        self.bot.add_view(TicketActionsView())

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

        embed.set_image(url="https://i.imgur.com/s3Qvs9x.png")
        embed.set_footer(text="Família Sant's • Painel oficial de atendimento")

        await interaction.channel.send(
            embed=embed,
            view=TicketView()
        )

        await interaction.response.send_message(
            "✅ Painel enviado com sucesso.",
            ephemeral=True
        )

    @ticket.error
    async def ticket_error(self, interaction: discord.Interaction, error):
        mensagem = "❌ Você não tem permissão para usar esse comando."

        if interaction.response.is_done():
            await interaction.followup.send(mensagem, ephemeral=True)
        else:
            await interaction.response.send_message(mensagem, ephemeral=True)


async def setup(bot):
    await bot.add_cog(TicketCog(bot))