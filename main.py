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

    GUILD_ID = 1480334256763961465
    guild = discord.Object(id=GUILD_ID)

    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)

    print("✅ Slash commands sincronizados no servidor")

    if not trocar_status.is_running():
        trocar_status.start()

async def main():
    async with bot:
        print("Iniciando bot...")

        await bot.load_extension("cogs.tickets")
        await bot.load_extension("cogs.parceiros")
        await bot.load_extension("cogs.conquistas")
        await bot.load_extension("cogs.notificacoes")

        token = os.getenv("DISCORD_TOKEN")
        print("Token encontrado:", bool(token))

        await bot.start(token)

asyncio.run(main())