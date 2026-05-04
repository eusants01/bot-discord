import os
import discord
import asyncio
from discord.ext import commands, tasks
from utils.db import criar_tabelas

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = 1480334256763961465

status_list = [
    "🩸 Em expansão de domínio...",
    "🔮 Julgando maldições...",
    "⚔️ Apenas os fortes sobrevivem",
    "👁️ Observando os fracos...",
    "🔥 Despertando energia amaldiçoada",
    "💀 Você está dentro do domínio...",
]


@tasks.loop(seconds=15)
async def trocar_status():
    for status in status_list:
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game(name=status)
        )
        await asyncio.sleep(15)


@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")

    criar_tabelas()
    print("✅ Banco de conquistas iniciado")

    guild = discord.Object(id=GUILD_ID)

    comandos = [cmd.name for cmd in bot.tree.get_commands()]
    print("📌 Comandos carregados antes do sync:", comandos)

    # 🔥 Limpa comandos antigos do servidor
    bot.tree.clear_commands(guild=guild)

    # 🔥 Copia comandos atuais para o servidor
    bot.tree.copy_global_to(guild=guild)

    # 🔥 Sincroniza no servidor
    synced = await bot.tree.sync(guild=guild)

    print(f"✅ {len(synced)} slash commands sincronizados no servidor:")
    for cmd in synced:
        print(f" - /{cmd.name}")

    if not trocar_status.is_running():
        trocar_status.start()


async def carregar_cog(nome):
    try:
        await bot.load_extension(nome)
        print(f"✅ {nome} carregado")
    except Exception as e:
        print(f"❌ Erro ao carregar {nome}: {type(e).__name__}: {e}")


async def main():
    async with bot:
        print("Iniciando bot...")

        await carregar_cog("cogs.tickets")
        await carregar_cog("cogs.parceiros")
        await carregar_cog("cogs.conquistas")
        await carregar_cog("cogs.notificacoes")
        await bot.load_extension("cogs.sorteios")

        token = os.getenv("DISCORD_TOKEN")
        print("Token encontrado:", bool(token))

        if not token:
            raise RuntimeError("DISCORD_TOKEN não encontrado nas variáveis de ambiente.")

        await bot.start(token)


asyncio.run(main())