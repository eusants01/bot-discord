import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from datetime import datetime, timedelta

COR_JUJUTSU = 0x6A00FF

GIF_SORTEIO = "https://cdn.discordapp.com/attachments/961677475191078992/1500700233816871062/content.png?ex=69f96381&is=69f81201&hm=513fd8c673f3b3121d73bf382a8c82a968f9fafe99ba949d37e0bd301f1b0e6b&"


class SorteioView(discord.ui.View):
    def __init__(self, cog, sorteio_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.sorteio_id = sorteio_id

    def is_admin(self, interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator

    @discord.ui.button(label="Participar", emoji="🎟️", style=discord.ButtonStyle.danger)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.cog.sorteios.get(self.sorteio_id)

        if not data:
            return await interaction.response.send_message(
                "❌ Esse sorteio não está mais ativo.",
                ephemeral=True
            )

        if data["cancelado"] or data["finalizado"]:
            return await interaction.response.send_message(
                "❌ Esse sorteio já foi encerrado.",
                ephemeral=True
            )

        membro = interaction.user

        if data["cargo_id"]:
            if not any(cargo.id == data["cargo_id"] for cargo in membro.roles):
                return await interaction.response.send_message(
                    f"❌ Você precisa do cargo <@&{data['cargo_id']}> para participar.",
                    ephemeral=True
                )

        if membro.id in data["participantes"]:
            return await interaction.response.send_message(
                "⚠️ Você já está participando.",
                ephemeral=True
            )

        data["participantes"].add(membro.id)

        await self.cog.atualizar_mensagem(self.sorteio_id)

        await interaction.response.send_message(
            "🩸 Você entrou no sorteio amaldiçoado.",
            ephemeral=True
        )

    @discord.ui.button(label="Sair", emoji="🚪", style=discord.ButtonStyle.secondary)
    async def sair(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.cog.sorteios.get(self.sorteio_id)

        if not data:
            return await interaction.response.send_message(
                "❌ Sorteio não encontrado.",
                ephemeral=True
            )

        if data["finalizado"] or data["cancelado"]:
            return await interaction.response.send_message(
                "❌ Esse sorteio já foi encerrado.",
                ephemeral=True
            )

        if interaction.user.id not in data["participantes"]:
            return await interaction.response.send_message(
                "⚠️ Você não está participando.",
                ephemeral=True
            )

        data["participantes"].remove(interaction.user.id)

        await self.cog.atualizar_mensagem(self.sorteio_id)

        await interaction.response.send_message(
            "🚪 Você saiu do sorteio.",
            ephemeral=True
        )

    @discord.ui.button(label="Finalizar", emoji="🏁", style=discord.ButtonStyle.success)
    async def finalizar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_admin(interaction):
            return await interaction.response.send_message(
                "❌ Apenas administradores podem usar isso.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        await self.cog.finalizar_sorteio(self.sorteio_id, manual=True)

        await interaction.followup.send(
            "🏁 Sorteio finalizado.",
            ephemeral=True
        )

    @discord.ui.button(label="Reroll", emoji="🔄", style=discord.ButtonStyle.primary)
    async def reroll(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_admin(interaction):
            return await interaction.response.send_message(
                "❌ Apenas administradores podem usar isso.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        resultado = await self.cog.reroll_sorteio(self.sorteio_id)

        await interaction.followup.send(resultado, ephemeral=True)

    @discord.ui.button(label="Cancelar", emoji="❌", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_admin(interaction):
            return await interaction.response.send_message(
                "❌ Apenas administradores podem usar isso.",
                ephemeral=True
            )

        data = self.cog.sorteios.get(self.sorteio_id)

        if not data:
            return await interaction.response.send_message(
                "❌ Sorteio não encontrado.",
                ephemeral=True
            )

        data["cancelado"] = True
        data["finalizado"] = True

        await self.cog.atualizar_mensagem(self.sorteio_id, cancelado=True)

        await interaction.response.send_message(
            "❌ Sorteio cancelado.",
            ephemeral=True
        )


class Sorteios(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sorteios = {}

    @app_commands.command(
        name="sorteio",
        description="Criar um sorteio amaldiçoado"
    )
    @app_commands.describe(
        premio="🎁 Prêmio do sorteio",
        descricao="📜 Descrição do prêmio",
        minutos="⏳ Tempo do sorteio em minutos",
        ganhadores="👥 Quantidade de ganhadores",
        canal="📢 Canal onde o sorteio será enviado",
        cargo="🧿 Cargo obrigatório para participar"
    )
    async def sorteio(
        self,
        interaction: discord.Interaction,
        premio: str,
        descricao: str,
        minutos: int,
        ganhadores: int,
        canal: discord.TextChannel,
        cargo: discord.Role = None
    ):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ Apenas administradores podem criar sorteios.",
                ephemeral=True
            )

        if minutos < 1:
            return await interaction.response.send_message(
                "❌ O tempo mínimo é 1 minuto.",
                ephemeral=True
            )

        if ganhadores < 1:
            return await interaction.response.send_message(
                "❌ O número de ganhadores precisa ser pelo menos 1.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        sorteio_id = interaction.id
        fim = datetime.utcnow() + timedelta(minutes=minutos)

        self.sorteios[sorteio_id] = {
            "premio": premio,
            "descricao": descricao,
            "ganhadores": ganhadores,
            "cargo_id": cargo.id if cargo else None,
            "participantes": set(),
            "fim": fim,
            "canal_id": canal.id,
            "mensagem_id": None,
            "finalizado": False,
            "cancelado": False,
            "vencedores": []
        }

        embed = self.criar_embed(sorteio_id)
        view = SorteioView(self, sorteio_id)

        msg = await canal.send(embed=embed, view=view)

        self.sorteios[sorteio_id]["mensagem_id"] = msg.id

        await interaction.followup.send(
            f"✅ Sorteio criado com sucesso em {canal.mention}.",
            ephemeral=True
        )

        asyncio.create_task(self.timer_sorteio(sorteio_id, minutos))

    def criar_embed(self, sorteio_id, cancelado=False, finalizado=False):
        data = self.sorteios[sorteio_id]

        requisito = f"<@&{data['cargo_id']}>" if data["cargo_id"] else "Nenhum"
        participantes = len(data["participantes"])

        status = "🩸 **Status:** Ativo"

        if cancelado:
            status = "❌ **Status:** Cancelado"
        elif finalizado:
            status = "🏁 **Status:** Finalizado"

        embed = discord.Embed(
            title="🩸 SORTEIO AMALDIÇOADO",
            description=(
                "Uma barreira foi erguida dentro do domínio da **Família Sant’s**.\n"
                "A energia amaldiçoada escolherá seus próximos portadores.\n\n"
                f"🎁 **Prêmio:** {data['premio']}\n"
                f"📜 **Descrição:** {data['descricao']}\n"
                f"👥 **Ganhadores:** {data['ganhadores']}\n"
                f"🎟️ **Participantes:** {participantes}\n"
                f"🧿 **Requisito:** {requisito}\n"
                f"⏳ **Termina:** <t:{int(data['fim'].timestamp())}:R>\n\n"
                "Clique em **Participar** para entrar no ritual.\n\n"
                f"{status}"
            ),
            color=COR_JUJUTSU
        )

        if GIF_SORTEIO and GIF_SORTEIO != "COLOQUE_AQUI_O_LINK_DO_SEU_BANNER":
            embed.set_image(url=GIF_SORTEIO)

        embed.set_footer(text="Família Sant’s • Sorteio Amaldiçoado")

        return embed

    async def atualizar_mensagem(self, sorteio_id, cancelado=False, finalizado=False):
        data = self.sorteios.get(sorteio_id)

        if not data:
            return

        canal = self.bot.get_channel(data["canal_id"])

        if not canal:
            return

        try:
            msg = await canal.fetch_message(data["mensagem_id"])
            embed = self.criar_embed(
                sorteio_id,
                cancelado=cancelado,
                finalizado=finalizado
            )
            await msg.edit(embed=embed)
        except Exception:
            pass

    async def timer_sorteio(self, sorteio_id, minutos):
        await asyncio.sleep(minutos * 60)

        data = self.sorteios.get(sorteio_id)

        if not data:
            return

        if data["finalizado"] or data["cancelado"]:
            return

        await self.finalizar_sorteio(sorteio_id)

    async def finalizar_sorteio(self, sorteio_id, manual=False):
        data = self.sorteios.get(sorteio_id)

        if not data:
            return

        if data["finalizado"]:
            return

        data["finalizado"] = True

        canal = self.bot.get_channel(data["canal_id"])

        if not canal:
            return

        participantes = list(data["participantes"])

        if len(participantes) < data["ganhadores"]:
            await canal.send(
                f"❌ O sorteio **{data['premio']}** foi encerrado, mas não teve participantes suficientes."
            )

            await self.atualizar_mensagem(sorteio_id, finalizado=True)
            return

        vencedores = random.sample(participantes, data["ganhadores"])

        data["vencedores"] = vencedores

        texto_vencedores = "\n".join([f"🏆 <@{v}>" for v in vencedores])

        embed = discord.Embed(
            title="🏆 O RITUAL FOI CONCLUÍDO",
            description=(
                f"🎁 **Prêmio:** {data['premio']}\n"
                f"📜 **Descrição:** {data['descricao']}\n\n"
                f"**Vencedores:**\n{texto_vencedores}\n\n"
                "A energia amaldiçoada escolheu seus portadores."
            ),
            color=COR_JUJUTSU
        )

        embed.set_footer(text="Família Sant’s • Resultado do Sorteio")

        await canal.send(embed=embed)

        await self.atualizar_mensagem(sorteio_id, finalizado=True)

    async def reroll_sorteio(self, sorteio_id):
        data = self.sorteios.get(sorteio_id)

        if not data:
            return "❌ Sorteio não encontrado."

        participantes = list(data["participantes"])

        if len(participantes) < data["ganhadores"]:
            return "❌ Não há participantes suficientes para fazer reroll."

        novos = random.sample(participantes, data["ganhadores"])

        data["vencedores"] = novos

        canal = self.bot.get_channel(data["canal_id"])

        texto = "\n".join([f"🔄 <@{v}>" for v in novos])

        embed = discord.Embed(
            title="🔄 REROLL DO SORTEIO",
            description=(
                f"🎁 **Prêmio:** {data['premio']}\n"
                f"📜 **Descrição:** {data['descricao']}\n\n"
                f"**Novos vencedores:**\n{texto}"
            ),
            color=COR_JUJUTSU
        )

        embed.set_footer(text="Família Sant’s • Reroll Amaldiçoado")

        if canal:
            await canal.send(embed=embed)

        return "🔄 Reroll realizado com sucesso."


async def setup(bot):
    await bot.add_cog(Sorteios(bot))