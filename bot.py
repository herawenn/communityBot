import asyncio
import logging
import os
import json
import psutil
from itertools import cycle
from typing import List, Tuple
import discord
from discord.ext import commands, tasks
import time
import random
import datetime
from dotenv import load_dotenv

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

    required_keys = ['discord', 'identifiers', 'paths', 'settings', 'apis', 'embeds', 'logging', 'moderation']
    for key in required_keys:
        if key not in config:
            logging.error(f"Missing required key '{key}' in {config_path}")
            return None

    config['discord']['token'] = os.getenv('DISCORD_TOKEN', config['discord'].get('token', ''))
    config['apis']['shodan']['api_key'] = os.getenv('SHODAN_API_KEY', config['apis']['shodan'].get('api_key', ''))
    config['apis']['dehashed']['api_key'] = os.getenv('DEHASHED_API_KEY', config['apis']['dehashed'].get('api_key', ''))
    config['apis']['gemini']['api_key'] = os.getenv('GEMINI_API_KEY', config['apis']['gemini'].get('api_key', ''))

    return config

config = load_config(CONFIG_PATH)

if config is None:
    raise Exception("Failed to load configuration")

if not config['discord']['token']:
    raise ValueError("Discord token is not set in the configuration file.")

LOGS_DIR = config['logging']['log_path']
LOG_FILE_NAME = config['logging']['log_file_name']
LOG_LEVEL = config['logging']['log_level']

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(os.path.join(LOGS_DIR, LOG_FILE_NAME), mode='w', encoding='utf-8'),
    logging.StreamHandler()
])
logger = logging.getLogger(__name__)

# --- Bot Setup ---

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config['discord']['prefix'], intents=intents, help_command=None)
bot.config = config

# --- Cog Loading ---

async def load_cogs() -> Tuple[List[str], List[str]]:
    loaded_cogs = []
    missing_cogs = []
    cogs_dir = bot.config['paths']['cogs_directory']

    cogs_order = [
        'cogs.database',
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
        'cogs.clear',
        'cogs.impersonate',
        'cogs.logging',
        'cogs.roles',
        'cogs.obfuscate',
        'cogs.quiz',
        'cogs.builder'
    ]

    for cog_name in cogs_order:
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
            logger.error(f"An unexpected error occurred while loading cog {cog_name}: {e}", exc_info=True)
            missing_cogs.append(cog_name)

    return loaded_cogs, missing_cogs

# --- Load JSON Files ---

def load_json_files(directory: str) -> dict:
    data = {}
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, 'r') as f:
                    data[filename[:-5]] = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to load JSON file: {file_path}, Error: {e}")
            except FileNotFoundError as e:
                logger.error(f"JSON file not found: {file_path}, Error: {e}")
    return data

# --- Bot Tasks ---

