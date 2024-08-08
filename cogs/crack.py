import discord
from discord.ext import commands
import hashid
import subprocess
import os
import logging

logger = logging.getLogger(__name__)

class HashCrack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.default_wordlist = 'utility/wordlist.txt'

    @commands.command(name="crack", help="Crack a hash. (Restricted)")
    @commands.is_owner()
    async def crack(self, ctx, hash_value: str, wordlist: str = None):
        if wordlist is None:
            wordlist = self.default_wordlist

        if not os.path.isfile(wordlist):
            await ctx.send(f"Wordlist not found: {wordlist}")
            logger.error(f"Wordlist not found: {wordlist}")
            return

        try:
            hash_info = hashid.hash_id(hash_value)
            hash_type = hash_info['hash_type']

            crack_cmd = {
                'md5': f"john --format=raw-md5 --wordlist={wordlist} hash.txt",
                'sha1': f"john --format=raw-sha1 --wordlist={wordlist} hash.txt",
                'sha256': f"john --format=raw-sha256 --wordlist={wordlist} hash.txt"
            }.get(hash_type)

            if not crack_cmd:
                await ctx.send(f"Unsupported hash type: {hash_type}")
                logger.error(f"Unsupported hash type: {hash_type}")
                return

            with open('hash.txt', 'w') as file:
                file.write(hash_value)

            try:
                process = subprocess.run(
                    crack_cmd.split(),
                    capture_output=True,
                    text=True
                )

                if process.returncode == 0:
                    cracked_password = process.stdout.strip()
                    await ctx.send(f"Cracked password: {cracked_password}")
                    logger.info(f"Hash cracked successfully by {ctx.author} in {ctx.guild}")
                else:
                    await ctx.send(f"Failed to crack hash: {process.stderr}")
                    logger.error(f"Failed to crack hash: {process.stderr}", exc_info=True)

            except FileNotFoundError:
                await ctx.send(f"Wordlist not found: {wordlist}")
                logger.error(f"Wordlist not found: {wordlist}")

        except Exception as e:
            logger.error(f"An error occurred in the hash cracking command: {e}", exc_info=True)
            await ctx.send("An error occurred while executing the hash cracking command. Please try again later.")

async def setup(bot):
    await bot.add_cog(HashCrack(bot))
