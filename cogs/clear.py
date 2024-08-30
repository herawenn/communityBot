import discord
import asyncio
from discord.ext import commands
import logging
from discord.app_commands import AppCommandError, MissingPermissions
from helpers import send_and_delete

logger = logging.getLogger(__name__)

class Clear(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.delete_command_delay: int = bot.config['settings']['delete_command_delay']
        self.delete_commands: bool = bot.config['settings']['delete_commands']
        self.delete_responses: bool = bot.config['settings']['delete_responses']
        self.delete_response_delay: int = bot.config['settings']['delete_response_delay']

    @commands.command(name="clear", help="Deletes a specified number of messages. Requires 'Manage Messages' permissions.")
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def clear(self, ctx: commands.Context, amount: int) -> None:
        try:
            logger.info(f"Clear command invoked by {ctx.author} in {ctx.guild} with amount {amount}")

            if amount <= 0:
                await send_and_delete(ctx, "`Error: The number of messages to delete must be greater than 0.`",
                                    delay=self.bot.config['settings']['delete_errors_delay'],
                                    delete_type='error')
                return

            deleted_messages = await ctx.channel.purge(limit=amount + 1)
            await send_and_delete(ctx, f"`{len(deleted_messages) - 1} messages removed.`",
                                delay=self.bot.config['settings']['delete_response_delay'])
            logger.info(f"Successfully removed {len(deleted_messages) - 1} messages in {ctx.guild} by {ctx.author}")

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Error occurred while deleting messages in {ctx.guild} by {ctx.author}: {e}")
            await send_and_delete(ctx, "`Error: I do not have the required permissions to delete messages.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')
        except Exception as e:
            logger.error(f"An unexpected error occurred in clear command: {e}", exc_info=True)
            await send_and_delete(ctx, "`An unexpected error occurred. Please try again later.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')

    @clear.error
    async def clear_error(self, ctx: commands.Context, error: AppCommandError) -> None:
        try:
            if isinstance(error, MissingPermissions):
                await send_and_delete(ctx, "`Error: You do not have permission to use this command.`",
                                    delay=self.bot.config['settings']['delete_errors_delay'],
                                    delete_type='error')
                logger.warning(f"Missing permissions for {ctx.author} in {ctx.guild}")
            elif isinstance(error, commands.BadArgument):
                await send_and_delete(ctx, "`Error: Please provide a valid number of messages to delete. For example: ..clear 5`",
                                    delay=self.bot.config['settings']['delete_errors_delay'],
                                    delete_type='error')
                logger.warning(f"Invalid argument provided by {ctx.author} in {ctx.guild}")
            else:
                logger.error(f"Unexpected error occurred: {error}")
                await send_and_delete(ctx, "`Error: An unexpected error occurred. Please try again later.`",
                                    delay=self.bot.config['settings']['delete_errors_delay'],
                                    delete_type='error')
        except Exception as e:
            logger.error(f"An unexpected error occurred in clear_error: {e}", exc_info=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Clear(bot))
