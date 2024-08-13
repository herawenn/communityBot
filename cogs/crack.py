import asyncio
import logging
import os
import subprocess
from typing import Optional
import discord
import tempfile
from discord.ext import commands

logger = logging.getLogger(__name__)

class Crack(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.jtr_path = "john"
        self.wordlist_path: str = os.path.join(self.bot.config['paths']['root_directory'], self.bot.config['paths']['password_list_path'], "wordlist.txt")
        self.delete_commands: bool = self.bot.config['settings']['delete_commands']
        self.delete_command_delay: int = self.bot.config['settings']['delete_command_delay']
        self.delete_responses: bool = self.bot.config['settings']['delete_responses']
        self.delete_response_delay: int = self.bot.config['settings']['delete_response_delay']

    @commands.command(name="crack", help="Attempt to crack a given hash.")
    async def crack_hash(self, ctx: commands.Context, hash_to_crack: str, hash_type: str = "raw-sha256") -> None:
        async with ctx.typing():
            await self.run_john(ctx, hash_to_crack, hash_type)

    async def run_john(self, ctx: commands.Context, hash_to_crack: str, hash_type: str) -> None:
        try:
            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_hash_file:
                temp_hash_file.write(f"{hash_type}:{hash_to_crack}\n")
                temp_hash_file_path = temp_hash_file.name

            command = [self.jtr_path, "--format=" + hash_type, "--wordlist=" + self.wordlist_path, temp_hash_file_path]

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                output = stdout.decode("utf-8").strip()
                cracked_password = self.extract_password(output)
                if cracked_password:
                    response_message = await ctx.send(f"`Cracked! The password is: {cracked_password}`")
                else:
                    response_message = await ctx.send("`Cracking complete, but no password found.`")
            else:
                error_output = stderr.decode("utf-8").strip()
                response_message = await ctx.send(f"`John the Ripper cracking failed: {error_output}`")

            os.remove(temp_hash_file_path)

            if self.delete_responses:
                await asyncio.sleep(self.delete_response_delay)
                await response_message.delete()

        except FileNotFoundError:
            error_message = await ctx.send(f"`John the Ripper executable not found at: {self.jtr_path}`")
            if self.delete_responses:
                await asyncio.sleep(self.delete_response_delay)
                await error_message.delete()
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            error_message = await ctx.send(f"`An error occurred during the crack attempt: {e}`")
            if self.delete_responses:
                await asyncio.sleep(self.delete_response_delay)
                await error_message.delete()

        if self.delete_commands:
            await ctx.message.delete()

    def extract_password(self, jtr_output: str) -> Optional[str]:
        for line in jtr_output.splitlines():
            if line.startswith("password:"):
                return line.split("password:")[1].strip()
        return None

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Crack(bot))
