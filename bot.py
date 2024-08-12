# -*- coding: utf-8 -*-
import os
import json
import asyncio
import logging
import discord
from discord.ext import commands, tasks
from itertools import cycle

# Load Config
with open('config.json') as f:
    config = json.load(f)

# --- Logging ---

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs.txt', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=config['prefix'], intents=intents, help_command=None)
bot.config = config

statuses = [
    (discord.ActivityType.watching, "Hated 🤓 Code"),
    (discord.ActivityType.watching, "the 🚄 pass"),
    (discord.ActivityType.playing, "Lun 🌙 Client"),
    (discord.ActivityType.watching, "for The FEDs"),
    (discord.ActivityType.playing, "Lego 🧇 Eggo"),
    (discord.ActivityType.watching, "🚀 Above and Beyond"),
    (discord.ActivityType.watching, "🗺️ it spread"),
    (discord.ActivityType.playing, "w Herawens 💔"),
]

status_cycle = cycle(statuses)

@tasks.loop(seconds=15)
async def change_status() -> None:
    if status_cycle:
        activity_type, status_message = next(status_cycle)
        await bot.change_presence(activity=discord.Activity(type=activity_type, name=status_message))
    else:
        logger.error("Status cycle is empty")

# --- Helper Functions ---

async def load_cogs() -> tuple:
    cogs_to_load = config.get('cogs', [])
    loaded_cogs = []
    missing_cogs = []
    loaded_extensions = set(bot.extensions.keys())

    for cog in cogs_to_load:
        if cog not in loaded_extensions:
            try:
                await bot.load_extension(f"cogs.{cog}")
                loaded_cogs.append(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")
                missing_cogs.append(cog)
        else:
            logger.info(f"Cog {cog} is already loaded.")

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
async def on_error(event: str, *args, **kwargs) -> None:
    logger.error(f"Unhandled exception in {event}: {args} {kwargs}", exc_info=True)

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

        print(f"[{G}!{X}] Logged in as: {G}{bot.user.name}{X}")
        print(f"[{G}!{X}] Discord ID: {G}{bot.user.id}{X}")
        print(f"[{G}!{X}] Bot Version: {G}{config['botVersion']}{X}")
        print(f"[{G}!{X}] Discord.py Version: {G}{discord.__version__}{X}")
        print(f"[{G}!{X}] Commands: {G}{len(loaded_cogs)}/{len(total_cogs)}{X}")
        if missing_cogs:
            print(f"[{G}!{X}] Missing: {R}{'/'.join(missing_cogs)}{X}")

    except Exception as ex:
        logger.error(f"An error occurred during bot startup: {ex}", exc_info=True)


# -- Commands ---
@bot.command(name='reload_cogs', hidden=True)
@commands.is_owner()
async def reload_cogs_command(ctx: commands.Context) -> None:
    await reload_cogs()
    await ctx.send("Cogs reloaded.")

async def main() -> None:
    try:
        await bot.start(config['token'])
    except Exception as ex:
        logger.error(f"An error occurred during bot startup: {ex}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
