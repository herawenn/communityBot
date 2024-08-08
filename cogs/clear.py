import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class Clear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clear", help="Deletes a specified number of messages.")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        logger.info(f"Clear command invoked by {ctx.author} in {ctx.guild} with amount {amount}")

        if amount <= 0:
            await ctx.send("Error: The number of messages to delete must be greater than 0.")
            logger.warning(f"Invalid amount specified by {ctx.author} in {ctx.guild}: {amount}")
            return

        try:
            await self.delete_messages(ctx, amount)
        except discord.Forbidden:
            await self.handle_forbidden_error(ctx)
        except discord.HTTPException as e:
            await self.handle_http_error(ctx, e)
        except Exception as e:
            await self.handle_unexpected_error(ctx, e)

    async def delete_messages(self, ctx, amount):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"`{amount} messages removed`", delete_after=5)
        logger.info(f"Successfully removed {amount} messages in {ctx.guild} by {ctx.author}")

    async def handle_forbidden_error(self, ctx):
        await ctx.send("Error: I do not have permission to delete messages in this channel.")
        logger.error(f"Missing permissions to delete messages in {ctx.guild} by {ctx.author}")

    async def handle_http_error(self, ctx, e):
        await ctx.send(f"Error: Failed to delete messages. {e}")
        logger.error(f"HTTP exception occurred while deleting messages in {ctx.guild} by {ctx.author}: {e}")

    async def handle_unexpected_error(self, ctx, e):
        await ctx.send(f"Error: An unexpected error occurred. Details: {e}")
        logger.error(f"Unexpected error occurred while deleting messages in {ctx.guild} by {ctx.author}: {e}", exc_info=True)

    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await self.handle_missing_permissions_error(ctx)
        elif isinstance(error, commands.BadArgument):
            await self.handle_bad_argument_error(ctx)
        else:
            await self.handle_unexpected_error(ctx, error)

    async def handle_missing_permissions_error(self, ctx):
        await ctx.send("Error: You do not have permission to use this command.")
        logger.warning(f"Missing permissions for {ctx.author} in {ctx.guild}")

    async def handle_bad_argument_error(self, ctx):
        await ctx.send("Error: Please provide a valid number of messages to delete.")
        logger.warning(f"Invalid argument provided by {ctx.author} in {ctx.guild}")

async def setup(bot):
    await bot.add_cog(Clear(bot))
