import discord
from discord.ext import commands
import logging
from typing import Dict, Optional
import json
from helpers import send_and_delete, create_embed # type:ignore
import asyncio

logger = logging.getLogger(__name__)

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.config = bot.config
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
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def help_command(self, ctx: commands.Context, command_name: str = None) -> None:
        try:
            if command_name:
                command = self.bot.get_command(command_name)
                if command:
                    embed = self.create_command_help_embed(command)
                else:
                    embed = create_embed(title="Command Not Found",
                                          description=f"The command `{command_name}` was not found.",
                                          color_key='error',
                                          config=self.bot.config
                                          )
            else:
                embed = self.create_main_help_embed(ctx.author.id)
                help_message = await ctx.send(embed=embed)

                await self.add_reactions(help_message)

                if self.delete_commands:
                    await asyncio.sleep(5)
                    await ctx.message.delete(delay=self.delete_command_delay)

        except (discord.HTTPException, discord.Forbidden) as e:
            logger.error(f"An error occurred while managing the help message: {e}")
            await send_and_delete(ctx, content="An error occurred with the help menu. Try again later.",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')
        except Exception as e:
            logger.error(f"An unexpected error occurred in the help command: {e}", exc_info=True)
            await send_and_delete(ctx, content="An error occurred. Please try again later.",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

    @help_command.error
    async def help_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(ctx,
                                content=f"`This command is on cooldown. Please try again in {retry_after:.2f} seconds.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again later.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

    def create_main_help_embed(self, user_id: int) -> discord.Embed:
        embed = create_embed(title="PortLords AI - Help",
                              description="```   Your AI Powered Cyber Security Companion\n\n[!] Search credentials with Dehashed\n[!] Identify vulnerabilities with Shodan\n[!] Download exploits with ExploitDB\n[!] Leverage Hashcat, Nmap, John, and more!```",
                              color_key='primary',
                              config=self.bot.config
                              )
        return embed

    async def add_reactions(self, message: discord.Message) -> None:
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '❌']
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
            '1️⃣': "Security",
            '2️⃣': "Tools",
            '3️⃣': "Community",
            '4️⃣': "Moderation",
            '5️⃣': "Owner",
            '❌': "Close"
        }

        try:
            category = category_mapping.get(str(reaction.emoji))
            if category:
                if category == "Close":
                    await message.delete()
                else:
                    new_embed = self.create_category_help_embed(category, user.id)
                    if new_embed.fields:
                        await message.edit(embed=new_embed)
                    else:
                        embed = create_embed(title='Command Help',
                                              description="`No commands found for this category.`",
                                              color_key='error',
                                              config=self.bot.config
                                              )
                        await send_and_delete(message.channel, embed=embed, delay=self.delete_errors_delay,
                                              delete_type='error')
                    await message.clear_reactions()
                    await self.add_reactions(message)
        except Exception as e:
            logger.error(f"An error occurred while managing the help message: {e}", exc_info=True)
            await send_and_delete(message.channel, content="An error occurred with the help menu. Try again later.",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

    def create_command_help_embed(self, command: commands.Command) -> discord.Embed:
        embed = discord.Embed(title=f"Command: ..{command.name}",
                              color=int(self.bot.config['embeds']['embed_colors']['primary'], 16))
        embed.set_footer(text=self.bot.config['embeds']['embed_footer'])
        embed.set_image(url=self.bot.config['embeds']['embed_banner'])

        command_data = self.command_help_data.get(command.name)
        if command_data:
            embed.description = command_data.get("description", command.help)
            embed.add_field(name="Usage", value=f"`{command_data.get('usage', '')}`", inline=False)
            embed.add_field(name="Example", value=f"`{command_data.get('example', '')}`", inline=False)
        else:
            embed.description = command.help

        return embed

    def create_category_help_embed(self, category: Optional[str] = None, user_id: int = None) -> discord.Embed:

        embed = create_embed(title=f"PortLords Bot - {category} Commands",
                              description=" ",
                              color_key='primary',
                              config=self.bot.config
                              )

        if category == "Security":
            embed.add_field(name=" ", value="""
            **`host`** *`<ip address>`* - `Host info from Shodan.`
            **`recon`** *`<IP address>`* - `Perform an nmap scan.`
            **`cancelscan`** - `Cancel an ongoing nmap scan.`
            **`categories`** - `List ExploitDB categories.`
            **`exploits`** *`<keyword>`* - `Search ExploitDB for exploits.`
            **`download`** *`<exploit ID>`* - `Download an exploit by ID.`
            **`~~censys <query> - Search Censys using natural language.~~`
            **`search`** *`<query type> <query>`* - `Search leaked databases.`
            **`vulnerability`** *`<message>`* - `Vulnerability analysis by PortLordsAI.`
            **`malware`** *`<message>`* - `Malware analysis by PortLordsAI.`
            """, inline=False)
        elif category == "Tools":
            embed.add_field(name=" ", value="""
            **`chat`** *`<message>`* - `Converse with PortLordsAI.`
            **`code`** *`<message>`* - `Code help from PortLordsAI.`
            **`sudo`** *`<command>`* - `Use an AI powered linux terminal.`
            **`crack`** *`<hash> <hash_type>`* - `Crack a hash using Hashcat.`
            **`fullz`** - `Sends random person data.`
            **`stealer`** - `Sends random stealer data.`
            **`privacy`** *`[service]`* - `Get data removal links for popular data brokers or specific services.`
            **`username`** *`<username>`* - `Search for your digital footprint.`
            **`password`** *`<password>`* - `Check the strength of a password.`
            **`hibp`** *`<email>`* - `Check if an email has been involved in a data breach using 'Have I Been Pwned?'.`
            **`obfuscate`** - `Obfuscate code (in the #obfuscation channel).`
            **`proxy`** - `Retrieve proxies.`
            """, inline=False)
        elif category == "Community":
            embed.add_field(name=" ", value="""
            **`help`** *`<category>`* - `Show this message.`
            **`ping`** - `Check the bot's latency.`
            **`8ball`** *`<question>`* - `Ask the magic 8-ball a question.`
            **`dice`** - `Roll a 6-sided dice.`
            **`coinflip`** - `Flip a coin.`
            **`joke`** - `Tell a programming joke.`
            **`reminder`** *`<seconds> <message>`* - `Set a reminder.`
            **`userinfo`** *`<user mention>`* - `Get information about a user.`
            **`serverinfo`** - `Get information about the current server.`
            **`quiz`** - `Start a new quiz.`
            **`leaderboard`** - `Show the quiz leaderboard`
            """, inline=False)
        elif category == "Moderation":
            embed.add_field(name=" ", value="""
            **`kick`** *`<user mention> <reason>`* - `Kick a user.`
            **`ban`** *`<user mention> <reason>`* - `Ban a user.`
            **`unban`** *`<user#1234>`* - `Unban a user.`
            **`mute`** *`<user mention> <reason>`* - `Mute a user.`
            **`unmute`** *`<user mention> <reason>`* - `Unmute a user.`
            **`clear`** *`<number of messages>`* - `Clear messages.`
            **`warn`** *`<user mention> <reason>`* - `Warn a user.`
            """, inline=False)
        elif category == "Owner":
            embed.add_field(name=" ", value="""
            **`crawl`** *`<range_name>`* - `Start the PortLords crawler.`
            **`reload`** *`<cog>`* - `Reload bot cogs.`
            **`verification`** - `Manage the verification process.`
            **`tiers`** - `Show the tier structure.`
            **`impersonate`** *`<user mention> <message>`* - `Impersonate a user and send a message.`
            **`postdevice`** - `Post a random device from the crawler's data.`
            **`adduser`** *`<user ID> <username>`* - `Add a user to the database.`
            **`getuser`** *`<user ID>`* - `Retrieve information about a user from the database.`
            **`userpoints`** *`<user ID> <points>`* - `Update points for a user.`
            **`usertier`** *`<user ID> <tier>`* - `Update the tier for a user.`
            """, inline=False)

        return embed

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Help(bot))
