import discord
from discord.ext import commands
import aiohttp
import asyncio
import logging
import json
import os
import tempfile
from helpers import send_and_delete

logger = logging.getLogger(__name__)

CONFIG_PATH = 'files/json/config.json'

def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config

config = load_config(CONFIG_PATH)

class Impersonate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.original_username = bot.user.name
        self.original_avatar = bot.user.avatar.url

    @commands.command(name='impersonate')
    @commands.is_owner()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def impersonate(self, ctx, user: discord.User, *, message: str):
        try:
            self.original_username = self.bot.user.name
            self.original_avatar = self.bot.user.avatar.url

            await self.bot.user.edit(username=user.display_name)

            avatar_url = user.avatar.url
            avatar_data = await self.get_avatar_data(avatar_url)

            if avatar_data:
                await self.bot.user.edit(avatar=avatar_data)

            await send_and_delete(ctx, message, delay=self.bot.config['settings']['delete_response_delay'])

            await asyncio.sleep(10)
            await self.bot.user.edit(username=self.original_username)
            original_avatar_data = await self.get_avatar_data(self.original_avatar)

            if original_avatar_data:
                await self.bot.user.edit(avatar=original_avatar_data)

        except discord.HTTPException as e:
            logger.error(f"Failed to impersonate user: {e}")
            await send_and_delete(ctx, "`Failed to impersonate the user. Please check the bot's permissions and try again.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            await send_and_delete(ctx, "`An unexpected error occurred. Please try again later.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')

    async def get_avatar_data(self, avatar_url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as resp:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                        temp_file.write(await resp.read())
                        temp_file_path = temp_file.name
                        return temp_file_path
        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch avatar data: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching avatar data: {e}", exc_info=True)
            return None

async def setup(bot):
    await bot.add_cog(Impersonate(bot))
