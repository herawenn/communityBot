# -*- coding: utf-8 -*-
import os
import json
import logging
import asyncio
import discord
from discord.ext import commands, tasks
from itertools import cycle

# Load config
with open('config.json') as f:
    config = json.load(f)

# --- Logging ---

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('logs.txt', mode='w', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# --- Bot Setup ---

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=config['prefix'], intents=intents, help_command=None)

# --- Tasks ---

statuses = [
    "Hated torrent files",
    "the train come",
    "Lun client",
    "for The FEDs",
    "ai kill us Sxul",
    "kt become katie",
    "Lego my eggo",
    "python save humanity",
    "hands Above your head",
    "you be great",
    "Herawen was here",
]

status_cycle = cycle(statuses)

@tasks.loop(seconds=5)
async def change_status() -> None:
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name=next(status_cycle)))

# --- Helper Functions ---

async def load_cogs() -> tuple:
    cogs_to_load = config.get('cogs', [])
    loaded_cogs = []
    missing_cogs = []

    for cog in cogs_to_load:
        try:
            await bot.load_extension(f"cogs.{cog}")
            loaded_cogs.append(cog)
            logger.info(f"Loaded cog: {cog}")
        except Exception as e:
            logger.error(f"Failed to load cog {cog}: {e}")
            missing_cogs.append(cog)

    return loaded_cogs, missing_cogs

async def reload_cogs() -> None:
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            cog_name = f"cogs.{filename[:-3]}"
            try:
                await bot.reload_extension(cog_name)
                logger.info(f"Reloaded cog: {cog_name}")
            except commands.ExtensionNotLoaded:
                try:
                    await bot.load_extension(cog_name)
                    logger.info(f"Loaded cog: {cog_name}")
                except Exception as e:
                    logger.error(f"Failed to load cog {cog_name}: {e}")
            except Exception as e:
                logger.error(f"Failed to reload cog {cog_name}: {e}")

# --- Bot Events ---

@bot.event
async def on_ready() -> None:
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        R = '\033[31m'
        G = '\033[92m'
        X = '\033[0m'
        loaded_cogs, missing_cogs = await load_cogs()
        total_cogs = config.get('cogs', [])

        change_status.start()

        print(f"[{G}!{X}] Logged in as: {G}{bot.user}{X}")
        print(f"[{G}!{X}] Discord ID: {G}{bot.user.id}{X}")
        print(f"[{G}!{X}] Bot Version: {G}{config['botVersion']}{X}")
        print(f"[{G}!{X}] Discord.py Version: {G}{discord.__version__}{X}")
        print(f"[{G}!{X}] Commands: {G}{len(loaded_cogs)}/{len(total_cogs)}{X}")
        if missing_cogs:
            print(f"[{G}!{X}] Missing: {R}{'/'.join(missing_cogs)}{X}")

    except Exception as ex:
        logger.error(f"An error occurred during bot startup: {ex}")

@bot.event
async def on_error(event: str, *args, **kwargs) -> None:
    logger.error(f"Unhandled exception in {event}: {args} {kwargs}", exc_info=True)

async def main() -> None:
    try:
        async with bot:
            await bot.start(config['token'])
    except Exception as ex:
        logger.error(f"An error occurred during bot startup: {ex}")

if __name__ == "__main__":
    asyncio.run(main())
