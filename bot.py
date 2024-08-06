# -*- coding: utf-8 -*-

import os
import time
import json
import logging
import asyncio
import discord
from discord.ext import commands, tasks
import requests
from io import BytesIO
from PIL import Image


R = '\033[31m'  # Red
G = '\033[92m'  # Green
Y = '\033[33m'  # Yellow
X = '\033[0m'  # Reset

# Load
with open('config.json') as f:
    config = json.load(f)

# Validate
required_keys = ['prefix', 'token', 'owner_id', 'logging', 'server_id', 'verified_role_name', 'verified_channel_name', 'verification_channel_id']
if not all(key in config for key in required_keys):
    raise ValueError("Invalid config.json")

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, config['logging']['level']))

file_handler = logging.FileHandler('logs.txt', mode='w', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

bot = commands.Bot(command_prefix=config['prefix'], intents=discord.Intents.all(), help_command=None)

restricted_role_id = 1152126043486965831

def has_restricted_role():
    async def predicate(ctx):
        role = discord.utils.get(ctx.author.roles, id=restricted_role_id)
        return role is not None
    return commands.check(predicate)

# Events

@bot.event
async def on_ready():
    logger.info("Bot started")
    os.system('cls' if os.name == 'nt' else 'clear')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="you"))
    print(f"[{G}!{X}] Logged in as: {G}{bot.user}{X}")
    print(f"[{G}!{X}] Discord ID: {G}{bot.user.id}{X}")
    print(f"[{G}!{X}] Bot Version: {G}{config['botVersion']}{X}")
    print(f"[{G}!{X}] Discord.py Version: {G}{discord.__version__}{X}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"Error: Command not found. Use `{config['prefix']}help` for a list of commands.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("Error: You do not have permission to use this command.")
    else:
        logger.error(f"Command error: {error}")
        await ctx.send(f"Error: An unexpected error occurred. Details: {error}")

@bot.event
async def on_command(ctx: commands.Context):
    try:
        await ctx.message.delete()
    except discord.HTTPException as e:
        logger.error(f"Error deleting message: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)
    if message.content.startswith(config['prefix']):
        await asyncio.sleep(5)
        if message.exists:
            await message.delete()

def has_restricted_role():
    async def predicate(ctx):
        role = discord.utils.get(ctx.author.roles, id=restricted_role_id)
        return role is not None
    return commands.check(predicate)

@bot.command(name="help", help="Displays information about the bot.")
@has_restricted_role()
async def help_command(ctx):
    embed = discord.Embed(
        description="All Available Commands:",
        color=discord.Color(0x6900ff),
    )

    for cmd in bot.commands:
        embed.add_field(name=f"`{config['prefix']}{cmd.name}`", value=cmd.help, inline=False)

    embed.set_image(url=config.get('help_image', "https://i.imgur.com/5mp2Siz.png"))
    embed.set_footer(text="From PortLords w Love 2024")
    await ctx.send(embed=embed)

@bot.command(name="ping", help="Displays the bot's latency.")
@has_restricted_role()
async def ping_command(ctx):
    await ctx.send(f"Ping: {bot.latency * 1000:.2f}ms")

@bot.command(name="reload", help="Reloads the bot's code (development only).")
@commands.is_owner()
async def reload(ctx):
    await ctx.send("Reloading...")
    await bot.close()
    os.system("python bot.py")

@bot.command(name="verification", help="Starts the verification process.")
async def verification_command(ctx):
    logger.info(f"Verification command invoked by {ctx.author} in {ctx.guild}")
    try:
        server = bot.get_guild(int(config['server_id']))
        if not server:
            await ctx.send(f"Error: Could not find the server with ID {config['server_id']}. Please check your config.")
            return

        verified_role = discord.utils.get(server.roles, name=config['verified_role_name'])
        if not verified_role:
            await ctx.send(f"Error: Could not find the verified role with name '{config['verified_role_name']}'. Please check your server roles.")
            return

        verification_channel_id = int(config['verification_channel_id'])
        verification_channel = bot.get_channel(verification_channel_id)
        if not verification_channel:
            await ctx.send(f"Error: Could not find the verification channel with ID '{verification_channel_id}'. Please check your config.")
            return

        if ctx.channel.id != verification_channel.id:
            await ctx.send(f"Please use this command in the designated verification channel: {verification_channel.mention}")
            return

        embed = discord.Embed(
            title="Agree & Continue",
            description="🗹 `We are not responsible for the actions of our members`",
            color=discord.Color(0x6900ff),
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Verify", style=discord.ButtonStyle.secondary))

        async def button_callback(interaction):
            try:
                await interaction.response.send_message("Verification successful!", ephemeral=True)
                await interaction.user.add_roles(verified_role)
                logger.info(f"User {interaction.user} verified successfully in {ctx.guild}")
            except Exception as e:
                logger.error(f"Error during verification: {e}")
                await ctx.send(f"Error during verification. Please try again later.")

        view.children[0].callback = button_callback

        await ctx.send(embed=embed, view=view)
        logger.info(f"Verification embed sent to channel {verification_channel} in {ctx.guild}")

    except Exception as e:
        logger.error(f"An error occurred in the verification command: {e}")
        await ctx.send(f"An error occurred. Please try again later.")

@bot.command(name="impersonate", help="Impersonates a user.")
@commands.has_permissions(administrator=True)
async def impersonate(ctx, member: discord.Member, *, message: str):
    await bot.user.edit(username=member.name, avatar=await member.avatar_url.read())

    await ctx.send(message)

bot.run(config['token'])
