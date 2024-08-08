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
        self.default_wordlist = 'wordlist.txt'

    async def crack_hash(self, hash_value: str, wordlist: str):
        if not os.path.isfile(wordlist):
            return f"Wordlist not found: {wordlist}"

        try:
            hash_info = hashid.hash_id(hash_value)
            hash_type = hash_info['hash_type']

            crack_cmd = {
              'md5': f"john --format=raw-md5 --wordlist={wordlist} hash.txt",
              'sha1': f"john --format=raw-sha1 --wordlist={wordlist} hash.txt",
              'sha256': f"john --format=raw-sha256 --wordlist={wordlist} hash.txt"
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
                return f"Wordlist not found: {wordlist}"
            except Exception as e:
                logger.error(f"An error occurred in the hash cracking command: {e}", exc_info=True)
                return "An error occurred while executing the hash cracking command. Please try again later."

        except Exception as e:
            logger.error(f"An error occurred in the hash cracking command: {e}", exc_info=True)
            return "An error occurred while executing the hash cracking command. Please try again later."

    @commands.command(name="crack", help="Crack a hash. (Restricted)")
    @commands.is_owner()
    async def crack(self, ctx, hash_value: str, wordlist: str = None):
        if wordlist is None:
            wordlist = self.default_wordlist

        result = await self.crack_hash(hash_value, wordlist)
        await ctx.send(result)
        logger.info(f"Hash cracking command executed by {ctx.author} in {ctx.guild}")

async def setup(bot):
    await bot.add_cog(HashCrack(bot))
