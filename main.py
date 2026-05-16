import os
import discord
import asyncio
from discord.ext import commands, tasks
from dotenv import load_dotenv

from utils.database import conectar_db
from utils.db import criar_tabelas

load_dotenv()

# =========================
# CONFIGURAÇÕES
# =========================

GUILD_ID = 1480334256763961465

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

status_list = [
    "🩸 Em expansão de domínio...",
    "🔮 Julgando maldições...",
    "⚔️ Apenas os fortes sobrevivem",
    "👁️ Observando os fracos...",
    "🔥 Despertando energia amaldiçoada",
    "💀 Você está dentro do domínio...",
]


# =========================
# STATUS ROTATIVO
# =========================

@tasks.loop(seconds=15)
async def trocar_status():
    status = status_list[trocar_status.current_loop % len(status_list)]

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(name=status)
    )


# =========================
# CARREGAR COGS
# =========================

async def carregar_cog(nome):
    try:
        await bot.load_extension(nome)
        print(f"✅ {nome} carregado")
    except Exception as e:
        print(f"❌ Erro ao carregar {nome}: {type(e).__name__}: {e}")


# =========================
# BOT ONLINE
# =========================

@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")

    # Banco antigo das conquistas
    criar_tabelas()
    print("✅ Banco de conquistas iniciado")

    guild = discord.Object(id=GUILD_ID)

    comandos = [cmd.name for cmd in bot.tree.get_commands()]
    print("📌 Comandos carregados antes do sync:", comandos)

    bot.tree.clear_commands(guild=guild)
    bot.tree.copy_global_to(guild=guild)

    synced = await bot.tree.sync(guild=guild)

    print(f"✅ {len(synced)} slash commands sincronizados no servidor:")
    for cmd in synced:
        print(f" - /{cmd.name}")

    if not trocar_status.is_running():
        trocar_status.start()


# =========================
# MAIN
# =========================

async def main():
    async with bot:
        print("🚀 Iniciando bot...")

        # PostgreSQL Railway
        await conectar_db()
        print("✅ PostgreSQL iniciado")

        await carregar_cog("cogs.tickets")
        await carregar_cog("cogs.parceiros")
        await carregar_cog("cogs.conquistas")
        await carregar_cog("cogs.notificacoes")
        await carregar_cog("cogs.sorteios")
        await carregar_cog("cogs.moderacao")

        token = os.getenv("DISCORD_TOKEN")
        print("Token encontrado:", bool(token))

        if not token:
            raise RuntimeError("DISCORD_TOKEN não encontrado nas variáveis de ambiente.")

        await bot.start(token)


asyncio.run(main())