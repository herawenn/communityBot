import asyncio
import logging
from typing import Optional
import discord
from discord.ext import commands
from pycrack import hash_cracker # type: ignore

logger = logging.getLogger(__name__)

class Crack(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="crack", help="Attempt to crack a given hash.")
    async def crack_hash(self, ctx: commands.Context, hash_to_crack: str, hash_type: str = "sha256") -> None:

        if hash_type.lower() not in hash_cracker.SUPPORTED_ALGORITHMS:
            await ctx.send(
                f"Unsupported hash type: {hash_type}. "
                f"Supported types: {', '.join(hash_cracker.SUPPORTED_ALGORITHMS)}")
            return

        async with ctx.typing():
            result: Optional[str] = await asyncio.to_thread(self.attempt_crack, hash_to_crack, hash_type)

        if result:
            await ctx.send(f"Cracked! The password is: `{result}`")
        else:
            await ctx.send("`Unsuccessful. Password could not be cracked.`")

    def attempt_crack(self, hash_to_crack: str, hash_type: str) -> Optional[str]:
        try:
            cracker = hash_cracker.HashCracker(hash_type=hash_type)
            result = cracker.crack(hash_to_crack)
            if result:
                return result.password 
        except Exception as e:
            logger.error(f"An error occurred during the crack attempt: {e}", exc_info=True)
        return None

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Crack(bot))
