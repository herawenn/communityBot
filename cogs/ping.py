from discord.ext import commands
from bot import logger

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping", help="Displays the bot's latency.")
    async def ping_command(self, ctx):
        await ctx.send(f"`Ping: {self.bot.latency * 1000:.2f}ms`")


async def setup(bot):
    await bot.add_cog(Ping(bot))
