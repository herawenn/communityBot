import os
import json
import asyncio
import subprocess
import tempfile
import logging
import discord
from discord.ext import commands
from discord import File

with open('config.json') as f:
    config = json.load(f)

logger = logging.getLogger(__name__)

class Obfuscate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='embed', help='Sends the obfuscation embed.')
    async def embed_command(self, ctx):
        embed = discord.Embed(
            title="**Attachment Required**",
            description=f"*`Please attach a file to obfuscate.`*",
            color=discord.Color(0x6900ff)
        )
        embed.set_image(url="https://i.imgur.com/5mp2Siz.png")
        embed.set_footer(text="From PortLords w Love © 2024")
        if ctx.channel.id == config.get('obf_id'):
            await ctx.send(embed=embed)
            await ctx.message.delete()

    @commands.command(name='obfuscate', help='Obfuscates the attached file.')
    async def obfuscate_command(self, ctx):
        if ctx.channel.id != config.get('obf_id'):
            await ctx.send("`This command can only be used in #ᴏʙғ`")
            return

        if not ctx.message.attachments:
            await ctx.send("`Please attach a file to obfuscate.`")
            return

        attachment = ctx.message.attachments[0]
        file_name = attachment.filename
        file_extension = os.path.splitext(file_name)[1].lower()

        if file_extension not in ['.py', '.java', '.js', '.go', '.rs']:
            await ctx.send(f"Error: Unsupported file type {file_extension}")
            return

        try:
            output_dir = tempfile.mkdtemp()
            source_file_path = os.path.join(output_dir, file_name)
            await attachment.save(source_file_path)

            if file_extension == '.py':
                subprocess.run(['pyarmor', 'gen', '--output', output_dir, source_file_path], check=True)
            elif file_extension == '.js':
                subprocess.run(['npx', 'javascript-obfuscator', source_file_path, '--output', os.path.join(output_dir, file_name)], check=True)
            elif file_extension == '.java':
                subprocess.run(['proguard', '-injars', source_file_path, '-outjars', os.path.join(output_dir, file_name), '-dontshrink', '-dontoptimize'], check=True)
            elif file_extension == '.go':
                subprocess.run(['go', 'build', '-o', os.path.join(output_dir, file_name), source_file_path], check=True, cwd=output_dir)
                output_file_path = os.path.join(output_dir, file_name)
                output_file_name = file_name
                os.rename(output_file_path, os.path.join(output_dir, output_file_name))
            elif file_extension == '.rs':
                with tempfile.NamedTemporaryFile(suffix='.rs', delete=False) as temp_file:
                    temp_file_path = temp_file.name
                    subprocess.run(['rustc', '--edition=2018', '--crate-type=bin', '-o', temp_file_path, source_file_path], check=True)
                    os.rename(temp_file_path, os.path.join(output_dir, file_name))

            file_message = await ctx.send(file=File(os.path.join(output_dir, file_name)))
            await asyncio.sleep(10)
            await file_message.delete()

        except subprocess.CalledProcessError as e:
            logger.error(f"Subprocess error: {str(e)}")
            await ctx.send(f"Error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            await ctx.send(f"Error: An unexpected error occurred. Details: {e}")
        finally:
            if os.path.exists(output_dir):
                import shutil
                shutil.rmtree(output_dir)

async def setup(bot):
    await bot.add_cog(Obfuscate(bot))
