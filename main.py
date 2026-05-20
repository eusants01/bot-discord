import os
import discord
import asyncio
from discord.ext import commands, tasks
from dotenv import load_dotenv

from utils.database import conectar_db
from utils.db import criar_tabelas

load_dotenv()

# ==================================================
# 🎰 CONFIGURAÇÕES DO CASSINO CUPHEAD
# ==================================================

GUILD_ID = 1480334256763961465

COR_CUPHEAD = 0xC48A3A

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# Evita duplicar eventos após reconnect
bot.iniciado = False


# ==================================================
# 🎭 STATUS ROTATIVO CUPHEAD
# ==================================================

status_list = [
    "🎰 Cassino Retrô aberto...",
    "☕ Cuphead está apostando tudo...",
    "🎲 A roleta está girando...",
    "👑 Apenas os sortudos vencem...",
    "💰 Fazendo apostas no cassino...",
    "🔥 O diabo está observando...",
]


@tasks.loop(seconds=15)
async def trocar_status():
    status = status_list[
        trocar_status.current_loop % len(status_list)
    ]

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(name=status)
    )


# ==================================================
# 📦 CARREGADOR DE COGS
# ==================================================

async def carregar_cog(nome: str):
    try:
        await bot.load_extension(nome)

        print(f"✅ {nome} carregado com sucesso")

    except Exception as e:
        print(
            f"❌ Erro ao carregar {nome}: "
            f"{type(e).__name__}: {e}"
        )


# ==================================================
# 🎬 BOT ONLINE
# ==================================================

@bot.event
async def on_ready():

    # Evita duplicação
    if bot.iniciado:
        return

    bot.iniciado = True

    print("\n" + "=" * 50)
    print(f"🎰 BOT ONLINE COMO {bot.user}")
    print("=" * 50)

    guild = discord.Object(id=GUILD_ID)

    # Lista comandos antes do sync
    comandos = [
        cmd.name
        for cmd in bot.tree.get_commands()
    ]

    print(f"📌 {len(comandos)} comando(s) carregado(s):")

    for cmd in comandos:
        print(f"   ➜ /{cmd}")

    # Sync
    bot.tree.copy_global_to(guild=guild)

    synced = await bot.tree.sync(guild=guild)

    print("\n🎲 Slash commands sincronizados:")

    for cmd in synced:
        print(f"   ✅ /{cmd.name}")

    print("=" * 50)

    # Status rotativo
    if not trocar_status.is_running():
        trocar_status.start()
        print("🎭 Status rotativo iniciado")


# ==================================================
# 🚀 MAIN
# ==================================================

async def main():

    async with bot:

        print("\n🎬 Iniciando Cassino Cuphead...\n")

        # ==================================================
        # 🗄️ POSTGRESQL
        # ==================================================

        try:
            await conectar_db()

            print("✅ PostgreSQL conectado")
            print("🎰 Banco do cassino iniciado")

        except Exception as e:

            print(
                f"❌ Erro ao conectar PostgreSQL: "
                f"{type(e).__name__}: {e}"
            )

            return

        # ==================================================
        # 🏆 CONQUISTAS ANTIGAS, PORÉM DESATIVDAS ATÉ ENTÃO.
        # ==================================================

        try:
            criar_tabelas()

            print("✅ Banco de conquistas iniciado")

        except Exception as e:

            print(
                f"⚠️ Erro no banco de conquistas: "
                f"{type(e).__name__}: {e}"
            )

        # ==================================================
        # 📦 COGS
        # ==================================================

        cogs = [
            "cogs.tickets",
            "cogs.parceiros",
            "cogs.notificacoes",
            "cogs.sorteios",
            "cogs.moderacao",
        ]

        # Caso ainda use conquistas:
        # cogs.append("cogs.conquistas")

        print("\n📦 Carregando sistemas...\n")

        for cog in cogs:
            await carregar_cog(cog)

        print("\n✅ Todos os sistemas foram carregados")
        print("=" * 50)

        # ==================================================
        # 🔑 TOKEN
        # ==================================================

        token = os.getenv("DISCORD_TOKEN")

        if not token:
            raise RuntimeError(
                "DISCORD_TOKEN não encontrada."
            )

        print("🔑 Token encontrado")
        print("🎰 Abrindo o cassino...\n")

        await bot.start(token)


# ==================================================
# 🎯 START
# ==================================================

if __name__ == "__main__":
    asyncio.run(main())