import discord
from discord.ext import commands
import aiohttp
import asyncio
from discord import app_commands
from dotenv import load_dotenv
import os
import aiosqlite
from openai import OpenAi

load_dotenv()

intents = discord.Intents.default()
intents.typing = False
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix=";", intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Watching tickets for shitheads"
        )
    )

    print(f'{bot.user} online')

    bot.db = await aiosqlite.connect('keo.db')

    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            warned_by INTEGER NOT NULL,
            reason TEXT
        )
    """)
    await bot.db.commit()

    await bot.tree.sync()

@bot.event
async def on_member_join(member):

    keowelcome = discord.utils.get(member.guild.text_channels, name="-")

    if keowelcome is None:
        return

    embed = discord.Embed(title=member, color=discord.Color.green())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="", value=f"{member.mention} just joined {member.guild.name}, they are now at {member.guild.member_count}", inline=False)

    await keowelcome.send(embed=embed)

@bot.tree.command(name="invite", description="Get keo's invite link")
async def invite(interaction: discord.Interaction):

    await interaction.response.send_message("https://discord.com/oauth2/authorize?client_id=1454097190548148256&permissions=8&integration_type=0&scope=bot")

@bot.tree.command(name="license", description="Shows the license of distribution for keo")
async def license(interaction: discord.Interaction):

    await interaction.response.send_message("Keo is available for modification BUT copy's of keo's code modified by users must NOT be distributed, sold, or for public use without the written consent of it's direct owner. If you violate any of these statues you may be subject to legal action being taken against you for copyright infringments. You can read more at https://github.com/sh5sui/keo/blob/main/LICENSE/")

@bot.tree.command(name="warn", description="Warns a user for a reason")
async def warn(interaction: discord.Interaction, member: discord.Member = None, reason: str = None):

    if not(interaction.user.guild_permissions.manage_messages):
        await interaction.response.send_message("You don't have permission to use this command", ephemeral=True)
        return
    
    if interaction.user == member:
        await interaction.response.send_message("You cannot warn yourself", ephemeral=True)
        return
    
    if member is None or reason is None:
        await interaction.response.send_message("You must provide a member to warn and a reason", ephemeral=True)
        return
    
    await bot.db.execute(
        "INSERT INTO warnings (guild_id, user_id, warned_by, reason) VALUES (?, ?, ?, ?)",
        (interaction.guild.id, member.id, interaction.user.id, reason)
    )
    await bot.db.commit()

    await interaction.response.send_message(f"{member.mention} Has been warned for reason {reason}")

@bot.tree.command(name="askai", description="Ask ChatGPT Anything")
async def askai(interaction: discord.Interaction, prompt: str = None):

    client = OpenAi(
        api_key=os.getenv("OpenAI"),
    )

    response = client.resposes.create(
        model="gpt-4o",
        instructions="Limit to one sentence, briefly explain the topic to the best of your ability.",
        input=prompt
    )

    interaction.response.send_message(response)

@bot.tree.command(name="viewwarns", description="Views the warns of a certain user")
async def viewwarns(interaction: discord.Interaction, userid: str = None):

    if not(interaction.user.guild_permissions.manage_messages):
        await interaction.response.send_message("You don't have permission to run this command", ephemeral=True)
        return
    
    if userid is None:
        await interaction.response.send_message("You must enter a userid", ephemeral=True)
        return
    
    async with bot.db.execute(
        "SELECT id, reason, warned_by FROM warnings WHERE guild_id = ? AND user_id = ?",
        (interaction.guild.id, userid)
    ) as cursor:
        rows = await cursor.fetchall()

    if not rows:
        await interaction.response.send_message(f"No warnings found for <@{userid}>")

    embed = discord.Embed(title="Warnings", color=discord.Color.red())
    embed.set_thumbnail(url=interaction.guild.icon.url)

    for row in rows:
        warn_id, reason, warned_by_id = row
        warned_by = interaction.guild.get_member(warned_by_id)
        warned_by_name = warned_by.name if warned_by else f"{warned_by_id}"
        embed.add_field(name=f"Warn id", value=warn_id, inline=False)
        embed.add_field(name=f"Reason", value=reason, inline=False)
        embed.add_field(name="Warned by", value=warned_by_name, inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ban", description="Bans a user")
async def ban(interaction: discord.Interaction, target: discord.User = None, reason: str = None):

    guild = interaction.guild

    if target == interaction.user:
        await interaction.response.send_message("You cannot ban yourself", ephemeral=True)
        return
    
    if not(interaction.user.guild_permissions.ban_members):
        await interaction.response.send_message("You don't have permission to use this command", ephemeral=True)
        return
    
    if target.top_role > interaction.user.top_role:
        await interaction.response.send_message("You cannot ban someone with a higher role than you", ephemeral=True)
        return
    
    await guild.ban(target, reason=f"Banned by {interaction.user} for reason: {reason}")
    await interaction.response.send_message(f"{target.mention} was banned for reason: {reason}")

@bot.tree.command(name="kick", description="Kicks a user")
async def kick(interaction: discord.Interaction, target: discord.User = None, reason: str = None):

    guild = interaction.guild

    if target == interaction.user:
        await interaction.response.send_message("You cannot kick yourself", ephemeral=True)
        return
    
    if not(interaction.user.guild_permissions.kick_members):
        await interaction.response.send_message("You don't have permission to use this command", ephemeral=True)
        return
    
    if target.top_role > interaction.user.top_role:
        await interaction.response.send_message("You cannot kick someone with a higher role than you", ephemeral=True)
        return
    
    await guild.kick(target, reason=f"Kicked by {interaction.user} for reason: {reason}")
    await interaction.response.send_message(f"{target.mention} was kicked for reason: {reason}")

@bot.tree.command(name="globalban", description="Globally bans someone from every server that the bot is in")
async def globalban(interaction: discord.Interaction, target: str = None):

    if interaction.user.id != 610825208999182336:
        await interaction.response.send_message("This command is meant to only be for the bot owners use. This bot applys a ban to every single server that the bot is in for a specific user. This will only be used for very serious offenses. If you want to ask for a person to be added to the global ban system you can open a ticket in the support server.", ephemeral=True)
        return
    
    await interaction.response.send_message("Command is still in development", ephemeral=True)

@bot.tree.command(name="removewarn", description="Removes a warn from a person")
async def removewarn(interaction: discord.Interaction, warnid: str = None):

    if not(interaction.user.guild_permissions.manage_messages):
        await interaction.response.send_message("You don't have permission to run this command", ephemeral=True)
        return
    
    if warnid is None:
        await interaction.response.send_message("You must enter a valid warnid", ephemeral=True)
        return
    
    await bot.db.execute(
        "DELETE FROM warnings WHERE guild_id = ? AND id = ?",
        (interaction.guild.id, warnid)
    )
    await bot.db.commit()

    await interaction.response.send_message("Warn was removed successfully")

@bot.tree.command(name="userinfo", description="Shows information about a user")
async def userinfo(interaction: discord.Interaction, target: discord.Member = None):

    embed = discord.Embed(title="User info", color=discord.Color.blue())
    embed.set_thumbnail(url=target.avatar.url)
    embed.add_field(name="Username", value=target.mention)
    embed.add_field(name="Account age", value=target.created_at)
    embed.add_field(name="Status", value=target.client_status)

@bot.tree.command(name="serverinfo", description="Shows information about the server")
async def serverinfo(interaction: discord.Interaction):

    embed = discord.Embed(title="Server info", color=discord.Color.blue())
    embed.set_thumbnail(url=interaction.guild.icon.url)
    embed.add_field(name="Server Id", value=interaction.guild_id, inline=False)
    embed.add_field(name="Owner", value=interaction.guild.owner.mention, inline=False)
    embed.add_field(name="Member Count", value=interaction.guild.member_count, inline=False)
    embed.add_field(name="Created On", value=interaction.guild.created_at, inline=False)
    embed.add_field(name="Roles", value=len(interaction.guild.roles), inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="activate", description="Activate the usage of the bot for a certain guild")
async def activate(interaction: discord.Interaction, guildid: str = None):

    if interaction.user.id != 610825208999182336:
        await interaction.response.send_message("You don't have permission to use this command")
        return
    
    await interaction.response.send_message("Currently under development")

@bot.tree.command(name="mute", description="Timeout a user with reason")
async def mute(interaction: discord.Interaction, target: discord.User = None, reason: str = None, length: int = None):

    guild = interaction.guild
    mutedrole = interaction.guild.get_role("muted")

    if not(interaction.user.guild_permissions.mute_members):
        await interaction.response.send_message("You don't have permission to use this command", ephemeral=True)
        return
    
    if target == interaction.user:
        await interaction.response.send_message("You cannot mute yourself", ephemeral=True)
        return
    
    if target.top_role > interaction.user.top_role:
        await interaction.response.send_message("You cannot mute someone with a higher role than you", ephemeral=True)
        return
    
    await target.add_roles(mutedrole)
    await interaction.response.send_message(f"{target.mention} has been muted for {length}s for reason {reason}")

    asyncio.sleep(length)

    await target.remove_roles(mutedrole)
    await interaction.followup.send(f"{target.mention} has been muted for reason timeout expired")

@bot.tree.command(name="unmute", description="Removes a mute from a person")
async def unmute(interaction: discord.Interaction, target: discord.Member = None):

    mutedrole = interaction.guild.get_role("muted")

    if not(interaction.user.guild_permissions.mute_members):
        await interaction.response.send_message("You don't have permission to use this command", ephemeral=True)
        return
    
    await target.remove_roles(mutedrole)
    await interaction.response.send_message(f"{target.mention} has been unmuted by {interaction.user.mention}")

@bot.tree.command(name="ticket", description="Open a ticket with a specified reason")
async def ticket(interaction: discord.Interaction, reason: str = None):

    guild = interaction.guild

    logs = discord.utils.get(guild.text_channels, name="keo-logs")

    keologs = logs

    permissions = {
    guild.default_role: discord.PermissionOverwrite(view_channel=False),
    interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    embed = discord.Embed(title="Ticket", color=discord.Color.blue())
    embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="", value="Please wait for a member of staff to respond to your ticket. While your waiting, feel free to describe your issue in more detail.")

    category = discord.utils.get(guild.categories, name="tickets")

    ticket = await guild.create_text_channel(
        name=f"ticket-{reason}",
        category=category,
        overwrites=permissions
    )

    await ticket.send(
        f"Welcome {interaction.user.mention} ||@here||\n",
        embed=embed
    )

    await interaction.response.send_message(f"Your ticket has been created, {ticket.mention}", ephemeral=True)

    logsembed=discord.Embed(title="Ticket opened", color=discord.Color.blue())
    logsembed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1365048856706023517/1454186679060660387/d1631a367e7b13cb22c78a416a5ad5be.jpg?ex=69502c61&is=694edae1&hm=4e908a9198ed0cd6477ceffa54ebabbf08f579b767d37ea516b126092ac3ecec&")
    logsembed.add_field(name="", value=f"Ticket created by {interaction.user.mention}")

    await keologs.send(embed=logsembed)

@bot.tree.command(name="giverole", description="Gives a role to everyone in the server")
async def giverole(interaction: discord.Interaction, role: discord.Role = None):

    if not(interaction.user.guild_permissions.administrator):
        interaction.response.send_message("You don't have permission to use this command", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    count = 0
    for member in interaction.guild.members:
        if role not in member.roles:
            try:
                await member.add_roles(role, reason=f"Role mass added by {interaction.user}")
                count +=1
                await asyncio.sleep(0.8)
            except Exception as e:
                print(f"Failed to give role to {member}")

            await interaction.followup.send(f"Added {role} to {count} members")

@bot.tree.command(name="add", description="Adds a member to a ticket")
async def add(interaction: discord.Interaction, member: discord.Member = None):

    if interaction.channel.category.name != "tickets":
        await interaction.response.send_message("You cannot use this command outside of the tickets category")
        return
    
    if not(interaction.user.guild_permissions.manage_channels):
        await interaction.response.send_message("You don't have permission to run this command")
        return
    
    await interaction.channel.set_permissions(
        member,
        view_channel=True,
        send_messages=True,
        read_message_history=True
    )

    await interaction.response.send_message(f"{member.mention}, Has been added to the ticket")

@bot.tree.command(name="commands", description="Shows a list of all available commands")
async def commands(interaction: discord.Interaction):

    embed=discord.Embed(title="Keo commands", color=discord.Color.blue())
    embed.set_thumbnail(url=interaction.guild.icon.url)
    embed.add_field(name="invite", value="Gives the invite for keo", inline=False)
    embed.add_field(name="license", value="Shows the license for keo", inline=False)
    embed.add_field(name="ticket", value="Opens a ticket with reason", inline=False)
    embed.add_field(name="close", value="Closes an open ticket with reason", inline=False)
    embed.add_field(name="setup", value="Automatically sets your server up to be in full compatability with keo", inline=False)
    embed.add_field(name="ping", value="Pings keo to see the latency")
    embed.add_field(name="avatar", value="Gets a users avatar")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="Pings the bot to see latency")
async def ping(interaction: discord.Interaction):

    await interaction.response.send_message(f"Latency: {bot.latency}ms")

@bot.tree.command(name="avatar", description="Get a users avatar")
async def avatar(interaction: discord.Interaction, target: discord.User = None):

    await interaction.response.send_message(target.avatar.url)

@bot.tree.command(name="close", description="Closes an open ticket")
async def close(interaction: discord.Interaction, reason: str = None):

    guild = interaction.guild

    logs = discord.utils.get(guild.text_channels, name="keo-logs")

    keologs = logs

    if not (interaction.user.guild_permissions.manage_channels):
        await interaction.response.send_message("You do not have permission to run this command", ephemeral=True)
        return
    
    if interaction.channel.category is None or interaction.channel.category.name != "tickets":
        await interaction.response.send_message("You cannot use this command outside of the tickets category", ephemeral=True)
        return
    
    await interaction.response.send_message(f"This ticket will be deleted in 3 seconds for reason: {reason}")

    await asyncio.sleep(3)
    
    await interaction.channel.delete()

    logsembed=discord.Embed(title="Ticket closed", color=discord.Color.blue())
    logsembed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1365048856706023517/1454186679060660387/d1631a367e7b13cb22c78a416a5ad5be.jpg?ex=69502c61&is=694edae1&hm=4e908a9198ed0cd6477ceffa54ebabbf08f579b767d37ea516b126092ac3ecec&")
    logsembed.add_field(name="", value=f"Ticket closed by {interaction.user.mention}")

    await keologs.send(embed=logsembed)

@bot.tree.command(name="setup", description="Runs you through a setup to ensure that keo runs as intended in your server")
async def setup(interaction: discord.Interaction):

    muted = interaction.guild.get_role("muted")

    ticketspermissions = {
        interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False)
    }

    logpermissions = {
        interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False)
    }

    onboardingpermissions = {
        interaction.guild.default_role: discord.PermissionOverwrite(send_messages=False)
    }

    mutedrolepermissions = {
        muted: discord.PermissionOverwrite(send_messages=False)
    }

    guild = interaction.guild

    logs = discord.utils.get(guild.text_channels, name="keo-logs")

    keologs = logs

    if not (interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("You don't have permission to run this command. Missing permssion: Administrator")
        return

    setupstart=discord.Embed(title="Setup process", color=discord.Color.blue())
    setupstart.set_thumbnail(url=interaction.guild.icon.url)
    setupstart.add_field(name="", value="Welcome to the keto bot setup process. This process is automated and any changes that should be made for this bot to work properly in your server will be completed automatically. Any changes we need to do that are already done by you will be skipped.")

    await interaction.response.send_message(embed=setupstart)

    ticketsetup = await interaction.guild.create_category(
        name="tickets",
        overwrites=ticketspermissions
    )

    logsetup = await interaction.guild.create_text_channel(
        name="keo-logs",
        overwrites=logpermissions
    )

    onboardingsetup = await interaction.guild.create_text_channel(
        name="-",
        overwrites=onboardingpermissions
    )

    mutedrolesetup = await interaction.guild.create_role(
        name="muted",
        permissions=mutedrolepermissions
    )

    interaction.followup.send(f"Setup finished, Created tickets category, created keo logs channel {logsetup.mention}")

    logsembed=discord.Embed(title="Command executed", color=discord.Color.blue())
    logsembed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1365048856706023517/1454186679060660387/d1631a367e7b13cb22c78a416a5ad5be.jpg?ex=69502c61&is=694edae1&hm=4e908a9198ed0cd6477ceffa54ebabbf08f579b767d37ea516b126092ac3ecec&")
    logsembed.add_field(name="", value=f"Setup was triggered by {interaction.user.mention}")

    await keologs.send(embed=logsembed)

Token = os.getenv("Token")
bot.run(Token)