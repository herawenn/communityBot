# -*- coding: utf-8 -*-
import os
import json
import asyncio
import logging
from typing import List, Tuple
import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
from itertools import cycle

# --- Load & Validate ---

CONFIG_PATH = 'config.json'

def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        config = json.load(f)

    required_keys = [
        'discord', 'identifiers', 'paths', 'settings', 'apis', 'embeds'
    ]
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Missing required key '{key}' in config.json")
    return config

config = load_config(CONFIG_PATH)

DISCORD_CONFIG = config['discord']
IDENTIFIERS_CONFIG = config['identifiers']
PATHS_CONFIG = config['paths']
SETTINGS_CONFIG = config['settings']
APIS_CONFIG = config['apis']
EMBEDS_CONFIG = config['embeds']

# --- Logging ---

LOGS_DIR = 'logs'
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(os.path.join(LOGS_DIR, 'logs.txt'), mode='w', encoding='utf-8'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# --- Bot Initialization ---

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=DISCORD_CONFIG['prefix'], intents=intents, help_command=None)
bot.config = config

# --- Tasks ---

STATUSES = [
    (discord.ActivityType.watching, "Hated 🤓 Code"),
    (discord.ActivityType.watching, "the 🚄 pass"),
    (discord.ActivityType.playing, "Lun 🌙 Client"),
    (discord.ActivityType.watching, "for The FEDs"),
    (discord.ActivityType.playing, "Lego 🧇 Eggo"),
    (discord.ActivityType.watching, "🚀 Above and Beyond"),
    (discord.ActivityType.watching, "🗺️ it spread"),
    (discord.ActivityType.playing, "w Herawens 💔")
]
status_cycle = cycle(STATUSES)

@tasks.loop(seconds=15)
async def change_status() -> None:
    if status_cycle:
        activity_type, status_message = next(status_cycle)
        await bot.change_presence(
            activity=discord.Activity(
                type=activity_type, name=status_message
            )
        )
    else:
        logger.error("Status list is empty.")

# --- Helper Functions ---

async def load_cogs() -> Tuple[List[str], List[str]]:

    loaded_cogs = []
    missing_cogs = []

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            cog_name = f"cogs.{filename[:-3]}"
            try:
                if cog_name not in bot.extensions:
                    await bot.load_extension(cog_name)
                    loaded_cogs.append(cog_name)
                    logger.info(f"Loaded cog: {cog_name}")
                else:
                    logger.info(f"Cog {cog_name} is already loaded.")
            except Exception as e:
                logger.error(f"Failed to load cog {cog_name}: {e}")
                missing_cogs.append(cog_name)

    return loaded_cogs, missing_cogs

# --- Bot Events ---

@bot.event
async def on_error(event: str, *args, **kwargs) -> None:
    logger.error(
        f"Unhandled exception in {event}: {args} {kwargs}",
        exc_info=True
    )

@bot.event
async def on_command_error(
    ctx: commands.Context,
    error: commands.CommandError
) -> None:
    if isinstance(error, commands.CommandNotFound):
        return

    logger.error(f"Command error: {error}", exc_info=True)
    await ctx.send("An error occurred while executing the command.")

@bot.event
async def on_ready() -> None:
    try:
        R = '\033[31m'
        G = '\033[92m'
        X = '\033[0m'

        os.system('cls' if os.name == 'nt' else 'clear')

        loaded_cogs, missing_cogs = await load_cogs()
        change_status.start()

        print(f"[{G}!{X}] Logged in as: {G}{bot.user.name}{X}")
        print(f"[{G}!{X}] Discord ID: {G}{bot.user.id}{X}")
        print(f"[{G}!{X}] Bot Version: {G}{DISCORD_CONFIG['version']}{X}")
        print(f"[{G}!{X}] Discord.py Version: {G}{discord.__version__}{X}")
        print(f"[{G}!{X}] Commands: {G}{len(loaded_cogs)}{X}")

        print(f"[{G}!{X}] Loaded Cogs: {G}{', '.join(loaded_cogs)}{X}")
        if missing_cogs:
            print(f"[{R}!{X}] Missing Cogs: {R}{', '.join(missing_cogs)}{X}")

    except Exception as ex:
        logger.error(
            f"An error occurred during bot startup: {ex}",
            exc_info=True
        )

# --- Bot Commands ---

@bot.command(name='reload')
@commands.is_owner()
async def reload(ctx: commands.Context, cog: str) -> None:
    try:
        await bot.unload_extension(f"cogs.{cog}")
        await bot.load_extension(f"cogs.{cog}")
        await ctx.send(f"Reloaded cog: {cog}")
        logger.info(f"Reloaded cog: {cog}")
    except Exception as e:
        await ctx.send(f"Failed to reload cog {cog}: {e}")
        logger.error(f"Failed to reload cog {cog}: {e}", exc_info=True)

async def main() -> None:
    try:
        await bot.start(DISCORD_CONFIG['token'])
    except Exception as ex:
        logger.error(
            f"An error occurred during bot startup: {ex}",
            exc_info=True
        )

if __name__ == "__main__":
    asyncio.run(main())
