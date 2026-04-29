import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io

DB_FILE = "dados_conquistas.json"

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
    largura, altura = 1600, 700

    img = Image.new("RGB", (largura, altura), (8, 5, 18))
    draw = ImageDraw.Draw(img)

    for y in range(altura):
        r = int(10 + y * 0.03)
        g = int(5 + y * 0.01)
        b = int(25 + y * 0.05)
        draw.line((0, y, largura, y), fill=(r, g, b))

    glow = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)

    gdraw.ellipse((-250, -180, 500, 500), fill=(80, 40, 255, 90))
    gdraw.ellipse((1150, -150, 1850, 520), fill=(255, 30, 80, 80))
    gdraw.ellipse((450, 250, 1150, 900), fill=(140, 40, 255, 45))

    glow = glow.filter(ImageFilter.GaussianBlur(80))
    img = Image.alpha_composite(img.convert("RGBA"), glow)
    draw = ImageDraw.Draw(img)

    try:
        fonte_titulo = ImageFont.truetype("arialbd.ttf", 78)
        fonte_media = ImageFont.truetype("arialbd.ttf", 34)
        fonte_pequena = ImageFont.truetype("arial.ttf", 22)
        fonte_numero = ImageFont.truetype("arialbd.ttf", 26)
    except:
        fonte_titulo = ImageFont.load_default()
        fonte_media = ImageFont.load_default()
        fonte_pequena = ImageFont.load_default()
        fonte_numero = ImageFont.load_default()

    draw.rounded_rectangle(
        (25, 25, largura - 25, altura - 25),
        radius=28,
        outline=(150, 65, 255),
        width=4
    )

    draw.text((430, 55), "CAMINHO DO FEITICEIRO", font=fonte_titulo, fill=(235, 210, 255))
    draw.text((610, 135), "FAMÍLIA SANT’S • JUJUTSU", font=fonte_pequena, fill=(180, 100, 255))

    try:
        avatar_bytes = await membro.display_avatar.replace(size=256).read()
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize((170, 170))

        mask = Image.new("L", (170, 170), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, 170, 170), fill=255)

        img.paste(avatar, (90, 90), mask)
        draw.ellipse((86, 86, 264, 264), outline=(170, 80, 255), width=5)
    except Exception:
        pass

    draw.text((300, 175), f"FEITICEIRO: {membro.display_name}", font=fonte_media, fill=(255, 255, 255))
    draw.text((300, 220), f"ID: {membro.id}", font=fonte_pequena, fill=(185, 185, 200))

    progresso = len(conquistas_user)
    total = 13

    draw.text((300, 265), f"CONQUISTAS DESBLOQUEADAS: {progresso}/{total}", font=fonte_media, fill=(190, 90, 255))

    barra_x, barra_y = 300, 320
    barra_w, barra_h = 720, 24

    draw.rounded_rectangle(
        (barra_x, barra_y, barra_x + barra_w, barra_y + barra_h),
        radius=12,
        fill=(28, 22, 40)
    )

    progresso_w = int((progresso / total) * barra_w)

    if progresso_w > 0:
        draw.rounded_rectangle(
            (barra_x, barra_y, barra_x + progresso_w, barra_y + barra_h),
            radius=12,
            fill=(160, 60, 255)
        )

    draw.text(
        (1080, 205),
        "“A maldição testa.\nO feiticeiro evolui.\nO domínio se expande.”",
        font=fonte_media,
        fill=(230, 210, 255),
        spacing=10
    )

    start_x = 70
    start_y = 415
    box_w = 108
    box_h = 170
    gap = 9

    simbolos = {
        1: "●",
        2: "◉",
        3: "👁",
        4: "札",
        5: "⚔",
        6: "☠",
        7: "🌀",
        8: "✦",
        9: "弐",
        10: "壱",
        11: "鬼",
        12: "領",
        13: "域"
    }

    for i in range(1, 14):
        x = start_x + (i - 1) * (box_w + gap)
        y = start_y

        desbloqueada = i in conquistas_user

        if desbloqueada:
            borda = (185, 75, 255)
            fundo = (45, 15, 75)
            texto = (255, 255, 255)
            simbolo_cor = (235, 190, 255)
            nome = CONQUISTAS[i]
        else:
            borda = (70, 70, 85)
            fundo = (20, 20, 28)
            texto = (120, 120, 130)
            simbolo_cor = (90, 90, 100)
            nome = "???"

        if desbloqueada:
            draw.rounded_rectangle(
                (x - 4, y - 4, x + box_w + 4, y + box_h + 4),
                radius=18,
                outline=(120, 45, 255),
                width=2
            )

        draw.rounded_rectangle(
            (x, y, x + box_w, y + box_h),
            radius=16,
            fill=fundo,
            outline=borda,
            width=3
        )

        draw.text((x + 38, y + 10), f"{i:02}", font=fonte_numero, fill=(255, 255, 255))

        if desbloqueada:
            draw.text((x + 35, y + 52), simbolos[i], font=fonte_media, fill=simbolo_cor)
        else:
            draw.text((x + 36, y + 52), "🔒", font=fonte_media, fill=simbolo_cor)

        nome_curto = nome.replace(" ", "\n", 1)
        draw.text((x + 8, y + 112), nome_curto[:18], font=fonte_pequena, fill=texto)

    draw.text(
        (430, 630),
        "DO DESPERTAR À EXPANSÃO DE DOMÍNIO — SOMENTE OS MAIS FORTES SOBREVIVEM.",
        font=fonte_pequena,
        fill=(190, 100, 255)
    )

    buffer = io.BytesIO()
    img.convert("RGB").save(buffer, format="PNG")
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