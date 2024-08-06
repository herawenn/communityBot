# -*- coding: utf-8 -*-

import os
import json
import logging
import asyncio
import discord
from discord.ext import commands, tasks
from itertools import cycle

R = '\033[31m'
G = '\033[92m'
Y = '\033[33m'
X = '\033[0m'

with open('config.json') as f:
    config = json.load(f)

# --- Logging ---

required_keys = ['prefix', 'token', 'owner_id', 'logging', 'server_id', 'verified_role_name', 'verified_channel_name', 'verification_channel_id', 'botVersion', 'restricted_role_id', 'initial_role_id']
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

# --- Rotating Status ---

statuses = [
    "hated torrent files",
    "the train come",
    "for The FEDs",
    "Herawen 2024",
    "Lunar Client",
    "you cook meth",
    "lego my eggo",
    "kt become katie",
    "python be great",
    "my lines disappear",
]

status_cycle = cycle(statuses)

@tasks.loop(seconds=5)
async def change_status():
    status = next(status_cycle)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status))

# --- Events ---

@bot.event
async def on_ready():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        logger.info("Bot started")

        loaded_cogs = await load_cogs()
        total_cogs = count_cogs()
        missing_cogs = [cog for cog in total_cogs if cog not in loaded_cogs]

        change_status.start()

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
async def on_member_join(member):
    initial_role_id = config['initial_role_id']
    initial_role = discord.utils.get(member.guild.roles, id=initial_role_id)
    if initial_role:
        await member.add_roles(initial_role)
        logger.info(f"Assigned initial role to new user {member} in {member.guild}")
    else:
        logger.error(f"Initial role with ID {initial_role_id} not found in {member.guild}")

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
        logger.error(f"Command error: {error}", exc_info=True)
        await ctx.send(f"Error: An unexpected error occurred. Details: {error}")

@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"Error in {event}: {args} {kwargs}", exc_info=True)

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

    try:
        await bot.process_commands(message)

        if config.get('delete_commands', False) and message.content.startswith(config['prefix']):
            try:
                await asyncio.sleep(5)
                await message.delete()
                logger.info(f"Deleted command message from {message.author} in {message.guild}")
            except discord.Forbidden:
                logger.error(f"Missing permissions to delete message from {message.author} in {message.guild}")
                await message.channel.send(f"{message.author.mention}, I don't have permission to delete your message.")
            except discord.NotFound:
                logger.error(f"Message not found - {message.author} in {message.guild}")
                
                # Don't notify the user if the message is already deleted
            
            except discord.HTTPException as e:
                logger.error(f"HTTP exception occurred while deleting message: {e}")
                await message.channel.send(f"{message.author.mention}, an error occurred while trying to delete your message.")
            except Exception as e:
                logger.error(f"Unexpected error occurred while deleting message: {e}", exc_info=True)
                await message.channel.send(f"{message.author.mention}, an unexpected error occurred while trying to delete your message.")

    except discord.HTTPException as e:
        logger.error(f"Error processing message: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in on_message: {e}", exc_info=True)

async def main():
    async with bot:
        await bot.start(config['token'])

if __name__ == "__main__":
    if not asyncio.get_event_loop().is_running():
        asyncio.run(main())
