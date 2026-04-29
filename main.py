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

    GUILD_ID = 1480334256763961465  # coloque aqui o ID do seu servidor

    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print("✅ Slash commands sincronizados no servidor")

    if not trocar_status.is_running():
        trocar_status.start()


async def main():
    async with bot:
        print("Iniciando bot...")

        # 🔥 carregando cogs
        await bot.load_extension("cogs.tickets")
        await bot.load_extension("cogs.parceiros")
        await bot.load_extension("cogs.conquistas")

        token = os.getenv("DISCORD_TOKEN")
        print("Token encontrado:", bool(token))

        await bot.start(token)