# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import json
from itertools import cycle
from typing import List, Tuple
import discord
from discord.ext import commands, tasks

# --- Load & Validate Configuration ---

CONFIG_PATH = 'config.json'

def load_config(config_path: str) -> dict:
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to load configuration file: {e}")
        return None

    required_keys = ['discord', 'identifiers', 'paths','settings', 'apis', 'embeds']
    for key in required_keys:
        if key not in config:
            logging.error(f"Missing required key '{key}' in {config_path}")
            return None

    return config

config = load_config(CONFIG_PATH)
if config is None:
    raise Exception("Failed to load configuration")

api_key = config['apis']['gemini']['api_key']
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

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler(os.path.join(LOGS_DIR, 'logs.txt'), mode='w', encoding='utf-8'), logging.StreamHandler()])

logger = logging.getLogger(__name__)

# --- Intents ---

intents = discord.Intents.all()
# intents.typing = False
# intents.presences = False
# intents.members = True

# --- Bot ---

bot = commands.Bot(command_prefix=DISCORD_CONFIG['prefix'], intents=intents, help_command=None)
bot.config = config

# --- Helper Functions ---

STATUSES = [
    (discord.ActivityType.watching, "Hated 🤓 Code"),
    (discord.ActivityType.watching, "the 🚄 pass"),
    (discord.ActivityType.playing, "🌙 Lun Client"),
    (discord.ActivityType.watching, "for The FEDs"),
    (discord.ActivityType.playing, "Leggo my Eggo 🧇"),
    (discord.ActivityType.watching, "🚀 Above and Beyond"),
    (discord.ActivityType.watching, "🗺️ it spread"),
    (discord.ActivityType.playing, "w Herawens 💔")
]
status_cycle = cycle(STATUSES)

# --- Tasks ---

@tasks.loop(seconds=15)
async def change_status() -> None:
    try:
        activity_type, status_message = next(status_cycle)
        await bot.change_presence(activity=discord.Activity(type=activity_type, name=status_message))
    except discord.HTTPException as e:
        logger.error(f"Failed to change status: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

# --- Cog Loading ---

async def load_cogs() -> Tuple[List[str], List[str]]:
    loaded_cogs = []
    missing_cogs = []

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename!= "__init__.py":
            cog_name = f"cogs.{filename[:-3]}"
            try:
                if cog_name not in bot.extensions:
                    await bot.load_extension(cog_name)
                    loaded_cogs.append(cog_name)
                    logger.info(f"Loaded cog: {cog_name}")
                else:
                    logger.info(f"Cog {cog_name} is already loaded.")
            except commands.ExtensionNotFound:
                logger.error(f"Failed to load cog {cog_name}: Not found")
                missing_cogs.append(cog_name)
            except commands.ExtensionFailed as e:
                logger.error(f"Failed to load cog {cog_name}: {e}")
                missing_cogs.append(cog_name)
            except Exception as e:
                logger.error(f"An unexpected error occurred while loading cog {cog_name}: {e}")
                missing_cogs.append(cog_name)

    return loaded_cogs, missing_cogs

# --- Bot Events ---

@bot.event
async def on_error(event: str, *args, **kwargs) -> None:
    logger.error(f"Unhandled exception in {event}: {args} {kwargs}", exc_info=True)

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please provide all required arguments.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument. Please try again.")
    else:
        logger.error(f"Command error: {error}", exc_info=True)
        await ctx.send("An error occurred. Please try again later.")

@bot.event
async def on_ready() -> None:
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        R = '\033[31m'
        G = '\033[92m'
        X = '\033[0m'

        change_status.start()

        print(f"[{G}!{X}] Logged in as: {G}{bot.user.name}{X}")
        print(f"[{G}!{X}] Discord ID: {G}{bot.user.id}{X}")
        print(f"[{G}!{X}] Bot Version: {G}{DISCORD_CONFIG['version']}{X}")
        print(f"[{G}!{X}] Discord.py Version: {G}{discord.__version__}{X}")

        loaded_cogs, missing_cogs = await load_cogs()

        print(f"[{G}!{X}] Commands: {G}{len(loaded_cogs)}{X}")
        print(f"[{G}!{X}] Loaded Cogs: {G}{', '.join(loaded_cogs)}{X}")

        if missing_cogs:
            print(f"[{R}!{X}] Missing Cogs: {R}{', '.join(missing_cogs)}{X}")

    except Exception as ex:
        logger.error(f"An error occurred during bot startup: {ex}", exc_info=True)

@bot.event
async def on_command(ctx: commands.Context) -> None:
    if SETTINGS_CONFIG['delete_commands']:
        logger.info(f"Scheduling deletion of command message: {ctx.message.content}")
        await asyncio.sleep(SETTINGS_CONFIG['delete_command_delay'])
        try:
            await ctx.message.delete()
            logger.info(f"Deleted command message: {ctx.message.content}")
        except discord.HTTPException as e:
            logger.error(f"Failed to delete command message: {ctx.message.content}, Error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while deleting command message: {e}")

# --- Bot Commands ---

@bot.command(name='reload')
@commands.is_owner()
async def reload(ctx: commands.Context, cog: str = None) -> None:
    try:
        if cog:
            await bot.unload_extension(f"cogs.{cog}")
            await bot.load_extension(f"cogs.{cog}")
            await ctx.send(f"`Reloaded cog: {cog}`")
            logger.info(f"Reloaded cog: {cog}")
        else:
            loaded_cogs, _ = await load_cogs()
            for cog in loaded_cogs:
                await bot.unload_extension(cog)
                await bot.load_extension(cog)
            await ctx.send("`Reloaded all cogs.`")
            logger.info("Reloaded all cogs.")
    except commands.ExtensionNotFound:
        await ctx.send(f"`Failed to reload cog {cog}`: Not found")
        logger.error(f"Failed to reload cog {cog}: Not found")
    except commands.ExtensionFailed as e:
        await ctx.send(f"`Failed to reload cog {cog}`: {e}")
        logger.error(f"Failed to reload cog {cog}: {e}", exc_info=True)
    except Exception as e:
        await ctx.send(f"`Failed to reload cog {cog}`: {e}")
        logger.error(f"An unexpected error occurred while reloading cog {cog}: {e}", exc_info=True)

async def main() -> None:
    try:
        await bot.start(DISCORD_CONFIG['token'])
    except discord.HTTPException as e:
        logger.error(f"Failed to start bot: {e}")
    except Exception as ex:
        logger.error(f"An error occurred during bot startup: {ex}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
