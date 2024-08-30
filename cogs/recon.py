import asyncio
import logging
import asyncio
import logging
import re
import subprocess
from typing import List
import discord
from discord.ext import commands
from helpers import send_and_delete

logger = logging.getLogger(__name__)

class Recon(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.nmap_path = "/usr/bin/nmap"
        self.delete_commands: bool = self.bot.config['settings']['delete_commands']
        self.delete_command_delay: int = self.bot.config['settings']['delete_command_delay']
        self.delete_responses: bool = self.bot.config['settings']['delete_responses']
        self.delete_response_delay: int = self.bot.config['settings']['delete_response_delay']
        self.delete_errors: bool = self.bot.config['settings']['delete_errors']
        self.delete_errors_delay: int = self.bot.config['settings']['delete_errors_delay']
        self.active_scans: List[asyncio.subprocess.Process] = []

    async def safe_delete_message(self, message, delay):
        try:
            await asyncio.sleep(delay)
            await message.delete()
        except discord.NotFound:
            logger.warning(f"Message not found: {message.id}")
        except Exception as e:
            logger.error(f"An error occurred while deleting message {message.id}: {e}", exc_info=True)

    def validate_ip_address(self, ip):
        regex = "^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        if re.search(regex, ip):
            return True
        else:
            return False

    @commands.command(name="recon", help="Perform network reconnaissance using Nmap. Usage: ..recon <target> [options]. Example: ..recon 192.168.1.1 -sS -T4")
    @commands.cooldown(1, 300, commands.BucketType.user)
    @commands.is_owner()
    async def recon(self, ctx: commands.Context, target: str, *options: str) -> None:
        try:
            if not self.validate_ip_address(target):
                await send_and_delete(
                    ctx,
                    "`Error: Invalid IP address or hostname format.`",
                    delay=self.bot.config['settings']['delete_errors_delay'],
                    delete_type='error'
                )
                return

            nmap_command = [self.nmap_path, target] + list(options)
            logger.info(f"Running Nmap command: {' '.join(nmap_command)}")

            async with ctx.typing():
                process = await asyncio.create_subprocess_exec(
                    *nmap_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                self.active_scans.append(process)

                stdout, stderr = await process.communicate()
                self.active_scans.remove(process)

                if process.returncode == 0:
                    output = stdout.decode("utf-8").strip()
                    await ctx.send(f"```\n{output}\n```")
                else:
                    error_output = stderr.decode("utf-8").strip()
                    logger.error(f"Nmap failed: {error_output}")
                    await ctx.send(f"`Nmap scan failed: {error_output}`")

            if self.delete_commands:
                await self.safe_delete_message(ctx.message, self.delete_command_delay)

        except Exception as e:
            logger.error(f"An unexpected error occurred in recon: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred during the Nmap scan. Please try again later.`",  delay=self.bot.config['settings']['delete_errors_delay'],  delete_type='error')

    @commands.command(name="reconhelp", help="Displays help for the 'recon' command.")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def recon_help(self, ctx: commands.Context) -> None:
        try:
            embed = discord.Embed(title="Recon Command Help", description="This command performs network reconnaissance using Nmap.", color=int(self.bot.config['embeds']['embed_colors']['primary'], 16))
            embed.add_field(name="Usage", value="`..recon <target> [options]`", inline=False)
            embed.add_field(name="Arguments", value=""" `<target>`: The IP address or hostname of the target server. `<options>`: Optional Nmap scan options (e.g., -sS -T4). """, inline=False)
            embed.add_field(name="Example", value="`..recon 192.168.1.10 -sS -T4`", inline=False)
            embed.add_field(name="Common Nmap Options", value=""" -sS (SYN Scan): Stealth scan (no connection) -sT (TCP Connect Scan): Full connection scan -sU (UDP Scan):  Scan UDP ports -T4 (Timing Template):  Faster scan speed -p <port-ranges>:  Specify port ranges to scan -A (Aggressive Scan):  Comprehensive scan (including OS detection) """, inline=False)
            embed.set_image(url=self.bot.config['embeds']['embed_banner'])
            embed.set_footer(text=self.bot.config['embeds']['embed_footer'])

            help_message = await ctx.send(embed=embed)

            if self.delete_responses:
                await self.safe_delete_message(help_message, self.delete_response_delay)

            if self.delete_commands:
                await self.safe_delete_message(ctx.message, self.delete_command_delay)
        except Exception as e:
            logger.error(f"An unexpected error occurred in recon_help: {e}", exc_info=True)
            error_message = await ctx.send("`An error occurred while displaying the help message. Please try again later.`")
            if self.delete_errors:
                await self.safe_delete_message(error_message, self.delete_errors_delay)

    @commands.command(name="cancelscan", help="Cancels the ongoing Nmap scan.")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def cancel_scan(self, ctx: commands.Context) -> None:
        try:
            if not self.active_scans:
                await ctx.send("`No active Nmap scans to cancel.`")
                return

            for process in self.active_scans:
                process.terminate()

            self.active_scans.clear()
            await ctx.send("`All active Nmap scans have been cancelled.`")
        except Exception as e:
            logger.error(f"An unexpected error occurred in cancel_scan: {e}", exc_info=True)
            error_message = await ctx.send("`An error occurred while cancelling the scans. Please try again later.`")
            if self.delete_errors:
                await self.safe_delete_message(error_message, self.delete_errors_delay)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Recon(bot))
