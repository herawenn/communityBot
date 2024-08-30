import discord
import logging
from discord.ext import commands

logger = logging.getLogger(__name__)

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.embeds = self.config['embeds']
        self.identifiers = self.config['identifiers']
        self.logging_channel_id = int(self.identifiers.get('logging_channel_id'))
        self.db = self.bot.get_cog("Database")

    async def log_message(self, message: str):
        logging_channel = self.bot.get_channel(self.logging_channel_id)
        if logging_channel:
            embed = discord.Embed(title=" ", description=message, color=int(self.embeds['embed_colors']['primary'], 16), timestamp=discord.utils.utcnow())
            embed.set_footer(text=self.embeds['embed_footer'])
            try:
                await logging_channel.send(embed=embed)

                await self.db.execute(
                    "INSERT INTO Logs (message, timestamp) VALUES (?, ?)",
                    (message, discord.utils.utcnow())
                )

            except discord.Forbidden:
                logger.error("Missing permissions to send messages in the logging channel.")
            except discord.HTTPException as e:
                logger.error(f"Failed to send log message: {e}")

    #--- Message-related events ---

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        await self.log_message(f"From {message.author.mention}: {message.content}")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return
        await self.log_message(f"Message edited by {before.author.mention} in {before.channel.mention}:\nBefore: {before.content}\nAfter: {after.content}")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        await self.log_message(f"Message deleted by {message.author.mention} in {message.channel.mention}: {message.content}")

    #--- Command-related events ---

    @commands.Cog.listener()
    async def on_command(self, ctx):
        await self.log_message(f"Command executed by {ctx.author.mention} in {ctx.channel.mention}: {ctx.message.content}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(ctx.channel, discord.DMChannel):
            channel_info = "Direct Message"
        else:
            channel_info = ctx.channel.mention

        await self.log_message(f"Command error for {ctx.author.mention} in {channel_info}: {error}")

    #--- Member-related events ---

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.log_message(f"{member.mention} `has joined the server.`")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.log_message(f"{member.mention} `has left the server.`")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            before_roles = ', '.join([role.name for role in before.roles])
            after_roles = ', '.join([role.name for role in after.roles])
            await self.log_message(f"Roles updated for {before.mention}:\nBefore: {before_roles}\nAfter: {after_roles}")

async def setup(bot):
    await bot.add_cog(Logging(bot))
