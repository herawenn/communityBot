import discord
from discord.ext import commands
import logging
from discord.ui import View, Button

logger = logging.getLogger(__name__)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.commands = {
            "General": [cmd for cmd in bot.commands if cmd.cog_name == "General"],
            "Osint": [cmd for cmd in bot.commands if cmd.cog_name == "Osint"],
            "Hacking": [cmd for cmd in bot.commands if cmd.cog_name == "Hacking"],
            "Crypto": [cmd for cmd in bot.commands if cmd.cog_name == "Crypto"],
        }

    @commands.command(name="help", help="Displays information about the bot and its commands.")
    async def help(self, ctx):
        try:
            embed = self.create_help_embed(ctx)
            view = self.create_view(ctx)
            await ctx.send(embed=embed, view=view)
        except discord.HTTPException as e:
            logger.error(f"An HTTP error occurred while sending the help embed: {e}")
            await ctx.send("An error occurred while sending the help embed. Please try again later.")
        except Exception as e:
            logger.error(f"An error occurred while executing the help command: {e}")
            await ctx.send("An error occurred while executing the help command. Please try again later.")

    def create_help_embed(self, ctx):
        embed = discord.Embed(
            title=self.bot.user.name,
            description="`PortLords Discord Bot`",
            color=int(self.bot.config['embeds']['embed_colors']['primary'], 16),
        )
        return embed

    def create_view(self, ctx):
        view = View()
        for category, cmds in self.commands.items():
            button = Button(label=category, style=discord.ButtonStyle.blurple, custom_id=category)
            button.callback = self.command_callback(ctx)
            view.add_item(button)
        return view

    def command_callback(self, ctx):
        async def callback(interaction):
            try:
                category = interaction.data.custom_id
                embed = self.create_command_embed(ctx, category)
                await interaction.response.edit_message(embed=embed)
            except discord.HTTPException as e:
                logger.error(f"An HTTP error occurred while editing the interaction response: {e}")
                await interaction.response.send_message(f"`An error occurred while editing the interaction response. Please try again later.`")
            except Exception as e:
                logger.error(f"An error occurred while executing the command callback: {e}")
                await interaction.response.send_message(f"`An error occurred while executing the command callback. Please try again later.`")
        return callback

    def create_command_embed(self, ctx, category):
        embed = discord.Embed(
            title=f"{category} Commands",
            description="A list of commands in this category.",
            color=int(self.bot.config['embeds']['embed_colors']['primary'], 16),
        )
        for cmd in self.commands[category]:
            embed.add_field(
                name=f"`{ctx.prefix}{cmd.name}`",
                value=f"**:** `{cmd.help or 'No description available.'}`",
                inline=False
            )
        return embed

async def setup(bot):
    await bot.add_cog(Help(bot))
