import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io

DB_FILE = "dados_conquistas.json"
BANNER_BASE = "assets/banner_base_conquistas.png"
PASTA_ICONES = "assets/conquistas"
LOCK_ICON = "assets/lock.png"

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


def get_font(nome="arial.ttf", tamanho=30):
    try:
        return ImageFont.truetype(nome, tamanho)
    except Exception:
        return ImageFont.load_default()


def centralizar_texto(draw, texto, x1, y1, x2, y2, fonte, fill):
    bbox = draw.textbbox((0, 0), texto, font=fonte)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = x1 + ((x2 - x1) - w) // 2
    y = y1 + ((y2 - y1) - h) // 2
    draw.text((x, y), texto, font=fonte, fill=fill)


async def criar_banner(membro, conquistas_user):
    base = Image.open(BANNER_BASE).convert("RGBA")
    draw = ImageDraw.Draw(base, "RGBA")

    fonte_nome = get_font("arialbd.ttf", 56)
    fonte_id = get_font("arial.ttf", 30)
    fonte_secao = get_font("arialbd.ttf", 38)
    fonte_numero = get_font("arialbd.ttf", 34)
    fonte_pequena = get_font("arial.ttf", 24)

    # ===== NOME / ID =====
    nome = membro.display_name[:18]
    centralizar_texto(draw, "FEITICEIRO:", 650, 545, 910, 595, fonte_id, (225, 225, 235, 255))
    draw.text((920, 535), nome, font=fonte_nome, fill=(210, 90, 255, 255))
    centralizar_texto(draw, f"ID: {membro.id}", 650, 600, 1390, 650, fonte_id, (220, 220, 225, 255))

    # ===== AVATAR =====
    try:
        avatar_bytes = await membro.display_avatar.replace(size=256).read()
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize((140, 140), Image.LANCZOS)

        mask = Image.new("L", (140, 140), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, 140, 140), fill=255)

        # moldura/avatar no centro do painel
        base.paste(avatar, (625, 526), mask)
        draw.ellipse((618, 519, 772, 673), outline=(190, 75, 255, 255), width=5)
    except Exception:
        pass

    # ===== TÍTULO DAS CONQUISTAS =====
    progresso = len(conquistas_user)
    centralizar_texto(
        draw,
        f"CONQUISTAS DESBLOQUEADAS  {progresso}/13",
        0, 710, 2048, 770,
        fonte_secao,
        (210, 80, 255, 255)
    )

    # ===== POSIÇÕES DOS 13 ÍCONES =====
    # Coordenadas feitas para o banner 2048x1093.
    centros_x = [105, 262, 419, 576, 733, 890, 1047, 1204, 1361, 1518, 1675, 1832, 1989]
    y_numero = 780
    y_icon = 835
    y_nome = 980

    for i, cx in enumerate(centros_x, start=1):
        desbloqueada = i in conquistas_user

        # número em cima
        centralizar_texto(draw, str(i), cx - 45, y_numero, cx + 45, y_numero + 45, fonte_numero, (245, 235, 255, 255))

        # brilho atrás dos desbloqueados
        if desbloqueada:
            glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow, "RGBA")
            gd.ellipse((cx - 70, y_icon - 25, cx + 70, y_icon + 115), fill=(170, 45, 255, 90))
            glow = glow.filter(ImageFilter.GaussianBlur(18))
            base.alpha_composite(glow)
            icon_path = f"{PASTA_ICONES}/{i}.png"
        else:
            icon_path = LOCK_ICON

        try:
            icon = Image.open(icon_path).convert("RGBA").resize((110, 110), Image.LANCZOS)
            base.paste(icon, (cx - 55, y_icon), icon)
        except Exception:
            pass

        # nome/??? embaixo
        if desbloqueada:
            nome_conq = CONQUISTAS[i].split()[0].upper()
            cor_nome = (210, 120, 255, 255)
        else:
            nome_conq = "???"
            cor_nome = (170, 75, 210, 255)

        centralizar_texto(draw, nome_conq, cx - 65, y_nome, cx + 65, y_nome + 35, fonte_pequena, cor_nome)

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
        db.setdefault(user_id, [])

        if conquista_id not in db[user_id]:
            db[user_id].append(conquista_id)
            db[user_id].sort()
            save_db(db)
            await interaction.response.send_message(f"✅ {membro.mention} recebeu **{CONQUISTAS[conquista_id]}**")
        else:
            await interaction.response.send_message("⚠️ Esse membro já possui essa conquista.", ephemeral=True)

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
            await interaction.response.send_message(f"❌ {CONQUISTAS.get(conquista_id, 'Conquista')} removida de {membro.mention}")
        else:
            await interaction.response.send_message("⚠️ Esse membro não possui essa conquista.", ephemeral=True)

    @app_commands.command(name="conquistas", description="Ver banner de conquistas")
    async def conquistas(self, interaction: discord.Interaction, membro: discord.Member = None):
        await interaction.response.defer()
        membro = membro or interaction.user

        db = load_db()
        conquistas_user = db.get(str(membro.id), [])
        banner = await criar_banner(membro, conquistas_user)

        file = discord.File(banner, filename=f"conquistas_{membro.id}.png")
        await interaction.followup.send(file=file)


async def setup(bot):
    await bot.add_cog(Conquistas(bot))
