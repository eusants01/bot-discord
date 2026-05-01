import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io

from utils.db import conn, cursor

COR_JUJUTSU = 0x7B2CFF

# 🏆 CONQUISTAS (exemplo — pode expandir)
CONQUISTAS = {
    "voz_da_sombra": {"emoji": "🔒", "nome": "???"},
    "rei_das_maldicoes": {"emoji": "👑", "nome": "Rei das Maldições"}
}

# 🔓 LIBERAR CONQUISTA
async def liberar_conquista(bot, usuario, conquista_id):
    cursor.execute(
        "SELECT 1 FROM conquistas WHERE user_id=? AND conquista_id=?",
        (str(usuario.id), conquista_id)
    )
    if cursor.fetchone():
        return False

    cursor.execute(
        "INSERT INTO conquistas VALUES (?, ?, ?)",
        (str(usuario.id), conquista_id, datetime.now().strftime("%d/%m/%Y"))
    )
    conn.commit()
    return True

# 🔍 AUTOCOMPLETE
async def autocomplete_conquista(interaction, current):
    return [
        app_commands.Choice(name=f"{c['nome']} ({cid})", value=cid)
        for cid, c in CONQUISTAS.items()
        if current.lower() in cid.lower()
    ][:25]


class Conquistas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 🎁 DAR CONQUISTA
    @app_commands.command(name="darconquista", description="Dar conquista a um membro")
    @app_commands.autocomplete(conquista_id=autocomplete_conquista)
    async def darconquista(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        conquista_id: str
    ):
        if conquista_id not in CONQUISTAS:
            return await interaction.response.send_message("Conquista inválida.", ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Sem permissão.", ephemeral=True)

        ganhou = await liberar_conquista(self.bot, membro, conquista_id)

        if not ganhou:
            return await interaction.response.send_message("Já possui.", ephemeral=True)

        await interaction.response.send_message("✅ Conquista entregue.", ephemeral=True)

    # 🎴 PERFIL ANIME (ABSURDO FINAL)
    @app_commands.command(name="conquistas", description="Veja seu perfil de conquistas")
    async def conquistas(self, interaction: discord.Interaction):

        def fonte(t):
            try:
                return ImageFont.truetype("arial.ttf", t)
            except:
                return ImageFont.load_default()

        cursor.execute(
            "SELECT conquista_id FROM conquistas WHERE user_id=?",
            (str(interaction.user.id),)
        )

        dados = [cid for (cid,) in cursor.fetchall()]
        total = len(CONQUISTAS)
        conquistadas = len(dados)

        # 🎴 FUNDO
        base = Image.open("assets/perfil_jujutsu.png").convert("RGBA")
        base = base.resize((1000, 420))

        # 🌑 overlay escuro
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 140))
        base = Image.alpha_composite(base, overlay)

        draw = ImageDraw.Draw(base)

        # 🟪 painel
        draw.rounded_rectangle(
            (40, 40, 680, 380),
            radius=25,
            fill=(20, 20, 40, 220),
            outline=(123, 44, 255),
            width=3
        )

        # 👤 nome
        draw.text((70, 60), interaction.user.display_name, fill=(255,255,255), font=fonte(28))

        # 📊 progresso
        porcentagem = int((conquistadas / total) * 100) if total > 0 else 0

        draw.text(
            (70, 110),
            f"{conquistadas}/{total} conquistas",
            fill=(200,200,255),
            font=fonte(20)
        )

        # 🔳 barra fundo
        draw.rounded_rectangle((70, 150, 550, 180), 15, fill=(60,60,80))

        # 🟣 barra progresso
        progresso = int((conquistadas / total) * 480) if total > 0 else 0
        draw.rounded_rectangle((70, 150, 70+progresso, 180), 15, fill=(123,44,255))

        # 👑 título
        if porcentagem >= 80:
            titulo = "👑 Rei das Maldições"
            cor = (255,80,80)
        elif porcentagem >= 50:
            titulo = "🔥 Feiticeiro Avançado"
            cor = (255,180,60)
        else:
            titulo = "🌀 Feiticeiro Iniciante"
            cor = (180,180,255)

        draw.text((70, 210), titulo, fill=cor, font=fonte(22))

        # 🧍 avatar redondo
        avatar_bytes = await interaction.user.display_avatar.read()
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((120,120))

        mask = Image.new("L", (120,120), 0)
        m = ImageDraw.Draw(mask)
        m.ellipse((0,0,120,120), fill=255)

        base.paste(avatar, (760, 70), mask)

        # 🔮 glow
        glow = Image.new("RGBA", base.size, (0,0,0,0))
        g = ImageDraw.Draw(glow)
        g.ellipse((740, 50, 900, 230), outline=(123,44,255), width=5)
        glow = glow.filter(ImageFilter.GaussianBlur(8))

        base = Image.alpha_composite(base, glow)

        # 💾 salvar
        buffer = io.BytesIO()
        base.convert("RGB").save(buffer, "PNG")
        buffer.seek(0)

        await interaction.response.send_message(
            file=discord.File(buffer, "perfil.png"),
            ephemeral=True
        )

    # 🔑 CODIGO
    @app_commands.command(name="codigo", description="Resgatar código secreto")
    async def codigo(self, interaction: discord.Interaction, codigo: str):

        codigos = {
            "MAHORAGA": {"c": "voz_da_sombra", "limite": 1},
            "SUKUNAHEIAN": {"c": "rei_das_maldicoes", "limite": 5}
        }

        codigo = codigo.upper()

        if codigo not in codigos:
            return await interaction.response.send_message("❌ Código inválido.", ephemeral=True)

        user_id = str(interaction.user.id)

        cursor.execute("SELECT 1 FROM codigos WHERE codigo=? AND user_id=?", (codigo, user_id))
        if cursor.fetchone():
            return await interaction.response.send_message("Já usou.", ephemeral=True)

        cursor.execute("SELECT COUNT(*) FROM codigos WHERE codigo=?", (codigo,))
        usos = cursor.fetchone()[0]

        if usos >= codigos[codigo]["limite"]:
            return await interaction.response.send_message("Esgotado.", ephemeral=True)

        await liberar_conquista(self.bot, interaction.user, codigos[codigo]["c"])

        cursor.execute("INSERT INTO codigos VALUES (?, ?)", (codigo, user_id))
        conn.commit()

        await interaction.response.send_message("✅ Código aceito.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Conquistas(bot))