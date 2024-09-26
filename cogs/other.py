import discord
from discord.ext import commands
import logging
import tempfile
import aiohttp
from typing import Dict
import random
import io
import os
from PIL import Image
from helpers import send_and_delete, create_embed # type:ignore

logger = logging.getLogger(__name__)

class Other(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.original_username = bot.user.name
        self.original_avatar = bot.user.avatar.url
        self.delete_command_delay = self.bot.config['settings']['delete_command_delay']
        self.delete_commands = self.bot.config['settings']['delete_commands']
        self.delete_responses = self.bot.config['settings']['delete_responses']
        self.delete_response_delay = self.bot.config['settings']['delete_response_delay']
        self.delete_errors = self.bot.config['settings']['delete_errors']
        self.delete_errors_delay = self.bot.config['settings']['delete_errors_delay']
        self.db = self.bot.get_cog("Database")

    @commands.command(name='tiers', help='Show the tier structure.')
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def show_tiers(self, ctx: commands.Context):
        try:
            tiers = await self.db.get_all_tiers()
            guild = ctx.guild

            embed = create_embed(title="Tier Structure",
                                  description="",
                                  color_key='primary',
                                  config=self.bot.config
                                  )

            for tier in tiers:
                role_name = tier[2]
                role = discord.utils.get(guild.roles, name=role_name)
                role_mention = role.mention if role else role_name
                embed.add_field(name=f"**Tier {tier[0]}: {tier[1]}**", value=f"`Required Points: {tier[3]}`\n{role_mention}", inline=False)

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error displaying tiers: {e}", exc_info=True)
            await ctx.send(f"`An error occurred while displaying tiers.`")

    @commands.command(name='impersonate', help="Usage: ..impersonate <user> <message>")
    @commands.is_owner()
    async def impersonate(self, ctx, user: discord.User, *, message: str):
        try:
            self.original_username = self.bot.user.name
            self.original_avatar = self.bot.user.avatar.url

            await self.bot.user.edit(username=user.display_name)

            avatar_url = user.avatar.url
            avatar_data = await self.get_avatar_data(avatar_url)

            if avatar_data:
                await self.bot.user.edit(avatar=avatar_data)

            await send_and_delete(ctx, content=message, delay=self.delete_response_delay)
            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

        except Exception as e:
            logger.error(f"Error during impersonation: {e}", exc_info=True)

            await self.bot.user.edit(username=self.original_username)
            original_avatar_data = await self.get_avatar_data(self.original_avatar)
            if original_avatar_data:
                await self.bot.user.edit(avatar=original_avatar_data)

            await send_and_delete(ctx, content="`Failed to impersonate the user. An error occurred.`", delay=self.delete_errors_delay, delete_type='error')

    async def get_avatar_data(self, avatar_url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()
                        img = Image.open(io.BytesIO(image_bytes))
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                            img.save(temp_file)
                            temp_file_path = temp_file.name
                            return temp_file_path
                    else:
                        logger.error(f"Failed to fetch avatar data: {resp.status} - {await resp.text()}")
                        return None
        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch avatar data: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching avatar data: {e}", exc_info=True)
            return None

    @commands.command(name="clear", help="Deletes a specified number of messages. Usage: ..clear <amount>")
    @commands.is_owner()
    async def clear(self, ctx: commands.Context, amount: int) -> None:
        try:
            logger.info(f"Clear command invoked by {ctx.author} in {ctx.guild} with amount {amount}")

            if amount <= 0:
                await send_and_delete(ctx, content="`Error: The number of messages to delete must be greater than 0.`",
                                    delay=self.delete_errors_delay,
                                    delete_type='error')
                return

            deleted_messages = await ctx.channel.purge(limit=amount + 1)
            await send_and_delete(ctx, content=f"`{len(deleted_messages) - 1} messages removed.`",
                                delay=self.delete_response_delay)
            logger.info(f"Successfully removed {len(deleted_messages) - 1} messages in {ctx.guild} by {ctx.author}")

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Error occurred while deleting messages in {ctx.guild} by {ctx.author}: {e}")
            await send_and_delete(ctx, content="`Error: I do not have the required permissions to delete messages.`",
                                delay=self.delete_errors_delay,
                                delete_type='error')
        except Exception as e:
            logger.error(f"An unexpected error occurred in clear command: {e}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again later.`", delay=self.delete_errors_delay, delete_type='error')

    @commands.command(name="proxy", help="Retrieves a list of proxies.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def proxy_command(self, ctx: commands.Context) -> None:
        try:
            proxy_api_url = os.getenv('PROXY_API')
            max_proxies_to_send = 10  # Adjust

            async with aiohttp.ClientSession() as session:
                async with session.get(proxy_api_url) as response:
                    if response.status == 200:
                        proxy_list = await response.text()
                        proxies = proxy_list.splitlines()
                        selected_proxies = random.sample(proxies, min(max_proxies_to_send, len(proxies)))

                        proxy_text = "```\n" + "\n".join(selected_proxies) + "\n```"

                        embed = create_embed(title="Proxies",
                                          description=proxy_text,
                                          color_key='primary',
                                          config=self.bot.config
                                          )

                        await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)
                        logger.info(f"Proxy command executed successfully in {ctx.guild}")
                    else:
                        logger.error(f"Proxy API request failed with status code {response.status}")
                        await send_and_delete(ctx,
                                              content="`Error: Could not retrieve proxy list. Please try again later.`",
                                              delay=self.delete_errors_delay, delete_type='error')

            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

        except Exception as e:
            logger.error(f"An error occurred in proxy_command: {e}", exc_info=True)
            await send_and_delete(ctx, content="`An error occurred while retrieving the proxy list. Please try again later.`", delay=self.delete_errors_delay, delete_type='error')

    @proxy_command.error
    async def proxy_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(ctx, content=f"`This command is on cooldown. Please try again in {retry_after:.2f} seconds.`",
                            delay=self.bot.config['settings']['delete_errors_delay'],
                            delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again later.`",
                            delay=self.bot.config['settings']['delete_errors_delay'],
                            delete_type='error')

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Other(bot))
