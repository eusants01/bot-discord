import os
import discord
import asyncio
from discord.ext import commands, tasks
from dotenv import load_dotenv

from utils.database import conectar_db
from utils.db import criar_tabelas

load_dotenv()

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

bot.iniciado = False

status_list = [
    "🌌 Explorando novos universos...",
    "🪐 Sistemas orbitando normalmente...",
    "📡 Recebendo sinais da galáxia...",
    "✨ Sincronizando estrelas...",
    "💜 Desenvolvido por Sant's",
    "⚡ Núcleo Nebularis ativo...",
    "🚀 Preparando novas funcionalidades...",
    "🛰️ Monitorando o servidor...",
    "💫 Expandindo o universo...",
]


@tasks.loop(seconds=5)
async def trocar_status():
    status = status_list[
        trocar_status.current_loop % len(status_list)
    ]

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(name=status)
    )

async def carregar_cog(nome: str):
    try:
        await bot.load_extension(nome)

        print(f"✅ {nome} carregado com sucesso")

    except Exception as e:
        print(
            f"❌ Erro ao carregar {nome}: "
            f"{type(e).__name__}: {e}"
        )

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

    if not trocar_status.is_running():
        trocar_status.start()
        print("🎭 Status rotativo iniciado")

async def main():

    async with bot:

        print("\n🎬 Iniciando Cassino Cuphead...\n")

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

        try:
            criar_tabelas()

            print("✅ Banco de conquistas iniciado")

        except Exception as e:

            print(
                f"⚠️ Erro no banco de conquistas: "
                f"{type(e).__name__}: {e}"
            )

        cogs = [
            "cogs.tickets",
            "cogs.enquetes",
            "cogs.notificacoes",
            "cogs.sorteios",
            "cogs.moderacao",
        ]

        print("\n📦 Carregando sistemas...\n")

        for cog in cogs:
            await carregar_cog(cog)

        print("\n✅ Todos os sistemas foram carregados")
        print("=" * 50)

        token = os.getenv("DISCORD_TOKEN")

        if not token:
            raise RuntimeError(
                "DISCORD_TOKEN não encontrada."
            )

        print("🔑 Token encontrado")
        print("🎰 Abrindo o cassino...\n")

        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())