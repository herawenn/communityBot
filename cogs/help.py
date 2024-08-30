import discord
from discord.ext import commands
import logging
from typing import Dict, Optional
import asyncio
import json

logger = logging.getLogger(__name__)

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.delete_command_delay = bot.config['settings']['delete_command_delay']
        self.delete_commands = bot.config['settings']['delete_commands']
        self.delete_responses = bot.config['settings']['delete_responses']
        self.delete_response_delay = bot.config['settings']['delete_response_delay']
        self.delete_errors = bot.config['settings']['delete_errors']
        self.delete_errors_delay = bot.config['settings']['delete_errors_delay']
        self.admin_id = int(bot.config['identifiers']['admin_id'])

        with open("files/json/commands.json", "r") as f:
            self.command_help_data = json.load(f)

    @commands.command(name="help", help="Displays information about the bot and its commands.")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def help_command(self, ctx: commands.Context, command_name: str = None) -> None:
        try:
            if command_name:
                command = self.bot.get_command(command_name)
                if command:
                    embed = self.create_command_help_embed(command)
                else:
                    embed = discord.Embed(title="Command Not Found", description=f"The command `{command_name}` was not found.", color=int(self.bot.config['embeds']['embed_colors']['error'], 16))
                    embed.set_footer(text=self.bot.config['embeds']['embed_footer'])
            else:
                embed = self.create_main_help_embed(ctx.author.id)

            help_message = await ctx.send(embed=embed)

            if not command_name:
                await self.add_reactions(help_message)

            if self.delete_responses:
                await asyncio.sleep(self.delete_response_delay)
                await help_message.delete()

        except (discord.HTTPException, discord.Forbidden) as e:
            logger.error(f"An error occurred while managing the help message: {e}")
            error_message = await ctx.send("An error occurred with the help menu. Try again later.")
            if self.delete_errors:
                await asyncio.sleep(self.delete_errors_delay)
                await error_message.delete()

        except Exception as e:
            logger.error(f"An unexpected error occurred in the help command: {e}", exc_info=True)
            error_message = await ctx.send("An error occurred. Please try again later.")
            if self.delete_errors:
                await asyncio.sleep(self.delete_errors_delay)
                await error_message.delete()

    def create_main_help_embed(self, user_id: int) -> discord.Embed:
        embed = discord.Embed(title=" ", description="```   Your AI Powered Cyber Security Companion\n\n[!] Search credentials with Dehashed\n[!] Identify vulnerabilities with Shodan\n[!] Download exploits with ExploitDB\n[!] Leverage Hashcat, Nmap, John, and more!```", color=int(self.bot.config['embeds']['embed_colors']['primary'], 16))
        embed.set_footer(text=self.bot.config['embeds']['embed_footer'])
        embed.set_image(url=self.bot.config['embeds']['embed_banner'])
        return embed

    async def add_reactions(self, message: discord.Message) -> None:
        reactions = ['🔒', '🛡️', '🛠️', '🎉', '🗃️', '❌']
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
            '🎉': "Community",
            '🗃️': "Database",
            '❌': "Close"
        }

        category = category_mapping.get(str(reaction.emoji))
        if category:
            if category == "Close":
                await message.delete()
            else:
                new_embed = self.create_category_help_embed(category, user.id)
                if new_embed.fields:
                    await message.edit(embed=new_embed)
                else:
                    interaction = await self.bot.wait_for('interaction', check=lambda i: i.user == user and i.message == message)
                    await interaction.response.send_message("`No commands found for this category.`")
                await message.clear_reactions()
                await self.add_reactions(message)

    def create_command_help_embed(self, command: commands.Command) -> discord.Embed:
        embed = discord.Embed(title=f"Command: ..{command.name}", color=int(self.bot.config['embeds']['embed_colors']['primary'], 16))
        embed.set_footer(text=self.bot.config['embeds']['embed_footer'])

        command_data = self.command_help_data.get(command.name)
        if command_data:
            embed.description = command_data.get("description", command.help)
            embed.add_field(name="Usage", value=f"`{command_data.get('usage', '')}`", inline=False)
            embed.add_field(name="Example", value=f"`{command_data.get('example', '')}`", inline=False)
        else:
            embed.description = command.help

        return embed

    def create_category_help_embed(self, category: Optional[str] = None, user_id: int = None) -> discord.Embed:
        embed = discord.Embed(title=f"PortLords Bot - {category} Commands", description=" ", color=int(self.bot.config['embeds']['embed_colors']['primary'], 16))
        embed.set_footer(text=self.bot.config['embeds']['embed_footer'])
        embed.set_image(url=self.bot.config['embeds']['embed_banner'])

        if category == "Security":
            embed.add_field(name="**Security Commands**", value="""
            **`shodanhost <ip>`** - `Host info from Shodan.`
            **`shodansearch <query>`** - `Search Shodan.`
            **`shodanscan <ip>`** - `Shodan scan (1 Credit)`
            **`shodanscanstatus <scan_id>`** - `Shodan scan status.`
            **`shodanscanresults <scan_id>`** - `Shodan scan results.`
            **`shodanhelp`** - `Shodan command help.`
            **`recon <target> [options]`** - `Nmap scan.`
            **`reconhelp`** - `Recon command help.`
            **`cancelscan`** - `Cancel recon scan.`
            **`aiscan <ip_address>`** - `Vuln assessment (DMs only).`
            **`categories`** - `List exploit categories.`
            **`exploits <keyword>`** - `Search for exploits.`
            **`download <exploit_id>`** - `Download an exploit.`
            """, inline=False)
        elif category == "Moderation":
            embed.add_field(name="**Moderation Commands**", value="""
            **`kick <user> [reason]`** - `Kick a user.`
            **`ban <user> [reason]`** - `Ban a user.`
            **`unban <user#1234>`** - `Unban a user.`
            **`mute <user> [reason]`** - `Mute a user.`
            **`unmute <user> [reason]`** - `Unmute a user.`
            **`clear <amount>`** - `Clear messages.`
            **`warn <user> [reason]`** - `Warn a user.`
            """, inline=False)
        elif category == "Tools":
            embed.add_field(name="**Tools Commands**", value="""
            **`search <query_type> <query>`** - `Search leaked databases.`
            **`removeaccount <platform>`** - `Account removal help.`
            **`deindex`** - `De index your info from google.`
            **`footprint <username>`** - `Digital footprint search.`
            **`passwordstrength <password>`** - `Check password strength.`
            **`obfuscate`** - `Obfuscate code (in #obfuscation).`
            """, inline=False)
        elif category == "Community":
            embed.add_field(name="**Community Commands**", value="""
            **`help [category]`** - `Show bot commands.`
            **`ping`** - `Check bot latency.`
            **`8ball <question>`** - `Magic 8 ball.`
            **`dice`** - `Roll a dice.`
            **`coinflip`** - `Flip a coin.`
            **`joke`** - `Tell a programming joke.`
            **`reminder <secs> <message>`** - `Set a reminder.`
            **`chat <message>`** - `Talk to the AI.`
            **`userinfo [user]`** - `User information.`
            **`serverinfo`** - `Server information.`
            **`quiz`** - `Starts a new quiz.`
            """, inline=False)
        elif category == "Database":
            embed.add_field(name="**Database Commands**", value="""
            **`adduser <user_id> <username>`** - `Add a user to the database.`
            **`getuser <user_id>`** - `Retrieve user information.`
            **`updateuserpoints <user_id> <points>`** - `Update user points.`
            **`updateusertier <user_id> <tier>`** - `Update user tier.`
            **`updateuserverified <user_id> <true/false>`** - `Update user verified status.`
            **`updateusermuteduntil <user_id> <YYYY-MM-DD HH:MM:SS>`** - `Update user muted timestamp.`
            **`updateuserbanreason <user_id> <reason>`** - `Update user ban reason.`
            **`updateuserwarncount <user_id> <warn_count>`** - `Update user warn count.`
            """, inline=False)
        if user_id == self.admin_id:
            embed.add_field(name="**Admin Commands**", value="""
            **`reload <cog>`** - `Reload bot cogs.`
            **`verification`** - `Verification process.`
            **`embed`** - `Obfuscation embed.`
            **`tiers`** - `Show tier structure.`
            """, inline=False)

        return embed

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))
