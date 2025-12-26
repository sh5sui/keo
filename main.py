import discord
from discord.ext import commands
import aiohttp
import asyncio
from discord import app_commands
from discord import guild
from dotenv import load_dotenv
import os

load_dotenv()

intents = discord.Intents.default()
intents.typing = False
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix=";", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} online')
    await bot.tree.sync()

@bot.tree.command(name="invite", description="Get keo's invite link")
async def name(interaction: discord.Interaction):

    await interaction.response.send_message("https://discord.com/oauth2/authorize?client_id=1454097190548148256&permissions=8&integration_type=0&scope=bot")

Token = os.getenv("Token")
bot.run(Token)