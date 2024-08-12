import discord
from discord.ext import commands
import hashid
import asyncio
import os
import logging
import shlex

logger = logging.getLogger(__name__)

class HashCrack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.wordlists_dir = 'wordlists'
        self.default_wordlist = 'milworm.txt'

    async def crack_hash(self, hash_value: str, wordlist_name: str):
        wordlist_path = os.path.join(self.wordlists_dir, wordlist_name)
        if not os.path.isfile(wordlist_path):
            return f"Wordlist not found: {wordlist_name}"

        try:
            hash_info = hashid.hash_id(hash_value)
            hash_type = hash_info['hash_type']

            crack_cmd = {
             'md5': f"john --format=raw-md5 --wordlist={wordlist_path} hash.txt",
             'sha1': f"john --format=raw-sha1 --wordlist={wordlist_path} hash.txt",
             'sha256': f"john --format=raw-sha256 --wordlist={wordlist_path} hash.txt"
            }.get(hash_type)

            if not crack_cmd:
                return f"Unsupported hash type: {hash_type}"

            with open('hash.txt', 'w') as file:
                file.write(hash_value)

            args = shlex.split(crack_cmd)
            try:
                process = await asyncio.create_subprocess_exec(*args, capture_output=True, text=True)
                stdout, stderr = await process.communicate()

                if process.returncode == 0:
                    cracked_password = stdout.strip()
                    return f"Cracked password: {cracked_password}"
                else:
                    return f"Failed to crack hash: {stderr}"
            except FileNotFoundError:
                return f"Wordlist not found: {wordlist_name}"
            except Exception as e:
                logger.error(f"An error occurred in the hash cracking command: {e}", exc_info=True)
                return "An error occurred while executing the hash cracking command. Please try again later."

        except Exception as e:
            logger.error(f"An error occurred in the hash cracking command: {e}", exc_info=True)
            return "An error occurred while executing the hash cracking command. Please try again later."

    @commands.command(name="crack", help="Attempt to crack a hashed password.")
    @commands.is_owner()
    async def crack(self, ctx, hash_value: str, wordlist_name: str = None):
        if wordlist_name is None:
            wordlist_name = self.default_wordlist

        result = await self.crack_hash(hash_value, wordlist_name)
        await ctx.send(f"```{result}```")
        logger.info(f"Hash cracking command executed by {ctx.author} in {ctx.guild}")

async def setup(bot):
    await bot.add_cog(HashCrack(bot))
