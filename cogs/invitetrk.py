import discord
from discord.ext import commands
import datetime
import asyncio


class InviteTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites = {}
        self.mod_channel_id = 817188083325349900  # Replace with your mod channel ID
        self.invite_log = {}
        self.task = self.bot.loop.create_task(self.track_invites())

    async def track_invites(self):
        await self.bot.wait_until_ready()
        while True:
            try:
                guild = self.bot.get_guild(817188083325349900)
                if guild:
                    self.invites = await guild.invites()
                    await asyncio.sleep(60)  # Check every 60 seconds
            except Exception as e:
                print(f"Error tracking invites: {e}")
                await asyncio.sleep(60)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            invite = await self.get_invite_used(member)
            if invite:
                self.log_invite(invite, member)
        except Exception as e:
            print(f"Error logging invite for {member.name}: {e}")

    async def get_invite_used(self, member):
        for invite in self.invites:
            if invite.uses > 0:
                if invite.code == member.id:
                    return invite
        return None

    def log_invite_to_channel(self, invite, member):
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"**{timestamp}** - **{member.name}#{member.discriminator}** joined using invite code **{invite.code}** (created by **{invite.inviter.name}#{invite.inviter.discriminator}**)"
        mod_channel = self.bot.get_channel(self.mod_channel_id)
        if mod_channel:
            asyncio.create_task(mod_channel.send(log_message))
        else:
            print(f"Error finding mod channel: {self.mod_channel_id}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def log_invite(self, ctx, member: discord.Member):
        """Logs the invite used by a member."""
        try:
            invite = await self.get_invite_used(member)
            if invite:
                self.log_invite(invite, member)
                await ctx.send(f"Invite used by {member.name} logged.")
            else:
                await ctx.send(f"No invite found for {member.name}.")
        except Exception as e:
            print(f"Error logging invite for {member.name}: {e}")
            await ctx.send("An error occurred while logging the invite.")


def setup(bot):
    bot.add_cog(InviteTracker(bot))
