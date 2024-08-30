import discord
from discord.ext import commands
import asyncio
import logging
from helpers import send_and_delete

logger = logging.getLogger(__name__)

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.reaction_roles = {
            "🤖": int(self.config['identifiers']['beginner_role_id']),
            "🕵️": int(self.config['identifiers']['intermediate_role_id']),
            "😈": int(self.config['identifiers']['advanced_role_id']),
            "🌐": int(self.config['identifiers']['networking_role_id']),
            "🕸️": int(self.config['identifiers']['websecurity_role_id']),
            "⚙️": int(self.config['identifiers']['reversing_role_id']),
            "🏹": int(self.config['identifiers']['pentesting_role_id']),
            "🚨": int(self.config['identifiers']['alerts_role_id']),
        }
        self.react_message = None
        self.db = self.bot.get_cog("Database")
        self.tiers = self.config.get('tiers', [])

    @commands.Cog.listener()
    async def on_ready(self):
        react_channel_id = int(self.config['identifiers']['react_channel_id'])
        react_channel = self.bot.get_channel(react_channel_id)

        if react_channel:
            try:
                embed = discord.Embed(title="**Role Selection**", color=discord.Color(int(self.config['embeds']['embed_colors']['primary'], 16)))
                embed.add_field(name=" ", value="React to the following emojis to select your desired roles and alerts.", inline=False)

                # Skill Level
                embed.add_field(name="🤖 Beginner", value="`For new users.`", inline=False)
                embed.add_field(name="🕵️ Intermediate", value="`For users with some experience.`", inline=False)
                embed.add_field(name="😈 Advanced", value="`For experienced users.`", inline=False)

                # Interests
                embed.add_field(name="🌐 Networking", value="`Networking related topics.`", inline=False)
                embed.add_field(name="🕸️ Web Security", value="`Web application security.`", inline=False)
                embed.add_field(name="⚙️ Reversing", value="`Malware analysis and reverse engineering.`", inline=False)
                embed.add_field(name="🏹 Pentesting", value="`Ethical hacking and penetration testing.`", inline=False)

                # Alerts
                embed.add_field(name="🚨 Vulnerability Alerts", value="`Get notified about critical vulnerability disclosures.`", inline=False)

                self.react_message = await react_channel.send(embed=embed)
                for emoji in self.reaction_roles:
                    await self.react_message.add_reaction(emoji)
            except Exception as e:
                logger.error(f"Error setting up reaction roles in #react: {e}")
        else:
            logger.error(f"React channel not found with ID: {react_channel_id}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            if self.react_message is None or payload.message_id != self.react_message.id:
                return

            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)

            if member.bot:
                return

            role_id = self.reaction_roles.get(payload.emoji.name)
            if role_id is None:
                return

            role = guild.get_role(role_id)
            if role is None:
                logger.error(f"Role with ID {role_id} not found.")
                return

            await member.add_roles(role)

            await self.db.execute(
                "INSERT OR IGNORE INTO UserRoles (user_id, role_id, assigned_at) VALUES (?, ?, ?)",
                (member.id, role.id, discord.utils.utcnow())
            )

        except Exception as e:
            logger.error(f"An error occurred while processing a reaction add event: {e}", exc_info=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        try:
            if self.react_message is None or payload.message_id != self.react_message.id:
                return

            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)

            if member.bot:
                return

            role_id = self.reaction_roles.get(payload.emoji.name)
            if role_id is None:
                return

            role = guild.get_role(role_id)
            if role is None:
                logger.error(f"Role with ID {role_id} not found.")
                return

            await member.remove_roles(role)

            await self.db.execute(
                "DELETE FROM UserRoles WHERE user_id = ? AND role_id = ?",
                (member.id, role.id)
            )

        except Exception as e:
            logger.error(f"An error occurred while processing a reaction remove event: {e}", exc_info=True)

async def setup(bot):
    await bot.add_cog(Roles(bot))
