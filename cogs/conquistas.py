import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from PIL import Image, ImageDraw, ImageFont
import io

DB_FILE = "dados_conquistas.json"
BANNER_BASE = "assets/banner_base_conquistas.png"

STAFF_ROLE_ID = 1480349452744265759

CONQUISTAS = {
    1: "Desperto",
    2: "Sensitivo",
    3: "Iniciado",
    4: "Aprendiz Amaldiçoado",
    5: "Combatente",
    6: "Executor de Maldições",
    7: "Manipulador de Energia",
    8: "Usuário de Técnica",
    9: "Feiticeiro Grau 2",
    10: "Feiticeiro Grau 1",
    11: "Grau Especial",
    12: "Portador de Domínio",
    13: "Expansão de Domínio"
}


def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def is_staff(member: discord.Member):
    return any(role.id == STAFF_ROLE_ID for role in member.roles)


async def criar_banner(membro, conquistas_user):
    base = Image.open(BANNER_BASE).convert("RGBA")
    draw = ImageDraw.Draw(base)

    try:
        fonte_nome = ImageFont.truetype("arialbd.ttf", 42)
        fonte_id = ImageFont.truetype("arial.ttf", 24)
    except:
        fonte_nome = ImageFont.load_default()
        fonte_id = ImageFont.load_default()

    # Nome
    draw.text(
        (450, 250),
        membro.display_name,
        font=fonte_nome,
        fill=(210, 120, 255)
    )

    # ID
    draw.text(
        (450, 300),
        f"ID: {membro.id}",
        font=fonte_id,
        fill=(220, 220, 220)
    )

    # Avatar
    try:
        avatar_bytes = await membro.display_avatar.replace(size=256).read()
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize((150, 150))

        mask = Image.new("L", (150, 150), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, 150, 150), fill=255)

        base.paste(avatar, (220, 205), mask)
    except:
        pass

    # Marcação das conquistas desbloqueadas
    start_x = 70
    y = 355
    gap = 101

    for i in range(1, 14):
        x = start_x + (i - 1) * gap

        if i in conquistas_user:
            draw.ellipse(
                (x, y, x + 70, y + 70),
                outline=(210, 90, 255),
                width=5
            )
        else:
            draw.ellipse(
                (x, y, x + 70, y + 70),
                outline=(70, 70, 80),
                width=3
            )

    buffer = io.BytesIO()
    base.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


class Conquistas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="addconquista", description="Adicionar conquista")
    async def addconquista(self, interaction: discord.Interaction, membro: discord.Member, conquista_id: int):
        if not is_staff(interaction.user):
            await interaction.response.send_message("❌ Apenas staff pode usar.", ephemeral=True)
            return

        if conquista_id not in CONQUISTAS:
            await interaction.response.send_message("❌ ID inválido. Use de 1 a 13.", ephemeral=True)
            return

        db = load_db()
        user_id = str(membro.id)

        if user_id not in db:
            db[user_id] = []

        if conquista_id not in db[user_id]:
            db[user_id].append(conquista_id)

        db[user_id].sort()
        save_db(db)

        await interaction.response.send_message(
            f"✅ {membro.mention} recebeu **{CONQUISTAS[conquista_id]}**"
        )

    @app_commands.command(name="removerconquista", description="Remover conquista")
    async def removerconquista(self, interaction: discord.Interaction, membro: discord.Member, conquista_id: int):
        if not is_staff(interaction.user):
            await interaction.response.send_message("❌ Apenas staff pode usar.", ephemeral=True)
            return

        db = load_db()
        user_id = str(membro.id)

        if user_id in db and conquista_id in db[user_id]:
            db[user_id].remove(conquista_id)
            save_db(db)
            await interaction.response.send_message(
                f"❌ {CONQUISTAS.get(conquista_id, 'Conquista')} removida de {membro.mention}"
            )
        else:
            await interaction.response.send_message(
                "⚠️ Esse membro não possui essa conquista.",
                ephemeral=True
            )

    @app_commands.command(name="conquistas", description="Ver banner de conquistas")
    async def conquistas(self, interaction: discord.Interaction, membro: discord.Member = None):
        await interaction.response.defer()

        membro = membro or interaction.user

        db = load_db()
        user_id = str(membro.id)

        conquistas_user = db.get(user_id, [])

        banner = await criar_banner(membro, conquistas_user)

        file = discord.File(
            banner,
            filename=f"conquistas_{membro.id}.png"
        )

        await interaction.followup.send(file=file)


async def setup(bot):
    await bot.add_cog(Conquistas(bot))