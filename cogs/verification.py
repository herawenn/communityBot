import discord
from discord.ext import commands
import asyncio

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verification_channel_id = int(bot.config['identifiers']['verification_channel_id'])
        self.verified_role_id = int(bot.config['identifiers']['verified_role_id'])
        self.unverified_role_id = int(bot.config['identifiers']['unverified_role_id'])
        self.delete_responses = bot.config['settings']['delete_responses']
        self.delete_response_delay = bot.config['settings']['delete_response_delay']
        self.verification_message = None

    async def send_and_delete(self, ctx, message):
        sent_message = await ctx.send(message)
        if self.delete_responses:
            await asyncio.sleep(self.delete_response_delay)
            await sent_message.delete()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        unverified_role = discord.utils.get(member.guild.roles, id=self.unverified_role_id)
        if unverified_role:
            await member.add_roles(unverified_role)

    @commands.command(name='verification')
    async def verification(self, ctx):
        if ctx.channel.id != self.verification_channel_id:
            await self.send_and_delete(ctx, "`You can only use this command in the verification channel.`")
            return

        embed = discord.Embed(title="**Agree & Continue**", description="🗹 `We are not responsible for the actions of our members`", color=discord.Color(0x6900ff))
        self.verification_message = await ctx.send(embed=embed)
        await self.verification_message.add_reaction('✅')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id != self.verification_message.id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)

        if member.bot:
            return

        verified_role = discord.utils.get(guild.roles, id=self.verified_role_id)
        unverified_role = discord.utils.get(guild.roles, id=self.unverified_role_id)

        if not verified_role:
            return

        if verified_role in member.roles:
            return

        if unverified_role:
            await member.remove_roles(unverified_role)

        await member.add_roles(verified_role)
        await self.send_and_delete(self.verification_message.channel, f'`{member.mention} has been verified.`')

async def setup(bot):
    await bot.add_cog(Verification(bot))
