import os
import discord
import asyncio
from discord.ext import commands

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")

async def main():
    async with bot:
        print("Iniciando bot...")
        await bot.load_extension("cogs.tickets")
        print("Cog tickets carregada.")
        token = os.getenv("DISCORD_TOKEN")
        print("Token encontrado:", bool(token))
        await bot.start(token)

asyncio.run(main())