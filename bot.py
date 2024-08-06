# -*- coding: utf-8 -*-

import os
import json
import logging
import asyncio
import discord
from discord.ext import commands

R = '\033[31m'
G = '\033[92m'
Y = '\033[33m'
X = '\033[0m'

with open('config.json') as f:
    config = json.load(f)

required_keys = ['prefix', 'token', 'owner_id', 'logging', 'server_id', 'verified_role_name', 'verified_channel_name', 'verification_channel_id', 'botVersion', 'restricted_role_id']
if not all(key in config for key in required_keys):
    raise ValueError("Invalid config.json")

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

# --- Helper Functions ---

def has_restricted_role():
    restricted_role_id = config.get('restricted_role_id')
    async def predicate(ctx):
        role = discord.utils.get(ctx.author.roles, id=restricted_role_id)
        logger.debug(f"Checking role for user {ctx.author}: {role}")
        return role is not None
    return commands.check(predicate)

def count_cogs():
    cogs = []
    for root, dirs, files in os.walk('./cogs'):
        for filename in files:
            if filename.endswith('.py'):
                cogs.append(os.path.join(root, filename).replace(os.sep, '.')[2:-3])
    return cogs

async def load_cogs():
    loaded_cogs = []
    for root, dirs, files in os.walk('./cogs'):
        for filename in files:
            if filename.endswith('.py'):
                cog_path = os.path.join(root, filename)
                cog_module = cog_path.replace(os.sep, '.')[2:-3]
                try:
                    await bot.load_extension(cog_module)
                    loaded_cogs.append(cog_module)
                except Exception as e:
                    logger.error(f"Failed to load cog {cog_module}: {e}")
    return loaded_cogs

# --- Bot Events ---

@bot.event
async def on_ready():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        logger.info("Bot started")

        loaded_cogs = await load_cogs()
        total_cogs = count_cogs()

        missing_cogs = [cog for cog in total_cogs if cog not in loaded_cogs]

        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="you"))
        print(f"[{G}!{X}] Logged in as: {G}{bot.user}{X}")
        print(f"[{G}!{X}] Discord ID: {G}{bot.user.id}{X}")
        print(f"[{G}!{X}] Bot Version: {G}{config['botVersion']}{X}")
        print(f"[{G}!{X}] Discord.py Version: {G}{discord.__version__}{X}")
        print(f"[{G}!{X}] Commands: {G}{len(loaded_cogs)}/{len(total_cogs)}{X}")
        if missing_cogs:
            print(f"[{G}!{X}] Missing: {R}{' '.join(missing_cogs)}{X}")

    except Exception as ex:
        logger.error(f"An error occurred during bot startup: {ex}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"Error: Command not found. Use `{config['prefix']}help` for a list of commands.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("Error: You do not have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Error: Missing required argument.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Error: Bad argument.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("Error: You do not have the required role to use this command.")
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
        await message.delete()

@bot.event
async def on_disconnect():
    logger.info("Bot disconnected")

@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"Error in {event}: {args} {kwargs}")

async def main():
    async with bot:
        await bot.start(config['token'])

if __name__ == "__main__":
    if not asyncio.get_event_loop().is_running():
        asyncio.run(main())
