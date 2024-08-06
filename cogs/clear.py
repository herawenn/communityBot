import discord
from discord.ext import commands
import json

with open('config.json') as f:
    config = json.load(f)

class Clear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clear", help="Deletes a specified number of messages.")
    @commands.has_permissions(manage_messages=True)
    async def clear_command(self, ctx, amount: int):
        if amount <= 0:
            await ctx.send("Error: The number of messages to delete must be greater than 0.")
            return

        try:
            await ctx.channel.purge(limit=amount + 1)
            await ctx.send(f"`{amount} messages removed`", delete_after=5)
        except discord.Forbidden:
            await ctx.send("Error: I do not have permission to delete messages in this channel.")
        except discord.HTTPException as e:
            await ctx.send(f"Error: Failed to delete messages. {e}")

    @clear_command.error
    async def clear_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Error: You do not have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Error: Please provide a valid number of messages to delete.")
        else:
            await ctx.send(f"Error: An unexpected error occurred. Details: {error}")

async def setup(bot):
    await bot.add_cog(Clear(bot))
