import discord
import asyncio
from discord.ext import commands
import logging
from typing import Dict, Optional, Union

from discord.app_commands import AppCommandError

logger = logging.getLogger(__name__)

class Help(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.help_messages: Dict[int, discord.Message] = {}

        logger.info("Help cog initialized.")

    @commands.command(name="help", help="Displays information about the bot and its commands.")
    async def help_command(self, ctx: commands.Context) -> None:
        try:
            embed = self.create_main_help_embed()
            help_message = await ctx.send(embed=embed)
            self.help_messages[ctx.author.id] = help_message

            await self.add_main_help_reactions(help_message)

            def check(reaction: discord.Reaction, user: discord.Member) -> bool:
                return (user == ctx.author
                        and str(reaction.emoji) in ("⚙️", "💻", "🌐", "⬅️", "❌"))

            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60.0)
                except asyncio.TimeoutError:
                    break

                if str(reaction.emoji) == "❌":
                    await help_message.delete()
                    del self.help_messages[ctx.author.id]
                    break

                category = self.get_category_from_reaction(reaction)
                if category:
                    await help_message.clear_reactions()
                    new_embed = self.create_help_embed(category)
                    await help_message.edit(embed=new_embed)
                    await self.add_navigation_reactions(help_message)
                elif str(reaction.emoji) == "⬅️":
                    await help_message.clear_reactions()
                    embed = self.create_main_help_embed()
                    await help_message.edit(embed=embed)
                    await self.add_main_help_reactions(help_message)

        except (discord.HTTPException, discord.Forbidden) as e:
            logger.error(f"An error occurred while managing the help message: {e}")
            await ctx.send("An error occurred with the help menu. Try again later.")
        except Exception as e:
            logger.error(f"An unexpected error occurred in the help command: {e}", exc_info=True)
            await ctx.send("An error occurred. Please try again later.")

    def create_main_help_embed(self) -> discord.Embed:
        embed = discord.Embed(title=self.bot.user.name, description="`Welcome to the PortLords Discord Bot.`\n`React to view a specific category.`\n\n⚙️ `= General` **`|`** 💻 `= Hacking` **`|`** 🌐 `= Exploits`", color=int(self.bot.config['embeds']['embed_colors']['primary'], 16),
        )
        embed.set_footer(text=self.bot.config['embeds']['embed_footer'])
        embed.set_image(url=self.bot.config['embeds']['embed_banner'])
        return embed

    async def add_main_help_reactions(self, message: discord.Message) -> None:
        await message.add_reaction("⚙️")
        await message.add_reaction("💻")
        await message.add_reaction("🌐")
        await message.add_reaction("❌")

    async def add_navigation_reactions(self, message: discord.Message) -> None:
        await message.add_reaction("⬅️")
        await message.add_reaction("❌")

    def get_category_from_reaction(self, reaction: discord.Reaction) -> str:

        category_mapping = {
            "⚙️": "General",
            "💻": "Hacking",
            "🌐": "Exploits"
        }
        return category_mapping.get(str(reaction.emoji))

    def create_help_embed(self, category: Optional[str] = None) -> discord.Embed:

        embed = discord.Embed(title=self.bot.user.name, description="`PortLords Discord Bot`", color=int(self.bot.config['embeds']['embed_colors']['primary'], 16),
        )
        embed.set_footer(text=self.bot.config['embeds']['embed_footer'])
        embed.set_image(url=self.bot.config['embeds']['embed_banner'])

        if category == "General":
            commands_to_show = ["clear", "chat", "reload"]
        elif category == "Hacking":
            commands_to_show = ["crack", "brute", "obfuscate"]
        elif category == "Exploits":
            commands_to_show = ["categories", "exploits", "download"]
        else:
            commands_to_show = self.bot.commands

        for cmd in commands_to_show:
            if isinstance(cmd, str):
                cmd = self.bot.get_command(cmd)
            if cmd:
                field_name = f"**`{cmd.name}`**"
                field_value = f"`{cmd.help or 'No description available.'}`"

                if len(field_value) > 1024:  
                    field_value = field_value[:1021] + "..."

                if len(embed) + len(field_name) + len(field_value) > 6000:
                    logger.warning("Embed character limit reached. Some commands may not be displayed.")
                    break

                embed.add_field(name=field_name, value=field_value, inline=False)

        return embed

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))
