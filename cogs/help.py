import discord
import json
from discord.ext import commands
from bot import logger

with open('config.json') as f:
    config = json.load(f)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", help="Displays information about the bot.")
    async def help_command(self, ctx):
        logger.info(f"Help command invoked by {ctx.author} in {ctx.guild}")
        try:
            embed = discord.Embed(
                description="All Available Commands:",
                color=discord.Color(0x6900ff),
            )

            for cmd in self.bot.commands:
                embed.add_field(name=f"`{config['prefix']}{cmd.name}`", value=cmd.help or "No description available.", inline=False)

            embed.set_image(url=config.get('help_image', "https://i.imgur.com/5mp2Siz.png"))
            embed.set_footer(text="From PortLords w Love 2024")

            await ctx.send(embed=embed)
            logger.info(f"Help command executed successfully in {ctx.guild}")
        except Exception as e:
            logger.error(f"An error occurred in the help command: {e}", exc_info=True)
            await ctx.send("An error occurred while executing the help command. Please try again later.")

async def setup(bot):
    await bot.add_cog(Help(bot))
