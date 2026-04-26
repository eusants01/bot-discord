import os
import discord
import asyncio
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.guilds = True
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
        atividade = discord.Game(name=status)
        await bot.change_presence(
            status=discord.Status.online,
            activity=atividade
        )
        await asyncio.sleep(15)

@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")

    if not trocar_status.is_running():
        trocar_status.start()

async def main():
    async with bot:
        print("Iniciando bot...")
        await bot.load_extension("cogs.tickets")

        token = os.getenv("DISCORD_TOKEN")
        print("DISCORD_TOKEN:", token)
        print("Token encontrado:", bool(token))

        await bot.start(token)

asyncio.run(main())