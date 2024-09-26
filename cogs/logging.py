import discord
import logging
from discord.ext import commands
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.embeds = self.config['embeds']
        self.identifiers = self.config['identifiers']
        self.logging_channel_id = int(self.identifiers.get('logging_channel_id'))
        self.db = self.bot.get_cog("Database")

    async def send_embed(self, channel, title: str, description: str, color_key: str = 'primary',
                         fields: Optional[List[Tuple[str, str, bool]]] = None,
                         footer_text: Optional[str] = None, image_url: Optional[str] = None):
        embed = discord.Embed(title=title, description=description,
                              color=int(self.config['embeds']['embed_colors'][color_key], 16),
                              timestamp=discord.utils.utcnow())

        if footer_text is None:
            footer_text = self.config['embeds']['embed_footer']
        embed.set_footer(text=footer_text)

        if image_url is None:
            image_url = self.config['embeds']['embed_banner']
        embed.set_image(url=image_url)

        if fields:
            for field in fields:
                embed.add_field(name=field[0], value=field[1], inline=field[2] if len(field) > 2 else False)

        await channel.send(embed=embed)

    async def log_message(self, title: str, description: str):
        try:
            logging_channel = self.bot.get_channel(self.logging_channel_id)
            if logging_channel:
                await self.send_embed(logging_channel, title, description, color_key='primary')

                await self.db.execute(
                    "INSERT INTO Logs (message, timestamp) VALUES (?,?)",
                    (description, discord.utils.utcnow())
                )
            else:
                logger.error(f"Logging channel with ID {self.logging_channel_id} not found.")

        except discord.Forbidden:
            logger.error("Missing permissions to send messages in the logging channel.")
        except discord.HTTPException as e:
            logger.error(f"Failed to send log message: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while logging a message: {e}", exc_info=True)

    # --- Message-related events ---

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            await self.log_message("Message Sent", f"From: {message.author.mention}\n"
                                                   f"Channel: {message.channel.mention}\n"
                                                   f"Content: {message.content}")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.author.bot:
            description = f"Message edited by {before.author.mention} in {before.channel.mention}:\n" \
                          f"Before: {before.content}\n" \
                          f"After: {after.content}"
            await self.log_message("Message Edited", description)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.author.bot:
            description = f"Message deleted by {message.author.mention} in {message.channel.mention}:\n" \
                          f"Content: {message.content}"
            await self.log_message(f"Message Deleted", description)

    # --- Command-related events ---

    @commands.Cog.listener()
    async def on_command(self, ctx):
        await self.log_message("Command Executed",
                               f"By: {ctx.author.mention}\n"
                               f"Channel: {ctx.channel.mention}\n"
                               f"Command: {ctx.message.content}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        channel_info = ctx.channel.mention if not isinstance(ctx.channel, discord.DMChannel) else "Direct Message"
        await self.log_message("Command Error", f"For: {ctx.author.mention}\n"
                                                 f"Channel: {channel_info}\n"
                                                 f"Error: {error}")

    # --- Member-related events ---

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not member.bot:
            await self.log_message("Member Joined", f"{member.mention} has joined the server.")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not member.bot:
            await self.log_message("Member Left", f"{member.mention} has left the server.")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if not before.bot and not after.bot:
            if before.roles != after.roles:
                before_roles = ', '.join([role.name for role in before.roles])
                after_roles = ', '.join([role.name for role in after.roles])
                await self.log_message("Member Roles Updated",
                                        f"Member: {before.mention}\n"
                                        f"Before: {before_roles}\n"
                                        f"After: {after_roles}")
            if before.nick != after.nick:
                await self.log_message("Member Nickname Updated",
                                        f"Member: {before.mention}\n"
                                        f"Before: {before.nick}\n"
                                        f"After: {after.nick}")
            if before.display_name != after.display_name:
                await self.log_message("Member Display Name Updated",
                                        f"Member: {before.mention}\n"
                                        f"Before: {before.display_name}\n"
                                        f"After: {after.display_name}")

    # --- Voice-related events ---

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot:
            if before.channel != after.channel:
                if before.channel is None:
                    await self.log_message("Voice Channel Joined",
                                          f"{member.mention} joined voice channel {after.channel.name}.")
                elif after.channel is None:
                    await self.log_message("Voice Channel Left",
                                          f"{member.mention} left voice channel {before.channel.name}.")
                else:
                    await self.log_message("Voice Channel Changed",
                                          f"{member.mention} moved from {before.channel.name} "
                                          f"to {after.channel.name}.")
            if before.mute != after.mute:
                action = "Muted" if after.mute else "Unmuted"
                await self.log_message(f"Voice {action}",
                                      f"{member.mention} was {action.lower()} in {before.channel.name}.")
            if before.deaf != after.deaf:
                action = "Deafened" if after.deaf else "Undeafened"
                await self.log_message(f"Voice {action}",
                                      f"{member.mention} was {action.lower()} in {before.channel.name}.")
            if before.self_mute != after.self_mute:
                action = "Muted" if after.self_mute else "Unmuted"
                await self.log_message(f"Voice Self-{action}",
                                      f"{member.mention} self-{action.lower()} in {before.channel.name}.")
            if before.self_deaf != after.self_deaf:
                action = "Deafened" if after.self_deaf else "Undeafened"
                await self.log_message(f"Voice Self-{action}",
                                      f"{member.mention} self-{action.lower()} in {before.channel.name}.")

    # --- Guild-related events ---

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.log_message("Guild Joined", f"Bot joined {guild.name} (ID: {guild.id})")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.log_message("Guild Left", f"Bot left {guild.name} (ID: {guild.id})")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        await self.log_message("Role Created", f"In {role.guild.name}: {role.name}")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.log_message("Role Deleted", f"In {role.guild.name}: {role.name}")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        changes = []
        if before.name != after.name:
            changes.append(f"Name: {before.name} -> {after.name}")
        if before.permissions != after.permissions:
            changes.append(f"Permissions: Changed")
        if before.color != after.color:
            changes.append(f"Color: {before.color} -> {after.color}")
        if before.hoist != after.hoist:
            changes.append(f"Hoisted: {before.hoist} -> {after.hoist}")
        if before.mentionable != after.mentionable:
            changes.append(f"Mentionable: {before.mentionable} -> {after.mentionable}")
        if changes:
            await self.log_message("Role Updated",
                                    f"In {before.guild.name} for role {before.name}:\n" + "\n".join(changes))

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self.log_message("Channel Created",
                              f"In {channel.guild.name}: {channel.name} (Type: {channel.type})")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.log_message("Channel Deleted",
                              f"In {channel.guild.name}: {channel.name} (Type: {channel.type})")

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        changes = []
        if before.name != after.name:
            changes.append(f"Name: {before.name} -> {after.name}")
        if changes:
            await self.log_message("Channel Updated",
                                  f"In {before.guild.name} for channel {before.name}:\n" + "\n".join(changes))

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        added_emojis = set(after) - set(before)
        removed_emojis = set(before) - set(after)
        if added_emojis:
            await self.log_message("Emojis Added",
                                    f"In {guild.name}: {', '.join(str(e) for e in added_emojis)}")
        if removed_emojis:
            await self.log_message("Emojis Removed",
                                    f"In {guild.name}: {', '.join(str(e) for e in removed_emojis)}")

def setup(bot):
    bot.add_cog(Logging(bot))
