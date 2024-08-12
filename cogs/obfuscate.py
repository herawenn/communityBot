import asyncio
import logging
import os
import subprocess
import tempfile
from typing import List

import discord
from discord import File
from discord.ext import commands

logger = logging.getLogger(__name__)

class Obfuscate(commands.Cog):
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.obf_channel_id: int = int(self.bot.config['identifiers']['obf_channel_id'])

    @commands.command(name='embed', help='Sends the obfuscation embed.')
    async def embed_command(self, ctx: commands.Context) -> None:
        if ctx.channel.id != self.obf_channel_id:
            return

        embed = discord.Embed(
            title="**Attachment Required**",
            description=f"*`Please attach a file to obfuscate.`*",
            color=int(self.bot.config['embeds']['embed_colors']['primary'], 16))
        embed.set_image(url=self.bot.config['embeds']['embed_banner'])
        embed.set_footer(text=self.bot.config['embeds']['embed_footer'])

        await ctx.send(embed=embed)
        await ctx.message.delete()

    @commands.command(name='obfuscate', help='Obfuscates the attached file.')
    async def obfuscate_command(self, ctx: commands.Context) -> None:
        
        if ctx.channel.id != self.obf_channel_id:
            await ctx.send("This command can only be used in the designated obfuscation channel.")
            return

        if not ctx.message.attachments:
            await ctx.send("Please attach a file to obfuscate.")
            return

        attachment: discord.Attachment = ctx.message.attachments[0]

        file_name: str = attachment.filename

        file_extension: str = os.path.splitext(file_name)[1].lower()

        supported_extensions: List[str] = ['.py', '.java', '.js', '.go', '.rs']
        if file_extension not in supported_extensions:
            await ctx.send(f"Error: Unsupported file type {file_extension}. Supported types: {', '.join(supported_extensions)}")
            return

        try:
            async with ctx.typing():
                with tempfile.TemporaryDirectory() as output_dir:
                    source_file_path: str = os.path.join(output_dir, file_name)
                    await attachment.save(source_file_path)

                    await self.obfuscate_file(file_extension, source_file_path, output_dir, file_name)

                    file_message = await ctx.send(file=File(os.path.join(output_dir, file_name)))

                    await asyncio.sleep(10)
                    await file_message.delete()

        except subprocess.CalledProcessError as e:
            logger.error(f"Subprocess error: {str(e)}")
            await ctx.send(f"Error during obfuscation: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            await ctx.send("An error occurred during obfuscation. Please try again later.")

    async def obfuscate_file(self, file_extension: str, source_file_path: str, output_dir: str, file_name: str) -> None:
        if file_extension == '.py':
            subprocess.run(['pyarmor', 'gen', '--output', output_dir, source_file_path], check=True)
        elif file_extension == '.js':
            subprocess.run(['npx', 'javascript-obfuscator', source_file_path, '--output', os.path.join(output_dir, file_name)], check=True)
        elif file_extension == '.java':
            subprocess.run(['proguard', '-injars', source_file_path, '-outjars', os.path.join(output_dir, file_name), '-dontshrink', '-dontoptimize'],check=True)
        elif file_extension == '.go':
            subprocess.run(['go', 'build', '-o', os.path.join(output_dir, file_name), source_file_path], check=True, cwd=output_dir)
        elif file_extension == '.rs':
            with tempfile.NamedTemporaryFile(suffix='.rs', delete=False) as temp_file:
                temp_file_path = temp_file.name
                subprocess.run(['rustc', '--edition=2018', '--crate-type=bin', '-o', temp_file_path, source_file_path], check=True)
                os.rename(temp_file_path, os.path.join(output_dir, file_name))

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Obfuscate(bot))
