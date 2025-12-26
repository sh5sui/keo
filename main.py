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
async def invite(interaction: discord.Interaction):

    await interaction.response.send_message("https://discord.com/oauth2/authorize?client_id=1454097190548148256&permissions=8&integration_type=0&scope=bot")

@bot.tree.command(name="license", description="Shows the license of distribution for keo")
async def license(interaction: discord.Interaction):

    await interaction.response.send_message("Keo is available for modification BUT copy's of keo's code modified by users must NOT be distributed, sold, or for public use without the written consent of it's direct owner. If you violate any of these statues you may be subject to legal action being taken against you for copyright infringments. You can read more at https://github.com/sh5sui/keo/blob/main/LICENSE/")

@bot.tree.command(name="ticket", description="Open a ticket with a specified reason")
async def ticket(interaction: discord.Interaction, reason: str = None):

    guild = interaction.guild

    embed = discord.Embed(title="Ticket", color=discord.Color.blue())
    embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="", value="Please wait for a member of staff to respond to your ticket. While your waiting, feel free to describe your issue in more detail.")

    category = discord.utils.get(guild.categories, name="tickets")

    ticket = await guild.create_text_channel(
        name=f"ticket-{reason}",
        category=category
    )

    await ticket.send(
        f"Welcome {interaction.user.mention} ||@here||\n",
        embed=embed
    )

    await interaction.response.send_message(f"Your ticket has been created, {ticket.mention}", ephemeral=True)

Token = os.getenv("Token")
bot.run(Token)