STATUSES = [
    (discord.ActivityType.listening, "the TOR Relay"),
    (discord.ActivityType.watching, "🌐 Hated dl it"),
    (discord.ActivityType.listening, "-p 3306"),
    (discord.ActivityType.watching, "PortLords © 2024"),
    (discord.ActivityType.watching, "Lego not let go 🙃"),
    (discord.ActivityType.playing, "With a 🐭 rat"),
    (discord.ActivityType.watching, "🚀 Above and Beyond"),
    (discord.ActivityType.listening, "localhost"),
    (discord.ActivityType.watching, "GPT Infect You"),
    (discord.ActivityType.playing, "w 🔒 obfuscation"),
    (discord.ActivityType.listening, "🚨 for The FEDs"),
    (discord.ActivityType.playing, "w Herawens 💔")
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

@tasks.loop(hours=24)
async def quiz_task(bot):
    if not bot.config['settings']['quiz_task_enabled']:
        return
    channel_id = int(bot.config['identifiers']['quiz_channel_id'])
    channel = bot.get_channel(channel_id)
    if not channel:
        logger.error("Invalid quiz channel ID in config.json.")
        return
    await bot.get_cog("Quiz").start_quiz(channel)

@quiz_task.before_loop
async def before_quiz_task():
    await bot.wait_until_ready()
    now = datetime.datetime.now()
    next_run = now.replace(hour=12, minute=0, second=0, microsecond=0)
    if next_run < now:
        next_run += datetime.timedelta(days=1)
    await asyncio.sleep((next_run - now).total_seconds())

@tasks.loop(hours=24)
async def send_security_tip():
    try:
        channel = bot.get_channel(int(bot.config['identifiers']['security_channel_id']))
        if channel:
            tips = bot.json_data['tips']['tips']
            random_tip = random.choice(tips)
            sent_message = await channel.send(f"**PortLords Tip of the Day:**\n{random_tip}")
            if bot.config['settings']['delete_responses']:
                await asyncio.sleep(bot.config['settings']['delete_response_delay'])
                await sent_message.delete()
    except Exception as e:
        logger.error(f"Error sending security tip: {e}", exc_info=True)

@send_security_tip.before_loop
async def before_send_security_tip():
    await bot.wait_until_ready()
    now = datetime.datetime.now()
    next_run = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
    await asyncio.sleep((next_run - now).total_seconds())

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
                await welcome_channel.send(f"{member.mention}\n`Weve been expecting you`")

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
        send_security_tip.start()
        quiz_task.start(bot)

        loaded_cogs, missing_cogs = await load_cogs()

        guild_count = len(bot.guilds)
        user_count = sum(guild.member_count for guild in bot.guilds)
        latency = bot.latency
        uptime = time.time() - bot.start_time

        total_commands = len(bot.commands)

        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / (1024 * 1024)
        cpu_usage = psutil.cpu_percent(interval=1)

        owner_id = config['identifiers'].get('owner_id')
        if owner_id:
            owner = await bot.fetch_user(owner_id)

        print('')
        print(f"[{G}!{X}] Logged in: {G}{bot.user.name}{X}")
        print(f"[{G}!{X}] Discord ID: {G}{bot.user.id}{X}")
        print(f"[{G}!{X}] Bot Version: {G}{config['discord']['version']}{X}")
        print(f"[{G}!{X}] Discord.py Version: {G}{discord.__version__}{X}")
        print('')
        print(f"    [{G}!{X}] Owner: {G}{owner.name}#{owner.discriminator}{X}")
        print('')
        print(f"    [{G}!{X}] Latency: {G}{latency:.2f}s{X}")
        print(f"    [{G}!{X}] Uptime: {G}{uptime:.2f}s{X}")
        print('')
        print(f"    [{G}!{X}] Mem Usage: {G}{memory_usage:.2f} MB{X}")
        print(f"    [{G}!{X}] CPU Usage: {G}{cpu_usage:.2f}%{X}")
        print('')
        print(f"    [{G}!{X}] Users: {G}{user_count}{X}")
        print(f"    [{G}!{X}] Servers: {G}{guild_count}{X}")
        print(f"    [{G}!{X}] Commands: {G}{total_commands}{X}")
        print('')
        print(f"    [{G}!{X}] Connected: {G}portlords.db{X}")
        print('')
        print(f"[{G}!{X}] Loaded Cogs: {G}{', '.join(loaded_cogs)}{X}")

        if missing_cogs:
            print(f"[{R}!{X}] Missing Cogs: {R}{', '.join(missing_cogs)}{X}")

    except Exception as ex:
        logger.error(f"An error occurred during bot startup: {ex}", exc_info=True)

@bot.event
async def on_command(ctx: commands.Context) -> None:
    try:
        if config['settings']['delete_commands']:
            logger.info(f"Scheduling deletion of command message: {ctx.message.content}")
            await asyncio.sleep(config['settings']['delete_command_delay'])
    except Exception as ex:
        logger.error(f"An error occurred during bot startup: {ex}", exc_info=True)

# --- Bot Commands ---

@bot.command(name='reload')
@commands.is_owner()
@commands.cooldown(1, 60, commands.BucketType.user)
async def reload(ctx: commands.Context, cog: str = None) -> None:
    try:
        if cog:
            cog = f"cogs.{cog}"
            await bot.reload_extension(cog)
            await ctx.send(f"`Reloaded cog: {cog}`")
            logger.info(f"Reloaded cog: {cog}")
        else:
            loaded_cogs, _ = await load_cogs()
            for cog in loaded_cogs:
                await bot.reload_extension(cog)
            await ctx.send("`Reloaded all cogs.`")
            logger.info("Reloaded all cogs.")

        if config['settings']['delete_responses']:
            logger.info(f"Scheduling deletion of response message: {ctx.message.content}")
            await asyncio.sleep(config['settings']['delete_response_delay'])
            try:
                await ctx.message.delete()
                logger.info(f"Deleted response message: {ctx.message.content}")
            except discord.HTTPException as e:
                logger.error(f"Failed to delete response message: {ctx.message.content}, Error: {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred while deleting response message: {e}")
    except commands.ExtensionNotFound:
        await ctx.send(f"`Failed to reload cog {cog}`: Not found")
        logger.error(f"Failed to reload cog {cog}: Not found")
    except commands.ExtensionFailed as e:
        await ctx.send(f"`Failed to reload cog {cog}`: {e}")
        logger.error(f"Failed to reload cog {cog}: {e}", exc_info=True)
    except Exception as e:
        await ctx.send(f"`Failed to reload cog {cog}`: {e}")
        logger.error(f"An unexpected error occurred while reloading cog {cog}: {e}", exc_info=True)

@bot.command(name='report', help="Report a bug, error, or inconsistency. Usage: ..report <your message>")
@commands.cooldown(1, 60, commands.BucketType.user)
async def report_issue(ctx: commands.Context, *, message: str) -> None:
    report_channel_id = int(config['identifiers']['report_channel_id'])
    report_channel = bot.get_channel(report_channel_id)
    if report_channel:
        await report_channel.send(f"Bug Report from {ctx.author.mention}:\n```\n{message}\n```")
        await ctx.send("`Thank you for your report! It has been sent to the developers.`", ephemeral=True)
    else:
        logger.error(f"Invalid report channel ID: {report_channel_id}")
        await ctx.send("`An error occurred while processing your report. Please try again later.`", ephemeral=True)

@bot.command(name='testtip', help="Test the security tip of the day by posting one at random in the current channel.")
@commands.cooldown(1, 60, commands.BucketType.user)
async def test_tip(ctx: commands.Context):
    try:

        with open('files/json/tips.json', 'r') as f:
            tips = json.load(f)

        random_tip = random.choice(tips)
        await ctx.send(f"`a friendly reminder from portlords:`\n\n```{random_tip}```")

        if bot.config['settings']['delete_responses']:
            await asyncio.sleep(bot.config['settings']['delete_response_delay'])
            await ctx.message.delete()
    except Exception as e:
        logger.error(f"Error sending security tip: {e}", exc_info=True)
        await ctx.send(f"`An error occurred while sending the security tip.`")

@bot.command(name='tiers', help='Show the tier structure.')
@commands.cooldown(1, 60, commands.BucketType.channel)
async def show_tiers(ctx: commands.Context):
    try:
        tiers = bot.config['tiers']
        guild = ctx.guild

        embed = discord.Embed(title="Tier Structure", color=int(bot.config['embeds']['embed_colors']['primary'], 16))

        for tier in tiers:
            role_name = tier["role_name"]
            role = discord.utils.get(guild.roles, name=role_name)
            role_mention = role.mention if role else role_name
            embed.add_field(name=f" ", value=f"`Tier: {tier['tier_id']} |` {role_mention} `| Points: {tier['required_points']}`", inline=False)

        embed.set_footer(text=bot.config['embeds']['embed_footer'])
        await ctx.send(embed=embed)

    except Exception as e:
        logger.error(f"Error displaying tiers: {e}")
        await ctx.send(f"`An error occurred while displaying tiers.`")

async def main() -> None:
    try:
        bot.start_time = time.time()
        await bot.start(config['discord']['token'])
    except discord.HTTPException as e:
        logger.error(f"Failed to start bot: {e}")
    except Exception as ex:
        logger.error(f"An error occurred during bot startup: {ex}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
