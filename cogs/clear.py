import discord
import asyncio
from discord.ext import commands
import logging
from discord.app_commands import AppCommandError, MissingPermissions

logger = logging.getLogger(__name__)

class Clear(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.delete_command_delay: int = bot.config['settings']['delete_command_delay']
        self.delete_commands: bool = bot.config['settings']['delete_commands']

    @commands.command(name="clear", help="Deletes a specified number of messages.")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, amount: int) -> None:
        logger.info(f"Clear command invoked by {ctx.author} in {ctx.guild} with amount {amount}")

        if amount <= 0:
            error_message = await ctx.send("Error: The number of messages to delete must be greater than 0.")
            logger.warning(f"Invalid amount specified by {ctx.author} in {ctx.guild}: {amount}")
            if self.delete_commands:
                await error_message.delete(delay=self.delete_command_delay)
            return
        try:
            deleted_messages = await ctx.channel.purge(limit=amount + 1)
            response_message = await ctx.send(f"`{len(deleted_messages)-1} messages removed`")
            if self.delete_commands:
                await asyncio.sleep(self.delete_command_delay)
                await response_message.delete()
            logger.info(f"Successfully removed {len(deleted_messages)-1} messages in {ctx.guild} by {ctx.author}")
        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Error occurred while deleting messages in {ctx.guild} by {ctx.author}: {e}")
            error_message = await ctx.send("Error: An unexpected error occurred. Please try again later.")
            if self.delete_commands:
                await asyncio.sleep(self.delete_command_delay)
                await error_message.delete()

    @clear.error
    async def clear_error(self, ctx: commands.Context, error: AppCommandError) -> None:
        if isinstance(error, MissingPermissions):
            error_message = await ctx.send("Error: You do not have permission to use this command.")
            logger.warning(f"Missing permissions for {ctx.author} in {ctx.guild}")
            if self.delete_commands:
                await error_message.delete(delay=self.delete_command_delay)
        elif isinstance(error, commands.BadArgument):
            error_message = await ctx.send("Error: Please provide a valid number of messages to delete.")
            logger.warning(f"Invalid argument provided by {ctx.author} in {ctx.guild}")
            if self.delete_commands:
                await error_message.delete(delay=self.delete_command_delay)
        else:
            logger.error(f"Unexpected error occurred: {error}")
            error_message = await ctx.send("Error: An unexpected error occurred. Please try again later.")
            if self.delete_commands:
                await error_message.delete(delay=self.delete_command_delay)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Clear(bot))
