import discord
from discord.ext import commands, tasks
import json
import logging
import aiohttp
import asyncio
import random
from datetime import datetime
from aiolimiter import AsyncLimiter
from helpers import send_and_delete, create_embed # type: ignore

logger = logging.getLogger(__name__)

class Community(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.delete_commands = self.config['settings']['delete_commands']
        self.delete_command_delay = self.config['settings']['delete_command_delay']
        self.delete_responses = self.config['settings']['delete_responses']
        self.delete_response_delay = self.config['settings']['delete_response_delay']
        self.delete_errors = self.config['settings']['delete_errors']
        self.delete_errors_delay = self.config['settings']['delete_errors_delay']
        self.active_polls = {}
        self.joke_api_limiter = AsyncLimiter(1, 15)

    async def log_action(self, ctx, action, message, description):
            logging_cog = self.bot.get_cog('Logging')
            if logging_cog:
                await logging_cog.log_message(f"{action.capitalize()} Action: {message}", description)

    # --- Commands ---

    @commands.command(name='ping', help="Check the bot's latency.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        embed = create_embed(title="Pong!",
                              description=f"`{latency}ms`",
                              color_key='primary',
                              config=self.bot.config
                              )
        await ctx.send(embed=embed)
        await self.log_action(ctx, "ping", f"Ping command used by {ctx.author.mention} in {ctx.channel.mention}", "Ping command used.")

        if self.delete_commands:
            await ctx.message.delete(delay=self.delete_command_delay)

    @ping.error
    async def ping_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(ctx, content=f"`This command is on cooldown. Please try again in {retry_after:.2f} seconds.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again later.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

    @commands.command(name='userinfo', help="Get information about a user. Usage: ..userinfo [user mention]")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def userinfo(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        fields = [
            ("ID", member.id, True),
            ("Name", member.name, True),
            ("Discriminator", member.discriminator, True),
            ("Bot", member.bot, True),
            ("Top Role", member.top_role.name, True),
            ("Status", member.status, True),
            ("Activity", member.activity.name if member.activity else "None", True),
            ("Joined At", member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), True),
            ("Created At", member.created_at.strftime("%Y-%m-%d %H:%M:%S"), True)
        ]

        embed = create_embed(title=f"User Info - {member.name}",
                              description=f"Information about {member.mention}",
                              color_key='primary',
                              fields=fields,
                              config=self.bot.config
                              )
        await ctx.send(embed=embed)

        await self.log_action(ctx, "userinfo", f"User info command used by {ctx.author.mention} for {member.mention} in {ctx.channel.mention}", "Userinfo command used.")
        if self.delete_commands:
            await ctx.message.delete(delay=self.delete_command_delay)

    @userinfo.error
    async def userinfo_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(ctx, content=f"`This command is on cooldown. Please try again in {retry_after:.2f} seconds.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again later.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

    @commands.command(name='serverinfo', help="Get information about the current server.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def serverinfo(self, ctx):
        guild = ctx.guild
        fields = [
            ("ID", guild.id, False),
            ("Name", guild.name, True),
            ("Owner", guild.owner.mention, True),
            ("Member Count", guild.member_count, True),
            ("Created At", guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), True)
        ]

        embed = create_embed(title=f"Server Info - {guild.name}",
                              description=f"Information about {guild.name}",
                              color_key='primary',
                              fields=fields,
                              config=self.bot.config
                              )
        await ctx.send(embed=embed)

        await self.log_action(ctx, "serverinfo", f"Server info command used by {ctx.author.mention} in {ctx.channel.mention}", "Serverinfo command used.")
        if self.delete_commands:
            await ctx.message.delete(delay=self.delete_command_delay)

    @serverinfo.error
    async def serverinfo_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(ctx, content=f"`This command is on cooldown. Please try again in {retry_after:.2f} seconds.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again later.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

    @commands.command(name='remind', help="Set a reminder for yourself. Usage: ..remind <time in seconds> <reminder message>")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def reminder(self, ctx, time: int, *, reminder: str):
        try:
            time = int(time)
            if time <= 0:
                raise ValueError("Time must be a positive integer.")

            embed = create_embed(title="Reminder Set",
                                  description=f"`Reminder set for {time} seconds.`",
                                  color_key='primary',
                                  config=self.bot.config
                                  )
            await ctx.send(embed=embed)

            await asyncio.sleep(time)

            embed = create_embed(title="Reminder",
                                  description=f"{ctx.author.mention}, reminder: {reminder}",
                                  color_key='primary',
                                  config=self.bot.config
                                  )
            await ctx.send(embed=embed)

            await self.log_action(ctx, "remind", f"Reminder set by {ctx.author.mention} in {ctx.channel.mention}: {reminder}", "Reminder command used.")
            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

        except ValueError:
            await send_and_delete(ctx, content="`Error: Invalid time format. Please use a positive integer (seconds).`",
                                delay=self.delete_errors_delay, delete_type='error')
        except Exception as e:
            logger.error(f"An error occurred in the reminder command: {e}", exc_info=True)
            await send_and_delete(ctx, content="`An error occurred while setting the reminder. Please try again later.`",
                                delay=self.delete_errors_delay, delete_type='error')

    @reminder.error
    async def reminder_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(ctx, content=f"`This command is on cooldown. Please try again in {retry_after:.2f} seconds.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again later.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

    @commands.command(name='8ball', help="Ask the Magic 8 Ball a question. Usage: ..8ball <your question>")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def eight_ball(self, ctx, *, question: str):
        responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.", "Yes, definitely.", "You may rely on it.",
            "As I see it, yes.", "Most likely.", "Outlook good.", "Signs point to yes.", "Yes.",
            "Reply hazy, try again.", "Ask again later.", "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "My reply is no.", "My sources say no.", "Outlook not so good.", "Very doubtful."
        ]

        embed = create_embed(title="Magic 8-Ball",
                              description=f"`Question: {question}\nAnswer: {random.choice(responses)}`",
                              color_key='primary',
                              config=self.bot.config
                              )
        await ctx.send(embed=embed)
        await self.log_action(ctx, "8ball", f"8ball command used by {ctx.author.mention} in {ctx.channel.mention}: {question}", "8ball command used.")
        if self.delete_commands:
            await ctx.message.delete(delay=self.delete_command_delay)

    @eight_ball.error
    async def eight_ball_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(ctx, content=f"`This command is on cooldown. Please try again in {retry_after:.2f} seconds.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again later.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

    @commands.command(name='dice', help="Roll a 6-sided dice.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def dice(self, ctx):
        result = random.randint(1, 6)
        embed = create_embed(title="Dice Roll",
                              description=f"`You rolled a {result}.`",
                              color_key='primary',
                              config=self.bot.config
                              )
        await ctx.send(embed=embed)
        await self.log_action(ctx, "dice", f"Dice command used by {ctx.author.mention} in {ctx.channel.mention}: Rolled a {result}", "Dice command used.")
        if self.delete_commands:
            await ctx.message.delete(delay=self.delete_command_delay)

    @dice.error
    async def dice_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(ctx, content=f"`This command is on cooldown. Please try again in {retry_after:.2f} seconds.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again later.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

    @commands.command(name='coinflip', help="Flip a coin.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def coinflip(self, ctx):
        result = random.choice(["Heads", "Tails"])
        embed = create_embed(title="Coin Flip",
                              description=f"`The coin landed on {result}.`",
                              color_key='primary',
                              config=self.bot.config
                              )
        await ctx.send(embed=embed)
        await self.log_action(ctx, "coinflip", f"Coinflip command used by {ctx.author.mention} in {ctx.channel.mention}: Landed on {result}", "Coinflip command used.")
        if self.delete_commands:
            await ctx.message.delete(delay=self.delete_command_delay)

    @coinflip.error
    async def coinflip_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(ctx, content=f"`This command is on cooldown. Please try again in {retry_after:.2f} seconds.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again later.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

    @commands.command(name='joke', help="Tell a random programming joke.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def joke(self, ctx):
        async with self.joke_api_limiter:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://v2.jokeapi.dev/joke/Programming') as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'joke' in data:
                            joke_text = data['joke']
                        else:
                            joke_text = f"{data['setup']}\n\n{data['delivery']}"

                        embed = create_embed(title="Programming Joke",
                                              description=f"`{joke_text}`",
                                              color_key='primary',
                                              config=self.bot.config
                                              )
                        await ctx.send(embed=embed)

                    else:
                        logger.error(f"Joke API request failed with status code {response.status}")
                        await send_and_delete(ctx, content="`Error: Could not retrieve a joke. Please try again later.`", delay=self.delete_errors_delay, delete_type='error')

        await self.log_action(ctx, "joke", f"Joke command used by {ctx.author.mention} in {ctx.channel.mention}", "Joke command used.")
        if self.delete_commands:
            await ctx.message.delete(delay=self.delete_command_delay)

    @joke.error
    async def joke_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(ctx, content=f"`This command is on cooldown. Please try again in {retry_after:.2f} seconds.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again later.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Community(bot))
