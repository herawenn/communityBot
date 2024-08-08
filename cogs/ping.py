from discord.ext import commands
from bot import logger


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping", help="Displays the bot's latency.")
    async def ping_command(self, ctx):
        logger.info(f"Ping command invoked by {ctx.author} in {ctx.guild}")
        try:
            latency = self.bot.latency * 1000
            await ctx.send(f"`Ping: {latency:.2f}ms`")
            logger.info(f"Ping command executed successfully in {ctx.guild}")
        except Exception as e:
            logger.error(f"An error occurred in the ping command: {e}")
            await ctx.send("An error occurred while executing the ping command. Please try again later.")


async def setup(bot):
    await bot.add_cog(Ping(bot))
