import asyncio
import logging
import os
import subprocess
from typing import List, Optional, Tuple

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

class Brute(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.hydra_path = "/usr/bin/hydra"
        self.wordlists_dir: str = os.path.join(
            self.bot.config['paths']['root_directory'],
            self.bot.config['paths']['password_list_path']
        )
        self.delete_commands: bool = self.bot.config['settings']['delete_commands']
        self.delete_command_delay: int = self.bot.config['settings']['delete_command_delay']
        self.delete_responses: bool = self.bot.config['settings']['delete_responses']
        self.delete_response_delay: int = self.bot.config['settings']['delete_response_delay']
        self.active_scans: List[asyncio.subprocess.Process] = []

    @commands.command(name="brute", help="Attempts to brute-force a service on an IP address using Hydra.")
    async def brute_force(self, ctx: commands.Context, ip_address: str, port: int, service: str) -> None:
        """
        Args:
            ip_address: The IP address of the target.
            port: The port to target on the IP address.
            service: The service to target (e.g., ssh, ftp, http).
        """

        wordlists: List[str] = [
            f for f in os.listdir(self.wordlists_dir)
            if os.path.isfile(os.path.join(self.wordlists_dir, f))
        ]

        if not wordlists:
            error_message = await ctx.send("`No wordlists found!`")
            if self.delete_responses:
                await asyncio.sleep(self.delete_response_delay)
                await error_message.delete()
            return

        embed = discord.Embed(
            title="Select a Wordlist", description="\n".join(f"{i+1}. {w}" for i, w in enumerate(wordlists)))
        embed.color = int(self.bot.config['embeds']['embed_colors']['primary'], 16)
        embed.set_footer(text=self.bot.config['embeds']['embed_footer'])
        wordlist_message = await ctx.send(embed=embed)

        # Add reactions for each wordlist
        for i in range(len(wordlists)):
            await wordlist_message.add_reaction(f"{i+1}\u20e3")

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                user == ctx.author and
                str(reaction.emoji) in [f"{i+1}\u20e3" for i in range(len(wordlists))]
            )

        try:
            reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=30.0)
            wordlist_index: int = int(reaction.emoji[0]) - 1
            chosen_wordlist: str = wordlists[wordlist_index]
        except asyncio.TimeoutError:
            error_message = await ctx.send("`Wordlist selection timed out.`")
            if self.delete_responses:
                await asyncio.sleep(self.delete_response_delay)
                await error_message.delete()
            return

        await ctx.send(
            f"`Starting brute force attack on {ip_address}:{port} "
            f"({service}) using wordlist: {chosen_wordlist}...`"
        )

        async with ctx.typing():
            success, credentials = await self.run_hydra(ctx, ip_address, port, service, chosen_wordlist)

        if success:
            result_message = await ctx.send(
                f"Hydra success {ip_address}:{port}! "
                f"Credentials found: `{credentials}`"
            )
        else:
            result_message = await ctx.send(f"Hydra failed {ip_address}:{port}.")

        if self.delete_responses:
            await asyncio.sleep(self.delete_response_delay)
            await result_message.delete()

        if self.delete_commands:
            await ctx.message.delete()
            await asyncio.sleep(self.delete_command_delay)
            await wordlist_message.delete()

    @commands.command(name="brutehelp", help="Displays help for the 'brute' command.")
    async def brute_help(self, ctx: commands.Context) -> None:
        embed = discord.Embed(
            title="Brute Force Command Help",
            description="`brute-force attack using Hydra.`",
            color=discord.Color(0x6900ff)
        )
        embed.add_field(
            name="Usage",
            value="`!brute <ip_address> <port> <service>`",
            inline=False
        )
        embed.add_field(
            name="Arguments",
            value="""
            `<ip_address>`: `The IP address of the target server.`
            `<port>`: `The port number of the service on the target server.`
            `<service>`: `The service to target (e.g., ssh, ftp, http).`
            """,
            inline=False
        )
        embed.add_field(
            name="Example",
            value="`!brute 192.168.1.10 22 ssh`",
            inline=False
        )
        embed.set_footer(text="Use responsibly and ensure you have proper authorization before performing any security testing.")

        help_message = await ctx.send(embed=embed)

        if self.delete_responses:
            await asyncio.sleep(self.delete_response_delay)
            await help_message.delete()

        if self.delete_commands:
            await ctx.message.delete()

    @commands.command(name="cancelscan", help="Cancels the ongoing brute force scan.")
    async def cancel_scan(self, ctx: commands.Context) -> None:
        if not self.active_scans:
            await ctx.send("`No active scans to cancel.`")
            return

        for process in self.active_scans:
            process.terminate()

        self.active_scans.clear()
        await ctx.send("`All active scans have been cancelled.`")

    async def run_hydra(self, ctx: commands.Context, ip_address: str, port: int, service: str, wordlist: str) -> Tuple[bool, Optional[str]]:
        try:
            wordlist_path = os.path.join(self.wordlists_dir, wordlist)
            command = [self.hydra_path, '-C', wordlist_path, f'{ip_address}:{port}', service]

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.active_scans.append(process)

            stdout, stderr = await process.communicate()
            self.active_scans.remove(process)

            if process.returncode == 0:
                output = stdout.decode("utf-8").strip()
                credentials = self.extract_credentials(output)
                return True, credentials
            else:
                error_output = stderr.decode("utf-8").strip()
                logger.error(f"Hydra failed: {error_output}")
                return False, None

        except FileNotFoundError:
            error_message = await ctx.send(f"`Hydra executable not found at: {self.hydra_path}`")
            if self.delete_responses:
                await asyncio.sleep(self.delete_response_delay)
                await error_message.delete()
            return False, None

        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            error_message = await ctx.send(f"`An error occurred during the brute force attempt: {e}`")
            if self.delete_responses:
                await asyncio.sleep(self.delete_response_delay)
                await error_message.delete()
            return False, None

    def extract_credentials(self, hydra_output: str) -> Optional[str]:
        for line in hydra_output.splitlines():
            if "login:" in line and "password:" in line:
                parts = line.split()
                login = parts[parts.index("login:") + 1]
                password = parts[parts.index("password:") + 1]
                return f"{login}:{password}"
        return None

    async def cleanup_scans(self):
        for process in self.active_scans:
            process.terminate()
        self.active_scans.clear()

async def setup(bot: commands.Bot) -> None:
    cog = Brute(bot)
    await bot.add_cog(cog)
    bot.add_listener(cog.cleanup_scans, 'on_disconnect')
