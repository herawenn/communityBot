import asyncio
import logging
import discord
import random
import os
import json
import psutil
from itertools import cycle
import discord
from discord.ext import commands, tasks
import time
from dotenv import load_dotenv
import importlib
from helpers import create_embed

load_dotenv()

# --- Configuration ---

CONFIG_PATH = 'files/json/config.json'

def load_config(config_path: str) -> dict:
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to load configuration file: {e}")
        return None
    except FileNotFoundError as e:
        logging.error(f"Configuration file not found: {e}")
        return None

    required_keys = ['discord', 'identifiers', 'paths', 'logging', 'embeds', 'features', 'moderation', 'settings']
    for key in required_keys:
        if key not in config:
            logging.error(f"Missing required key '{key}' in {config_path}")
            return None

    return config

config = load_config(CONFIG_PATH)
if config is None:
    raise Exception("Failed to load configuration")

LOGS_DIR = config['logging']['log_path']
LOG_FILE_NAME = config['logging']['log_file_name']
LOG_LEVEL = config['logging']['log_level']

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

logger = logging.getLogger(__name__)

# --- Bot Setup ---

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config['discord']['prefix'], intents=intents, help_command=None)
bot.config = config

# --- Cog Loading ---

def load_cogs():
    loaded_cogs = []
    missing_cogs = []
    cogs_dir = bot.config['paths']['cogs_directory']

    cogs_order = [
        'cogs.database',
        'cogs.roles',
        'cogs.verification',
        'cogs.admin',
        'cogs.osint',
        'cogs.shodan',
        'cogs.recon',
        'cogs.exploit',
        'cogs.privacy',
        'cogs.community',
        'cogs.ai',
        'cogs.help',
        'cogs.logging',
        'cogs.obfuscate',
        'cogs.quiz',
        'cogs.crawler',
        'cogs.nefarious',
        'cogs.newsfeed',
        'cogs.other'
    ]

    for cog_name in cogs_order:
        try:
            module = importlib.import_module(cog_name)
            if hasattr(module, 'setup'):
                module.setup(bot)
                loaded_cogs.append(cog_name)
                logger.info(f"Loaded cog: {cog_name}")
            else:
                logger.error(f"No setup function in {cog_name}")
                missing_cogs.append(cog_name)
        except ModuleNotFoundError:
            logger.error(f"{cog_name} not found.")
            missing_cogs.append(cog_name)
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading cog {cog_name}: {e}", exc_info=True)
            missing_cogs.append(cog_name)

    return loaded_cogs, missing_cogs

# --- Bot Tasks ---

STATUSES = [
    (discord.ActivityType.watching, "chown me 🤓"),
    (discord.ActivityType.watching, "hated use mongo"),
    (discord.ActivityType.watching, "🔒 ssh n chill"),
    (discord.ActivityType.watching, "lego play vscode"),
    (discord.ActivityType.watching, "send me malware 💀"),
    (discord.ActivityType.watching, "above be black"),
    (discord.ActivityType.watching, "sxul was here"),
    (discord.ActivityType.watching, "herawens bag 💔"),
    (discord.ActivityType.watching, "our db is bigger"),
    (discord.ActivityType.listening, "🚨 ..help"),
]
status_cycle = cycle(STATUSES)

