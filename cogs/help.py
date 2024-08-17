import discord
from discord.ext import commands
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.delete_command_delay = bot.config['settings']['delete_command_delay']
        self.delete_commands = bot.config['settings']['delete_commands']
        self.admin_id = int(bot.config['identifiers']['admin_id'])

        logger.info("Help cog initialized.")

    @commands.command(name="help", help="Displays information about the bot and its commands.")
    async def help_command(self, ctx: commands.Context) -> None:
        try:
            embed = self.create_main_help_embed(ctx.author.id)
            help_message = await ctx.send(embed=embed, ephemeral=True)

            await self.add_reactions(help_message)

        except (discord.HTTPException, discord.Forbidden) as e:
            logger.error(f"An error occurred while managing the help message: {e}")
            error_message = await ctx.send("An error occurred with the help menu. Try again later.", ephemeral=True)
            if self.delete_commands:
                await error_message.delete(delay=self.delete_command_delay)
        except Exception as e:
            logger.error(f"An unexpected error occurred in the help command: {e}", exc_info=True)
            error_message = await ctx.send("An error occurred. Please try again later.", ephemeral=True)
            if self.delete_commands:
                await error_message.delete(delay=self.delete_command_delay)

    def create_main_help_embed(self, user_id: int) -> discord.Embed:
        embed = discord.Embed(
            title=self.bot.user.name,
            description="`Welcome to the PortLords Discord bot.`",
            color=int(self.bot.config['embeds']['embed_colors']['primary'], 16)
        )
        embed.add_field(name="About", value="""```You Cyber Security Companion\n* identify vulnerabilities with Shodan\n* download exploits for targeted attacks\n* leverage Hashcat, Hydra, John, and more!```""", inline=False)
        embed.set_footer(text=self.bot.config['embeds']['embed_footer'])
        embed.set_image(url=self.bot.config['embeds']['embed_banner'])

        if user_id == self.admin_id:
            embed.add_field(name="Admin Commands", value="""
            **`embeds`** = Manage embeds for different channels.
            **`verification`** = Manage user verification.
            **`reload`** = Reload cogs.
            """, inline=False)

        return embed

    async def add_reactions(self, message: discord.Message) -> None:
        reactions = ['🔒', '🛡️', '🛠️', '🆘', '❌']
        for reaction in reactions:
            await message.add_reaction(reaction)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User) -> None:
        if user.bot:
            return

        message = reaction.message
        if message.author != self.bot.user:
            return

        category_mapping = {
            '🔒': "Security",
            '🛡️': "Moderation",
            '🛠️': "Tools",
            '🆘': "Support",
            '❌': "Close"
        }

        category = category_mapping.get(str(reaction.emoji))
        if category:
            if category == "Close":
                await message.delete()
            else:
                new_embed = self.create_help_embed(category, user.id)
                await message.edit(embed=new_embed)
                await message.clear_reactions()
                await self.add_reactions(message)

    def create_help_embed(self, category: Optional[str] = None, user_id: int = None) -> discord.Embed:
        embed = discord.Embed(
            title=self.bot.user.name,
            description="`PortLords Discord Bot`",
            color=int(self.bot.config['embeds']['embed_colors']['primary'], 16)
        )
        embed.set_footer(text=self.bot.config['embeds']['embed_footer'])
        embed.set_image(url=self.bot.config['embeds']['embed_banner'])

        if category == "Security":
            embed.add_field(name="**Exploitation Commands**", value="""
            **`categories`** - `List exploit categories.`
            **`exploits`** - `Search exploits by keyword.`
            **`download`** - `Download source code for a specific exploit.`
            **`shodan`** - `Search for devices and vulnerabilities.`
            """, inline=False)
        elif category == "Moderation":
            embed.add_field(name="**Moderation Commands**", value="""
            **`kick`** - `Kick a user from the server.`
            **`ban`** - `Ban a user from the server.`
            **`unban`** - `Unban a user from the server.`
            **`mute`** - `Mute a user in the server.`
            **`unmute`** - `Unmute a user in the server.`
            **`clear`** - `Clear a certain number of messages.`
            **`warn`** - `Warn a user for misbehavior.`
            """, inline=False)
        elif category == "Tools":
            embed.add_field(name="**Tools Commands**", value="""
            **`obfuscate`** - `Obfuscate code to make it harder to read.`
            **`crack`** - `Attempt to crack a hashed password.`
            **`phish`** - `Create a phishing page.`
            """, inline=False)
        elif category == "Support":
            embed.add_field(name="**Support Commands**", value="""
            **`chat`** - `Interact with the PortLordsAI model.`
            **`help`** - `Displays information about the bot.`
            """, inline=False)

        if user_id == self.admin_id:
            embed.add_field(name="**Admin Commands**", value="""
            **`embeds`** - `Manage embeds for different channels.`
            **`verification`** - `Manage user verification.`
            **`reload`** - `Reload cogs.`
            """, inline=False)

        return embed

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))
