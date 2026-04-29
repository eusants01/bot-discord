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

STAFF_ROLE_IDS = [
    1480349452744265759
]

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
    return any(role.id in STAFF_ROLE_IDS for role in member.roles)


def get_font(bold=False, tamanho=30):
    fontes = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for fonte in fontes:
        try:
            return ImageFont.truetype(fonte, tamanho)
        except Exception:
            pass

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

    w, h = base.size

    fonte_nome = get_font(True, int(w * 0.028))
    fonte_id = get_font(False, int(w * 0.015))
    fonte_nome_conq = get_font(True, int(w * 0.012))

    nome = membro.display_name[:18]

    # ===== NOME / ID =====
    # cobre apenas o texto antigo dentro da moldura original
    draw.rounded_rectangle(
        (int(w * 0.365), int(h * 0.455), int(w * 0.660), int(h * 0.525)),
        radius=10,
        fill=(5, 3, 12, 150)
    )

    draw.text(
        (int(w * 0.375), int(h * 0.465)),
        "FEITICEIRO:",
        font=fonte_id,
        fill=(230, 230, 235, 255)
    )

    draw.text(
        (int(w * 0.535), int(h * 0.452)),
        nome,
        font=fonte_nome,
        fill=(210, 90, 255, 255)
    )

    draw.text(
        (int(w * 0.410), int(h * 0.505)),
        f"ID: {membro.id}",
        font=fonte_id,
        fill=(220, 220, 225, 255)
    )

    # ===== ÍCONES =====
    centros_x = [int(w * p) for p in [
        0.052, 0.128, 0.204, 0.280, 0.356, 0.432, 0.508,
        0.584, 0.660, 0.736, 0.812, 0.888, 0.964
    ]]

    y_icon = int(h * 0.705)
    y_nome = int(h * 0.865)
    icon_size = int(w * 0.060)

    for i, cx in enumerate(centros_x, start=1):
        desbloqueada = i in conquistas_user

        if desbloqueada:
            icon_path = f"{PASTA_ICONES}/{i}.png"

            glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow, "RGBA")
            gd.ellipse(
                (
                    cx - int(icon_size * 0.75),
                    y_icon - int(icon_size * 0.25),
                    cx + int(icon_size * 0.75),
                    y_icon + int(icon_size * 1.25)
                ),
                fill=(170, 45, 255, 70)
            )
            glow = glow.filter(ImageFilter.GaussianBlur(16))
            base.alpha_composite(glow)

            nome_conq = CONQUISTAS[i].split()[0].upper()
            cor_nome = (210, 120, 255, 255)
        else:
            icon_path = LOCK_ICON
            nome_conq = "???"
            cor_nome = (170, 75, 210, 255)

        try:
            icon = Image.open(icon_path).convert("RGBA")
            icon = icon.resize((icon_size, icon_size), Image.LANCZOS)
            base.paste(icon, (cx - icon_size // 2, y_icon), icon)
        except Exception as e:
            print(f"Erro ao carregar ícone {i}: {e}")

        centralizar_texto(
            draw,
            nome_conq,
            cx - int(w * 0.040),
            y_nome,
            cx + int(w * 0.040),
            y_nome + int(h * 0.035),
            fonte_nome_conq,
            cor_nome
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
        db.setdefault(user_id, [])

        if conquista_id not in db[user_id]:
            db[user_id].append(conquista_id)
            db[user_id].sort()
            save_db(db)

            await interaction.response.send_message(
                f"✅ {membro.mention} recebeu **{CONQUISTAS[conquista_id]}**"
            )
        else:
            await interaction.response.send_message(
                "⚠️ Esse membro já possui essa conquista.",
                ephemeral=True
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
        conquistas_user = db.get(str(membro.id), [])

        banner = await criar_banner(membro, conquistas_user)

        file = discord.File(
            banner,
            filename=f"conquistas_{membro.id}.png"
        )

        await interaction.followup.send(file=file)


async def setup(bot):
    await bot.add_cog(Conquistas(bot))