@tasks.loop(seconds=30)
async def change_status() -> None:
    try:
        activity_type, status_message = next(status_cycle)
        await bot.change_presence(activity=discord.Activity(type=activity_type, name=status_message))
    except discord.HTTPException as e:
        logger.error(f"Failed to change status: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)

# --- Bot Events ---

@bot.event
async def on_error(event: str, *args, **kwargs) -> None:
    logger.error(f"Unhandled exception in {event}: {args} {kwargs}", exc_info=True)

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    try:
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("`Please provide all required arguments.`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("`Invalid argument. Please try again.`")
        else:
            logger.error(f"Command error: {error}", exc_info=True)
            await ctx.send("`An error occurred. Please try again later.`")

        if config['settings']['delete_errors']:
            logger.info(f"Scheduling deletion of error message: {ctx.message.content}")
            await asyncio.sleep(config['settings']['delete_errors_delay'])
            try:
                await ctx.message.delete()
                logger.info(f"Deleted error message: {ctx.message.content}")
            except discord.HTTPException as e:
                logger.error(f"Failed to delete error message: {ctx.message.content}, Error: {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred while deleting error message: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in on_command_error: {e}", exc_info=True)

@bot.event
async def on_member_join(member: discord.Member) -> None:
    try:
        unverified_role = discord.utils.get(member.guild.roles, id=config['identifiers']['unverified_role_id'])
        if unverified_role:
            await member.add_roles(unverified_role)

        welcome_channel_id = config['identifiers'].get('welcome_channel_id')
        if welcome_channel_id:
            welcome_channel = bot.get_channel(welcome_channel_id)
            if welcome_channel:
                await welcome_channel.send(f"{member.mention}\n`We've been expecting you`")

        database_cog = bot.get_cog('Database')
        if database_cog:
            await database_cog.add_new_user(member.id, member.name)

    except Exception as e:
        logger.error(f"An error occurred during member join: {e}", exc_info=True)

@bot.event
async def on_member_remove(member: discord.Member) -> None:
    try:
        farewell_channel_id = config['identifiers'].get('farewell_channel_id')
        if farewell_channel_id:
            farewell_channel = bot.get_channel(farewell_channel_id)
            if farewell_channel:
                await farewell_channel.send(f"{member.mention} `left the server.`")
    except Exception as e:
        logger.error(f"An error occurred during member leave: {e}", exc_info=True)

@bot.event
async def on_ready() -> None:
    try:

        os.system('cls' if os.name == 'nt' else 'clear')
        R = '\033[31m'
        G = '\033[92m'
        X = '\033[0m'

        change_status.start()

        loaded_cogs, missing_cogs = load_cogs()

        guild_count = len(bot.guilds)
        user_count = sum(guild.member_count for guild in bot.guilds)
        latency = bot.latency
        uptime = time.time() - bot.start_time

        total_commands = len(bot.commands)

        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / (1024 * 1024)
        cpu_usage = psutil.cpu_percent(interval=1)

        guild_id = <Guild ID Here>

        guild = bot.get_guild(guild_id)
        if guild is None:
            logger.error(f"Guild with ID {guild_id} not found.")
        else:
            members = guild.members

            database_cog = bot.get_cog('Database')
            if database_cog:
                for member in members:
                    if not member.bot:
                        user_exists = await database_cog.fetch_one(
                            "SELECT 1 FROM Users WHERE user_id = ?", (member.id,)
                        )
                        if not user_exists:
                            await database_cog.add_new_user(member.id, member.name)
            else:
                logger.error("Database cog not found.")

        owner_id = config['identifiers'].get('owner_id')
        if owner_id:
            owner = await bot.fetch_user(owner_id)

        database_cog = bot.get_cog('Database')
        if database_cog:
            database_user_count = (await database_cog.fetch_one("SELECT COUNT(*) FROM Users"))[0]
        else:
            database_user_count = "n/a"

        if bot.config['features']['crawler']:
            crawler_cog = bot.get_cog('Crawler')
            if crawler_cog:
                crawler_cog.device_poster_task.start()
                crawler_cog.start_crawling.start()
            else:
                logger.error("Crawler cog not found.")

        nefarious_cog = bot.get_cog('Nefarious')
        if nefarious_cog:
            if bot.config['features'].get('fullz', False):
                nefarious_cog.update_fullz_embed_task.start()
            if bot.config['features'].get('stealer', False):
                nefarious_cog.update_stealer_embed_task.start()
        else:
            logger.error("Nefarious cog not found.")

        print('')
        print(f"[{G}!{X}] Logged in: {G}{bot.user.name}{X}")
        print(f"[{G}!{X}] Discord ID: {G}{bot.user.id}{X}")
        print(f"[{G}!{X}] Discord.py: {G}{discord.__version__}{X}")
        print('')
        print(f"    [{G}!{X}] Owner: {G}{owner.name}#{owner.discriminator}{X}")
        print(f"    [{G}!{X}] Storage: {G}portlords.db{X}")
        print(f"    [{G}!{X}] Version: {G}{config['discord']['version']}{X}")
        print('')
        print(f"    [{G}!{X}] Users: {G}{database_user_count}{X}")
        print(f"    [{G}!{X}] Commands: {G}{total_commands}{X}")
        print('')
        print(f"    [{G}!{X}] CPU: {G}{cpu_usage:.2f}%{X}")
        print(f"    [{G}!{X}] Memory: {G}{memory_usage:.2f} MB{X}")
        print(f"    [{G}!{X}] Uptime: {G}{uptime:.2f}s{X}")
        print('')
        for feature, enabled in config['features'].items():
            print(f"    [{G}!{X}] {feature}: [{G}{enabled}{X}]")
        print('')
        print(f"[{G}!{X}] Loaded Cogs: {G}{', '.join(loaded_cogs)}{X}")

        if missing_cogs:
            print(f"[{R}!{X}] Missing Cogs: {R}{', '.join(missing_cogs)}{X}")

    except Exception as ex:
        logger.error(f"An error occurred during bot startup: {ex}", exc_info=True)

# --- Bot Commands ---

@bot.command(name='reload')
@commands.is_owner()
async def reload(ctx: commands.Context, cog: str = None) -> None:
    try:
        if cog:
            cog = f"cogs.{cog}"
            try:
                bot.unload_extension(cog)
            except commands.ExtensionNotLoaded:
                pass
            bot.reload_extension(cog)
            await ctx.send(f"`Reloaded cog: {cog}`")
            logger.info(f"Reloaded cog: {cog}")
        else:
            loaded_cogs, _ = load_cogs()
            for cog in loaded_cogs:
                try:
                    bot.unload_extension(cog)
                except commands.ExtensionNotLoaded:
                    pass
                bot.reload_extension(cog)
            await ctx.send("`Reloaded all cogs.`")
            logger.info("Reloaded all cogs.")

    except Exception as e:
        await ctx.send(f"`Failed to reload cog {cog}`: {e}")
        logger.error(f"An unexpected error occurred while reloading cog {cog}: {e}", exc_info=True)

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    bot.start_time = time.time()
    bot.run(token)
