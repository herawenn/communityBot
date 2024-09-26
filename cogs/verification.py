import discord
from discord.ext import commands
import asyncio
import logging
from helpers import send_and_delete, create_embed # type:ignore

# Setup logging
logger = logging.getLogger(__name__)

class Verification(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = bot.config
        self.verification_message = None
        self.db = self.bot.get_cog('Database')
        self.delete_errors = self.bot.config['settings']['delete_errors']
        self.delete_errors_delay = self.bot.config['settings']['delete_errors_delay']

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        try:
            unverified_role_id = int(self.config['identifiers']['unverified_role_id'])
            unverified_role = discord.utils.get(member.guild.roles, id=unverified_role_id)
            if unverified_role:
                await member.add_roles(unverified_role)
                logger.info(f"Assigned unverified role to {member.name}#{member.discriminator}")

            await self.verify_member(member)
        except Exception as e:
            logger.error(f"An error occurred while adding unverified role: {e}", exc_info=True)

    async def verify_member(self, member: discord.Member) -> None:
        try:
            verification_channel_id = int(self.config['identifiers']['verification_channel_id'])
            verification_channel = self.bot.get_channel(verification_channel_id)

            if verification_channel:
                embed = create_embed(
                    title="**Agree & Continue**",
                    description="",
                    color_key='primary',
                    fields=[(" ", "🗹 `We are not responsible for the actions of any user.`", False)],
                    config=self.bot.config
                )
                self.verification_message = await verification_channel.send(content=f"{member.mention}", embed=embed)
                await self.verification_message.add_reaction('✅')
        except Exception as e:
            logger.error(f"An error occurred while verifying member {member.name}#{member.discriminator}: {e}", exc_info=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.member.bot:
            return

        if self.verification_message is None or payload.message_id != self.verification_message.id:
            return

        if payload.emoji.name == '✅':
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            unverified_role_id = int(self.config['identifiers']['unverified_role_id'])
            unverified_role = discord.utils.get(member.guild.roles, id=unverified_role_id)
            verified_role_id = int(self.config['identifiers']['verified_role_id'])
            verified_role = discord.utils.get(member.guild.roles, id=verified_role_id)

            try:
                if unverified_role:
                    await member.remove_roles(unverified_role)
                if verified_role:
                    await member.add_roles(verified_role)

                await self.db.execute(
                    "INSERT OR IGNORE INTO Users (user_id, username, joined_at, verified, last_active) VALUES (?, ?, ?, ?, ?)",
                    (member.id, member.name, discord.utils.utcnow(), True, discord.utils.utcnow())
                )

                try:
                    await member.send("`Verification successful!`")
                except discord.HTTPException:
                    logger.warning(f"Failed to send DM to {member.mention} about verification.")

                await self.verification_message.delete()
                self.verification_message = None
            except discord.HTTPException as e:
                logger.error(f"Error adding verified role to user {member.mention}: {e}")
                guild = self.bot.get_guild(payload.guild_id)
                channel = guild.get_channel(payload.channel_id)
                await send_and_delete(channel, content=f"Error adding verified role to user {member.mention}: {e}", delay=self.delete_errors_delay, delete_type='error')

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context) -> None:
        try:
            user_exists = await self.db.fetch("SELECT 1 FROM Users WHERE user_id = ?", (ctx.author.id,))
            if not user_exists:
                await self.db.execute(
                    "INSERT OR IGNORE INTO Users (user_id, username, joined_at, last_active) VALUES (?, ?, ?, ?)",
                    (ctx.author.id, ctx.author.name, discord.utils.utcnow(), discord.utils.utcnow())
                )
            else:
                await self.db.execute(
                    "UPDATE Users SET last_active = ? WHERE user_id = ?",
                    (discord.utils.utcnow(), ctx.author.id)
                )

            if ctx.author.id is not None:
                await self.db.execute(
                    "INSERT INTO Logs (user_id, command, channel, message, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (ctx.author.id, ctx.command.name, ctx.channel.id, ctx.message.content, discord.utils.utcnow())
                )
            else:
                logger.error("Cannot log command: ctx.author.id is None.")

        except Exception as e:
            logger.error(f"Error processing on_command event: {e}", exc_info=True)

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Verification(bot))
