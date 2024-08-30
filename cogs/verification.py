import discord
from discord.ext import commands
import asyncio
import logging
from helpers import send_and_delete

logger = logging.getLogger(__name__)

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.verification_message = None
        self.db = self.bot.get_cog('Database')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            unverified_role_id = int(self.config['identifiers']['unverified_role_id'])
            unverified_role = discord.utils.get(member.guild.roles, id=unverified_role_id)
            if unverified_role:
                await member.add_roles(unverified_role)

            await self.verify_member(member)
        except Exception as e:
            logger.error(f"An error occurred while adding unverified role: {e}", exc_info=True)

    async def verify_member(self, member):
        verification_channel_id = int(self.config['identifiers']['verification_channel_id'])
        verification_channel = self.bot.get_channel(verification_channel_id)

        if verification_channel:
            embed = discord.Embed(title="**Agree & Continue**", color=discord.Color(int(self.config['embeds']['embed_colors']['primary'], 16)))
            embed.add_field(name=" ", value="🗹 `We are not responsible for the actions of any user.`", inline=False)

            self.verification_message = await verification_channel.send(content=f"{member.mention}", embed=embed)
            await self.verification_message.add_reaction('✅')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
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

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
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

        except Exception as e:
            logger.error(f"Error processing on_command event: {e}")

async def setup(bot):
    await bot.add_cog(Verification(bot))
