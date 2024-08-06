from discord.ext import commands
import os
import json
from bot import logger

with open('config.json') as f:
    config = json.load(f)

class Reload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reload", help="Reloads the bot's code (development only).")
    @commands.is_owner()
    async def reload(self, ctx):
        logger.info(f"Reload command invoked by {ctx.author} in {ctx.guild}")
        try:
            await ctx.send(f"`Reloading, please wait...`")
            logger.info(f"Reloading the bot as requested by {ctx.author} in {ctx.guild}")
            await self.bot.close()
            os.system("python3 bot.py")
        except Exception as e:
            logger.error(f"Error occurred while reloading the bot: {e}", exc_info=True)
            await ctx.send(f"Error: An unexpected error occurred while reloading the bot. Details: {e}")

async def setup(bot):
    await bot.add_cog(Reload(bot))