import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", help="Displays information about the bot and its commands.")
    async def help(self, ctx):
        try:
            embed = self.create_help_embed(ctx)
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"An error occurred while executing the help command: {e}")
            await ctx.send("An error occurred while executing the help command. Please try again later.")

    def create_help_embed(self, ctx):
        embed = discord.Embed(
            title="Community Help Command",
            description="Here are the available commands:",
            color=discord.Color(0x6900ff),
        )

        for cmd in self.bot.commands:
            embed.add_field(
                name=f"`{ctx.prefix}{cmd.name}`",
                value=f"**:** `{cmd.help or 'No description available.'}`",
                inline=False
            )

        embed.set_image(url="https://i.imgur.com/5mp2Siz.png")
        embed.set_footer(text="From PortLords w Love 2024")

        return embed

async def setup(bot):
    await bot.add_cog(Help(bot))
