import discord
import asyncio
import logging
import time
from discord.ext import commands
from discord.app_commands import AppCommandError, MissingPermissions
from helpers import send_and_delete
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.settings = self.config['settings']
        self.embeds = self.config['embeds']
        self.identifiers = self.config['identifiers']
        self.moderation = self.config['moderation']
        self.spam_threshold = self.moderation['spam_threshold']
        self.spam_message_count = self.moderation['spam_message_count']
        self.wall_of_text_length = self.moderation['wall_of_text_length']
        self.max_emojis = self.moderation['max_emojis']
        self.max_attachments = self.moderation['max_attachments']
        self.max_mentions = self.moderation['max_mentions']
        self.first_mute_duration = self.moderation['first_mute_duration']
        self.second_mute_duration = self.moderation['second_mute_duration']
        self.user_message_counts = {}
        self.db = self.bot.get_cog('Database')

    async def send_embed(self, ctx, title, description, color_key='primary', ephemeral=True):
        color = int(self.embeds['embed_colors'][color_key], 16)
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=self.embeds['embed_footer'])
        embed.set_image(url=self.embeds['embed_banner'])
        await ctx.send(embed=embed, ephemeral=ephemeral)

    async def log_action(self, ctx, action, member, reason=None):
        audit_channel_id = int(self.identifiers.get('audit_channel_id'))
        audit_channel = discord.utils.get(ctx.guild.channels, id=audit_channel_id)
        if audit_channel:
            embed = discord.Embed(title=f"{action.capitalize()} Action", color=int(self.embeds['embed_colors']['primary'], 16))
            embed.add_field(name="Member", value=member.mention, inline=False)
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            embed.set_footer(text=self.embeds['embed_footer'])
            embed.set_image(url=self.embeds['embed_banner'])
            await audit_channel.send(embed=embed)

        logging_cog = self.bot.get_cog('Logging')
        if logging_cog:
            await logging_cog.log_message(f"{action.capitalize()} Action: {member.mention} by {ctx.author.mention}. Reason: {reason}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        await self.check_for_spam(message)
        await self.check_message_content(message)

    async def check_for_spam(self, message):
        user_id = message.author.id
        current_time = time.time()

        if user_id not in self.user_message_counts:
            self.user_message_counts[user_id] = []

        self.user_message_counts[user_id].append(current_time)

        self.user_message_counts[user_id] = [
            msg_time for msg_time in self.user_message_counts[user_id]
            if current_time - msg_time <= self.spam_threshold
        ]

        if len(self.user_message_counts[user_id]) >= self.spam_message_count:
            await self.handle_spam(message)

    async def handle_spam(self, message):
        await message.delete()
        await self.mute_user(message.author, reason="Spamming")

    async def mute_user(self, member, reason, duration=None):
        muted_role_id = int(self.identifiers.get('muted_id'))
        muted_role = discord.utils.get(member.guild.roles, id=muted_role_id)
        if not muted_role:
            await send_and_delete(self, f"`Error: Muted role with ID '{muted_role_id}' not found. Please check your configuration.`", delay=self.settings['delete_errors_delay'], delete_type='error')
            return

        if duration is None:
            if member.id in self.user_message_counts:
                last_mute_time = self.user_message_counts[member.id][-1]
                time_since_last_mute = time.time() - last_mute_time
                if time_since_last_mute <= self.second_mute_duration:
                    mute_duration = self.second_mute_duration
                else:
                    mute_duration = self.first_mute_duration
            else:
                mute_duration = self.first_mute_duration
        else:
            mute_duration = duration

        await member.add_roles(muted_role, reason=reason)
        await send_and_delete(self, f"`{member.mention} has been muted for {mute_duration} seconds for: {reason}`", delay=self.settings['delete_response_delay'])
        await self.log_action(self, "mute", member, reason)

        # Update mute status in database
        muted_until = discord.utils.utcnow() + timedelta(seconds=mute_duration)
        await self.db.execute(
            "UPDATE Users SET muted_until = ? WHERE user_id = ?",
            (muted_until, member.id)
        )

        await asyncio.sleep(mute_duration)
        await member.remove_roles(muted_role, reason="Mute duration expired")
        await send_and_delete(self, f"`{member.mention}'s mute duration has expired.`", delay=self.settings['delete_response_delay'])

        # Clear mute status in database
        await self.db.execute(
            "UPDATE Users SET muted_until = NULL WHERE user_id = ?",
            (member.id,)
        )

    async def check_message_content(self, message):
        if len(message.content) > self.wall_of_text_length:
            await self.handle_wall_of_text(message)

        if len(message.mentions) > self.max_mentions:
            await self.handle_excessive_mentions(message)

        if len(message.attachments) > self.max_attachments:
            await self.handle_excessive_attachments(message)

        if len([e for e in message.content if e in '']) > self.max_emojis:
            await self.handle_excessive_emojis(message)

    async def handle_wall_of_text(self, message):
        await message.delete()
        await message.author.send("`Your message was deleted because it exceeded the character limit.`")

    async def handle_excessive_mentions(self, message):
        await message.delete()
        await message.author.send("`Your message was deleted because it contained too many mentions.`")

    async def handle_excessive_attachments(self, message):
        await message.delete()
        await message.author.send("`Your message was deleted because it contained too many attachments.`")

    async def handle_excessive_emojis(self, message):
        await message.delete()
        await message.author.send("`Your message was deleted because it contained too many emojis.`")

    @commands.command(name="kick", help="Kicks a user from the server. Usage: ..kick <user> [reason]")
    @commands.has_permissions(kick_members=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        try:
            await member.kick(reason=reason)
            await send_and_delete(ctx, f"`{member.mention} has been kicked.`", delay=self.settings['delete_response_delay'])
            await self.log_action(ctx, "kick", member, reason)
        except discord.Forbidden:
            await send_and_delete(ctx, "`Error: I do not have permission to kick this member.`", delay=self.settings['delete_errors_delay'], delete_type='error')
        except Exception as e:
            logger.error(f"An unexpected error occurred in kick: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred while kicking the member. Please try again later.`", delay=self.settings['delete_errors_delay'], delete_type='error')

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_and_delete(ctx, "`Error: Please mention a user to kick. Example: ..kick @user`", delay=self.settings['delete_errors_delay'], delete_type='error')
        elif isinstance(error, commands.MissingPermissions):
            await send_and_delete(ctx, "`Error: You do not have permission to kick members.`", delay=self.settings['delete_errors_delay'], delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}")
            await send_and_delete(ctx, "`Error: An unexpected error occurred. Please try again later.`", delay=self.settings['delete_errors_delay'], delete_type='error')

    @commands.command(name="ban", help="Bans a user from the server. Usage: ..ban <user> [reason]")
    @commands.has_permissions(ban_members=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        try:
            await member.ban(reason=reason)
            await send_and_delete(ctx, f"`{member.mention} has been banned.`", delay=self.settings['delete_response_delay'])
            await self.log_action(ctx, "ban", member, reason)
        except discord.Forbidden:
            await send_and_delete(ctx, "`Error: I do not have permission to ban this member.`", delay=self.settings['delete_errors_delay'], delete_type='error')
        except Exception as e:
            logger.error(f"An unexpected error occurred in ban: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred while banning the member. Please try again later.`", delay=self.settings['delete_errors_delay'], delete_type='error')

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_and_delete(ctx, "`Error: Please mention a user to ban. Example: ..ban @user`", delay=self.settings['delete_errors_delay'], delete_type='error')
        elif isinstance(error, commands.MissingPermissions):
            await send_and_delete(ctx, "`Error: You do not have permission to ban members.`", delay=self.settings['delete_errors_delay'], delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}")
            await send_and_delete(ctx, "`Error: An unexpected error occurred. Please try again later.`", delay=self.settings['delete_errors_delay'], delete_type='error')

    @commands.command(name="unban", help="Unbans a user from the server. Usage: ..unban <user#1234>")
    @commands.has_permissions(ban_members=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def unban(self, ctx, *, user: discord.User):
        try:
            await ctx.guild.unban(user)
            await send_and_delete(ctx, f"`{user} has been unbanned.`", delay=self.settings['delete_response_delay'])
            await self.log_action(ctx, "unban", user)
        except discord.Forbidden:
            await send_and_delete(ctx, "`Error: I do not have permission to unban this user.`", delay=self.settings['delete_errors_delay'], delete_type='error')
        except Exception as e:
            logger.error(f"An unexpected error occurred in unban: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred while unbanning the user. Please try again later.`", delay=self.settings['delete_errors_delay'], delete_type='error')

    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_and_delete(ctx, "`Error: Please provide a user to unban in the format 'user#1234'. Example: ..unban ExampleUser#1234`", delay=self.settings['delete_errors_delay'], delete_type='error')
        elif isinstance(error, commands.MissingPermissions):
            await send_and_delete(ctx, "`Error: You do not have permission to unban members.`", delay=self.settings['delete_errors_delay'], delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}")
            await send_and_delete(ctx, "`Error: An unexpected error occurred. Please try again later.`", delay=self.settings['delete_errors_delay'], delete_type='error')

    @commands.command(name="mute", help="Mutes a user in the server. Usage: ..mute <user> [reason] [duration in seconds]")
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def mute(self, ctx, member: discord.Member, *, reason=None, duration: int = None):
        try:
            await self.mute_user(member, reason, duration)
        except discord.Forbidden:
            await send_and_delete(ctx, "`Error: I do not have permission to mute this member.`", delay=self.settings['delete_errors_delay'], delete_type='error')
        except Exception as e:
            logger.error(f"An unexpected error occurred in mute: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred while muting the member. Please try again later.`", delay=self.settings['delete_errors_delay'], delete_type='error')

    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_and_delete(ctx, "`Error: Please mention a user to mute. Example: ..mute @user`", delay=self.settings['delete_errors_delay'], delete_type='error')
        elif isinstance(error, commands.MissingPermissions):
            await send_and_delete(ctx, "`Error: You do not have permission to mute members.`", delay=self.settings['delete_errors_delay'], delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}")
            await send_and_delete(ctx, "`Error: An unexpected error occurred. Please try again later.`", delay=self.settings['delete_errors_delay'], delete_type='error')

    @commands.command(name="unmute", help="Unmutes a user in the server. Usage: ..unmute <user>")
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def unmute(self, ctx, member: discord.Member):
        try:
            muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
            if not muted_role:
                await send_and_delete(ctx, "`Error: Muted role not found. Please create a role named 'Muted'.`", delay=self.settings['delete_errors_delay'], delete_type='error')
                return

            await member.remove_roles(muted_role)
            await send_and_delete(ctx, f"`{member.mention} has been unmuted.`", delay=self.settings['delete_response_delay'])
            await self.log_action(ctx, "unmute", member)
        except discord.Forbidden:
            await send_and_delete(ctx, "`Error: I do not have permission to unmute this member.`", delay=self.settings['delete_errors_delay'], delete_type='error')
        except Exception as e:
            logger.error(f"An unexpected error occurred in unmute: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred while unmuting the member. Please try again later.`", delay=self.settings['delete_errors_delay'], delete_type='error')

    @unmute.error
    async def unmute_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_and_delete(ctx, "`Error: Please mention a user to unmute. Example: ..unmute @user`", delay=self.settings['delete_errors_delay'], delete_type='error')
        elif isinstance(error, commands.MissingPermissions):
            await send_and_delete(ctx, "`Error: You do not have permission to unmute members.`", delay=self.settings['delete_errors_delay'], delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}")
            await send_and_delete(ctx, "`Error: An unexpected error occurred. Please try again later.`", delay=self.settings['delete_errors_delay'], delete_type='error')

    @commands.command(name="warn", help="Warns a user. Usage: ..warn <user> [reason]")
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        try:
            await send_and_delete(ctx, f"{member.mention} has received a warning: {reason}", delay=self.settings['delete_response_delay'])
            await self.log_action(ctx, "warn", member, reason)

            await self.db.execute(
                "UPDATE Users SET warn_count = warn_count + 1 WHERE user_id = ?",
                (member.id,)
            )
        except Exception as e:
            logger.error(f"An unexpected error occurred in warn: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred while warning the user. Please try again later.`", delay=self.settings['delete_errors_delay'], delete_type='error')

    @warn.error
    async def warn_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_and_delete(ctx, "`Error: Please mention a user to warn. Example: ..warn @user`", delay=self.settings['delete_errors_delay'], delete_type='error')
        elif isinstance(error, commands.MissingPermissions):
            await send_and_delete(ctx, "`Error: You do not have permission to warn members.`", delay=self.settings['delete_errors_delay'], delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}")
            await send_and_delete(ctx, "`Error: An unexpected error occurred. Please try again later.`", delay=self.settings['delete_errors_delay'], delete_type='error')

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Admin(bot))
