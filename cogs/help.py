import discord
from bot import has_restricted_role
from discord.ext import commands
import json

with open('config.json') as f:
    config = json.load(f)


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", help="Displays information about the bot.")
    @has_restricted_role()
    async def help_command(self, ctx):
        embed = discord.Embed(
            description="All Available Commands:",
            color=discord.Color(0x6900ff),
        )

        for cmd in self.bot.commands:
            embed.add_field(name=f"`{config['prefix']}{cmd.name}`", value=cmd.help, inline=False)

        embed.set_image(url=config.get('help_image', "https://i.imgur.com/5mp2Siz.png"))
        embed.set_footer(text="From PortLords w Love 2024")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
