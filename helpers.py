import asyncio
import logging
import discord
import re
import subprocess
import json
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

async def send_and_delete(ctx, content=None, embed=None, file=None, delay=None, delete_type='response'):
    try:
        if delete_type == 'command' and ctx.bot.config['settings']['delete_commands']:
            await asyncio.sleep(ctx.bot.config['settings']['delete_command_delay'])
            await ctx.message.delete()

        if content or embed or file:
            message = await ctx.send(content=content, embed=embed, file=file)

            if delete_type == 'response' and ctx.bot.config['settings']['delete_responses']:
                await asyncio.sleep(delay)
                await message.delete()

            return message
    except Exception as e:
        logger.error(f"An error occurred in send_and_delete: {e}")

def is_valid_integer(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

def is_valid_ip_address(ip):
    regex = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    if re.match(regex, ip):
        return True
    else:
        return False

def validate_scan_id(scan_id):
    try:
        int(scan_id)
        return True
    except ValueError:
        return False

def validate_exploit_id(exploit_id):
    try:
        int(exploit_id)
        return True
    except ValueError:
        return False

def create_embed(title, description, color_key='primary', fields=None, footer_text=None, image_url=None, config=None):
    if config is None:
        logger.error("Error: Configuration not provided to create_embed")
        return None

    embed = discord.Embed(title=title, description=description, color=int(config['embeds']['embed_colors'][color_key], 16))

    if footer_text is None:
        footer_text = config['embeds']['embed_footer']
    embed.set_footer(text=footer_text)

    if image_url is None:
        image_url = config['embeds']['embed_banner']
    embed.set_image(url=image_url)

    if fields:
        for field in fields:
            embed.add_field(name=field[0], value=field[1], inline=field[2] if len(field) > 2 else False)

    return embed
