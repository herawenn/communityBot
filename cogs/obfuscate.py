import asyncio
import logging
import os
import subprocess
import tempfile
from typing import List
import discord
from discord import File
from discord.ext import commands
from helpers import send_and_delete, create_embed # type:ignore

logger = logging.getLogger(__name__)

class Obfuscate(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.config = bot.config
        self.delete_commands = self.bot.config['settings']['delete_commands']
        self.delete_command_delay = self.bot.config['settings']['delete_command_delay']
        self.delete_responses = self.bot.config['settings']['delete_responses']
        self.delete_response_delay = self.bot.config['settings']['delete_response_delay']
        self.delete_errors = self.bot.config['settings']['delete_errors']
        self.delete_errors_delay = self.bot.config['settings']['delete_errors_delay']

    async def obfuscate_file(self, file_extension: str, source_file_path: str, output_dir: str,
                             file_name: str) -> None:
        try:
            if file_extension == '.py':
                subprocess.run(['pyarmor', 'gen', '--output', output_dir, source_file_path], check=True)
            elif file_extension == '.js':
                subprocess.run(['npx', 'javascript-obfuscator', source_file_path, '--output',
                                 os.path.join(output_dir, file_name)], check=True)
            elif file_extension == '.java':
                subprocess.run(
                    ['proguard', '-injars', source_file_path, '-outjars', os.path.join(output_dir, file_name),
                     '-dontshrink', '-dontoptimize'], check=True)
            elif file_extension == '.go':
                subprocess.run(['go', 'build', '-o', os.path.join(output_dir, file_name), source_file_path],
                               check=True, cwd=output_dir)
            elif file_extension == '.rs':
                with tempfile.NamedTemporaryFile(suffix='.rs', delete=False) as temp_file:
                    temp_file_path = temp_file.name
                    subprocess.run(
                        ['rustc', '--edition=2018', '--crate-type=bin', '-o', temp_file_path, source_file_path],
                        check=True)
                    os.rename(temp_file_path, os.path.join(output_dir, file_name))
        except subprocess.CalledProcessError as e:
            logger.error(f"Subprocess error during obfuscation: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during obfuscation: {str(e)}", exc_info=True)
            raise

    @commands.command(name='obfuscate', help='Obfuscates the attached code file.')
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def obfuscate_command(self, ctx: commands.Context) -> None:
        try:
            if not ctx.message.attachments:
                await send_and_delete(ctx, content="`Error: Please attach a file to obfuscate.`",
                                    delay=self.delete_errors_delay, delete_type='error')
                return

            attachment: discord.Attachment = ctx.message.attachments[0]
            file_name: str = attachment.filename
            file_extension: str = os.path.splitext(file_name)[1].lower()
            supported_extensions: List[str] = ['.py', '.java', '.js', '.go', '.rs']

            if file_extension not in supported_extensions:
                await send_and_delete(
                    ctx,
                    content=f"`Error: Unsupported file type {file_extension}. Supported types: {', '.join(supported_extensions)}`",
                    delay=self.delete_errors_delay, delete_type='error')
                return

            async with ctx.typing():
                with tempfile.TemporaryDirectory() as output_dir:
                    source_file_path: str = os.path.join(output_dir, file_name)
                    await attachment.save(source_file_path)

                    await self.obfuscate_file(file_extension, source_file_path, output_dir, file_name)
                    await send_and_delete(ctx, file=File(os.path.join(output_dir, file_name)), delay=self.delete_response_delay)

            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

        except subprocess.CalledProcessError as e:
            logger.error(f"Subprocess error: {str(e)}")
            await send_and_delete(ctx, content=f"`Error during obfuscation: {str(e)}`",
                                delay=self.delete_errors_delay, delete_type='error')
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            await send_and_delete(ctx, content="`An error occurred during obfuscation. Please try again later.`",
                                delay=self.delete_errors_delay, delete_type='error')

    @obfuscate_command.error
    async def obfuscate_command_error(self, ctx, error):
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

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Obfuscate(bot))
