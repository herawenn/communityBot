import discord
from discord.ext import commands, tasks
import json
import logging
import aiohttp
import asyncio
import random
from datetime import datetime
from aiolimiter import AsyncLimiter
from helpers import send_and_delete

logger = logging.getLogger(__name__)

class Community(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.embed_color_primary = int(self.config['embeds']['embed_colors']['primary'], 16)
        self.embed_color_success = int(self.config['embeds']['embed_colors']['success'], 16)
        self.embed_color_error = int(self.config['embeds']['embed_colors']['error'], 16)
        self.delete_commands = self.config['settings']['delete_commands']
        self.delete_command_delay = self.config['settings']['delete_command_delay']
        self.delete_responses = self.config['settings']['delete_responses']
        self.delete_response_delay = self.config['settings']['delete_response_delay']
        self.delete_errors = self.config['settings']['delete_errors']
        self.delete_errors_delay = self.config['settings']['delete_errors_delay']
        self.active_polls = {}
        self.joke_api_limiter = AsyncLimiter(1, 15)

    def validate_duration(self, duration):
        try:
            int(duration)
            return True
        except ValueError:
            return False

    def validate_time(self, time):
        try:
            int(time)
            return True
        except ValueError:
            return False

    def validate_datetime_format(self, datetime_str):
        try:
            datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            return True
        except ValueError:
            return False

    async def log_action(self, ctx, action, message):
        logging_cog = self.bot.get_cog('Logging')
        if logging_cog:
            await logging_cog.log_message(f"{action.capitalize()} Action: {message}")

    @commands.command(name='ping', help="Check the bot's latency.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        await send_and_delete(
            ctx,
            f'`Pong! {latency}ms`',
            delay=self.delete_response_delay
        )
        await self.log_action(ctx, "ping", f"Ping command used by {ctx.author.mention} in {ctx.channel.mention}")

    @commands.command(name='userinfo', help="Get information about a user. Usage: ..userinfo [user mention]")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def userinfo(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        embed = discord.Embed(
            title=f"User Info - {member.name}",
            description=f"Information about {member.mention}",
            color=discord.Color(self.embed_color_primary)
        )
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(name="Name", value=member.name, inline=True)
        embed.add_field(name="Discriminator", value=member.discriminator, inline=True)
        embed.add_field(name="Bot", value=member.bot, inline=True)
        embed.add_field(name="Top Role", value=member.top_role.name, inline=True)
        embed.add_field(name="Status", value=member.status, inline=True)
        embed.add_field(name="Activity", value=member.activity.name if member.activity else "None", inline=True)
        embed.add_field(name="Joined At", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="Created At", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)

        await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)
        await self.log_action(ctx, "userinfo", f"User info command used by {ctx.author.mention} for {member.mention} in {ctx.channel.mention}")

    @commands.command(name='serverinfo', help="Get information about the current server.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def serverinfo(self, ctx):
        guild = ctx.guild

        embed = discord.Embed(
            title=f"Server Info - {guild.name}",
            description=f"Information about {guild.name}",
            color=discord.Color(self.embed_color_primary)
        )
        embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="ID", value=guild.id, inline=False)
        embed.add_field(name="Name", value=guild.name, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Member Count", value=guild.member_count, inline=True)
        embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)

        await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)
        await self.log_action(ctx, "serverinfo", f"Server info command used by {ctx.author.mention} in {ctx.channel.mention}")

    @commands.command(name='remind', help="Set a reminder for yourself. Usage: ..remind <time in seconds> <reminder message>")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def reminder(self, ctx, time: int, *, reminder: str):
        if not self.validate_time(time):
            await send_and_delete(
                ctx,
                "`Error: Invalid time. Please provide a valid number of seconds.`",
                delay=self.delete_errors_delay,
                delete_type='error'
            )
            return

        await send_and_delete(ctx, f"`Reminder set for {time} seconds.`", delay=self.delete_response_delay)
        await asyncio.sleep(time)
        await send_and_delete(ctx, f"{ctx.author.mention}, reminder: {reminder}", delay=self.delete_response_delay)
        logger.info(f"Reminder set by {ctx.author.mention} in {ctx.channel.mention}: {reminder}")

    @commands.command(name='8ball', help="Ask the Magic 8 Ball a question. Usage: ..8ball <your question>")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def eight_ball(self, ctx, *, question: str):
        responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.", "Yes, definitely.", "You may rely on it.",
            "As I see it, yes.", "Most likely.", "Outlook good.", "Signs point to yes.", "Yes.",
            "Reply hazy, try again.", "Ask again later.", "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "My reply is no.", "My sources say no.", "Outlook not so good.", "Very doubtful."
        ]
        await send_and_delete(ctx, f"`Question: {question}\nAnswer: {random.choice(responses)}`", delay=self.delete_response_delay)
        await self.log_action(ctx, "8ball", f"8ball command used by {ctx.author.mention} in {ctx.channel.mention}: {question}")

    @commands.command(name='dice', help="Roll a 6-sided dice.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def dice(self, ctx):
        result = random.randint(1, 6)
        await send_and_delete(ctx, f"`You rolled a {result}.`", delay=self.delete_response_delay)
        await self.log_action(ctx, "dice", f"Dice command used by {ctx.author.mention} in {ctx.channel.mention}: Rolled a {result}")

    @commands.command(name='coinflip', help="Flip a coin.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def coinflip(self, ctx):
        result = random.choice(["Heads", "Tails"])
        await send_and_delete(ctx, f"`The coin landed on {result}.`", delay=self.delete_response_delay)
        await self.log_action(ctx, "coinflip", f"Coinflip command used by {ctx.author.mention} in {ctx.channel.mention}: Landed on {result}")

    @commands.command(name='joke', help="Tell a random programming joke.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def joke(self, ctx):
        async with self.joke_api_limiter:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://v2.jokeapi.dev/joke/Programming') as response:
                    data = await response.json()
                    if 'joke' in data:
                        joke = data['joke']
                    else:
                        joke = f"{data['setup']}\n\n{data['delivery']}"

                    await send_and_delete(ctx, f"`{joke}`", delay=self.delete_response_delay)

        await self.log_action(ctx, "joke", f"Joke command used by {ctx.author.mention} in {ctx.channel.mention}")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Community(bot))
