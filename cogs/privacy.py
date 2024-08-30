import discord
from discord.ext import commands
import asyncio
import logging
import json
import subprocess
import tempfile
import os
from helpers import send_and_delete

logger = logging.getLogger(__name__)

class Privacy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.delete_commands = self.bot.config['settings']['delete_commands']
        self.delete_command_delay = self.bot.config['settings']['delete_command_delay']
        self.delete_responses = self.bot.config['settings']['delete_responses']
        self.delete_response_delay = self.bot.config['settings']['delete_response_delay']
        self.delete_errors = self.bot.config['settings']['delete_errors']
        self.delete_errors_delay = self.bot.config['settings']['delete_errors_delay']
        self.db = self.bot.get_cog("Database")

    @commands.command(name='removeaccount', help="Helps with removing your account from specific platforms. Usage: ..removeaccount <platform>")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def remove_account(self, ctx, platform: str):
        try:
            with open("files/json/links.json", 'r') as f:
                self.removal_links = json.load(f)

            if platform in self.removal_links:
                link = self.removal_links[platform]
                await ctx.send(f"`{platform.capitalize()}`\n\n{link}")

                await self.db.execute(
                    "INSERT INTO LogPrivacyCommands (user_id, command, timestamp) VALUES (?, ?, ?)",
                    (ctx.author.id, "removeaccount", discord.utils.utcnow())
                )

            else:
                await send_and_delete(ctx, f"`Platform '{platform}' not found in the database. Check the command usage.`",delay=self.delete_errors_delay, delete_type='error')

        except Exception as e:
            logger.error(f"An unexpected error occurred in remove_account: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred while processing the command. Please try again later.`", delay=self.bot.config['settings']['delete_errors_delay'],delete_type='error')

    @commands.command(name='deindex', help="Provides guidance on deindexing your information from Google. Usage: ..deindex")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def deindex(self, ctx):
        try:
            await ctx.send("`To deindex your information from Google:`\n\nhttps://www.google.com/search/remove\n\n`Enter the URL you want to remove, and click 'Request removal'`")

            await self.db.execute(
                "INSERT INTO LogPrivacyCommands (user_id, command, timestamp) VALUES (?, ?, ?)",
                (ctx.author.id, "deindex", discord.utils.utcnow())
            )

        except Exception as e:
            logger.error(f"An unexpected error occurred in deindex: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred while processing the command. Please try again later.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')

    @commands.command(name='footprint', help="Search your digital footprint. Usage: ..footprint <username>")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def footprint(self, ctx, username: str):
        try:
            await ctx.send("`Depending on exposure level, this could take a bit. Results will be sent via DM.`")

            async with ctx.typing():
                process = await asyncio.create_subprocess_exec('maigret', username, '--no-recursion', '--no-extracting', '--no-progressbar', '--no-color', '--txt', '--timeout', '15', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = await process.communicate()

                if process.returncode == 0:
                    output = stdout.decode("utf-8").strip()
                    filtered_output = self.filter_output(output)

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
                        temp_file.write(filtered_output.encode("utf-8"))
                        temp_file_path = temp_file.name

                    with open(temp_file_path, 'rb') as file:
                        await ctx.author.send(file=discord.File(file, "footprints.txt"))

                    os.remove(temp_file_path)

                    await ctx.send(f"**`DMs`**")

                    await self.db.execute(
                        "INSERT INTO LogPrivacyCommands (user_id, command, timestamp) VALUES (?, ?, ?)",
                        (ctx.author.id, "footprint", discord.utils.utcnow())
                    )

                else:
                    error_output = stderr.decode("utf-8").strip()
                    logger.error(f"Maigret failed: {error_output}")
                    await ctx.send(f"`Maigret search failed: {error_output}`")

        except Exception as e:
            logger.error(f"An unexpected error occurred in footprint: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred while searching for your digital footprint. Please try again later.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')

    @commands.command(name='password', help="Check the strength of a password. Usage: ..password <password>")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def password_strength(self, ctx, password: str):
        try:
            strength = self.custom_password_strength(password)
            await ctx.send(f"`Password Rating: {strength}/4`")

            await self.db.execute(
                "INSERT INTO LogPrivacyCommands (user_id, command, timestamp) VALUES (?, ?, ?)",
                (ctx.author.id, "password", discord.utils.utcnow())
            )

        except Exception as e:
            logger.error(f"An unexpected error occurred in password_strength: {e}", exc_info=True)
            await send_and_delete(
                ctx, "`An error occurred while checking password strength. Please try again later.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')

    def filter_output(self, output: str) -> str:
        lines = output.splitlines()
        filtered_lines = [line for line in lines if line.startswith('[+]')]
        return '\n'.join(filtered_lines)

    def custom_password_strength(self, password: str) -> int:
        length = len(password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()-_=+[]{}|;:,.<>?/~`' for c in password)

        score = 0
        if length >= 8:
            score += 1
        if has_upper:
            score += 1
        if has_digit:
            score += 1
        if has_special:
            score += 1

        if any(password.lower().count(seq) >= 3 for seq in '0123456789'):
            score -= 1
        if any(seq in password.lower() for seq in ['123', 'abc', 'password', '1234', 'qwerty']):
            score -= 1

        return max(min(score, 4), 0)

async def setup(bot):
    await bot.add_cog(Privacy(bot))
