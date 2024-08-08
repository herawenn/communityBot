import discord
from discord.ext import commands
import json
from bot import logger


with open('config.json') as f:
    config = json.load(f)


class Clear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clear", help="Deletes a specified number of messages.")
    @commands.has_permissions(manage_messages=True)
    async def clear_command(self, ctx, amount: int):
        logger.info(f"Clear command invoked by {ctx.author} in {ctx.guild} with amount {amount}")

        if amount <= 0:
            await ctx.send("Error: The number of messages to delete must be greater than 0.")
            logger.warning(f"Invalid amount specified by {ctx.author} in {ctx.guild}: {amount}")
            return

        try:
            await ctx.channel.purge(limit=amount + 1)
            await ctx.send(f"`{amount} messages removed`", delete_after=5)
            logger.info(f"Successfully removed {amount} messages in {ctx.guild} by {ctx.author}")
        except discord.Forbidden:
            await ctx.send("Error: I do not have permission to delete messages in this channel.")
            logger.error(f"Missing permissions to delete messages in {ctx.guild} by {ctx.author}")
        except discord.HTTPException as e:
            await ctx.send(f"Error: Failed to delete messages. {e}")
            logger.error(f"HTTP exception occurred while deleting messages in {ctx.guild} by {ctx.author}: {e}")
        except Exception as e:
            await ctx.send(f"Error: An unexpected error occurred. Details: {e}")
            logger.error(f"Unexpected error occurred while deleting messages in {ctx.guild} by {ctx.author}: {e}", exc_info=True)

    @clear_command.error
    async def clear_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Error: You do not have permission to use this command.")
            logger.warning(f"Missing permissions for {ctx.author} in {ctx.guild}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Error: Please provide a valid number of messages to delete.")
            logger.warning(f"Invalid argument provided by {ctx.author} in {ctx.guild}")
        else:
            await ctx.send(f"Error: An unexpected error occurred. Details: {error}")
            logger.error(f"Unexpected error in clear command by {ctx.author} in {ctx.guild}: {error}", exc_info=True)


async def setup(bot):
    await bot.add_cog(Clear(bot))
