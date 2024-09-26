import discord
from discord.ext import commands, tasks
import asyncio
import logging
import json
from helpers import send_and_delete, create_embed  # type: ignore

logger = logging.getLogger(__name__)

class Roles(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.reaction_roles = {
            "👻": int(self.config['identifiers']['beginner_role_id']),
            "💀": int(self.config['identifiers']['intermediate_role_id']),
            "😈": int(self.config['identifiers']['advanced_role_id']),
            "🌐": int(self.config['identifiers']['networking_role_id']),
            "🕸️": int(self.config['identifiers']['webdevelopment_role_id']),
            "⚙️": int(self.config['identifiers']['reversing_role_id']),
            "🏹": int(self.config['identifiers']['pentesting_role_id']),
            "⌨️": int(self.config['identifiers']['developer_role_id']),
            "🤍": int(self.config['identifiers']['whitehat_role_id']),
            "🖤": int(self.config['identifiers']['blackhat_role_id']),
            "🚨": int(self.config['identifiers']['alerts_role_id']),
        }
        self.react_messages = []
        self.db = self.bot.get_cog("Database")
        self.tiers = self.config.get('tiers', [])
        self.delete_commands = self.bot.config['settings']['delete_commands']
        self.delete_command_delay = self.bot.config['settings'][
            'delete_command_delay'
        ]
        self.delete_responses = self.bot.config['settings']['delete_responses']
        self.delete_response_delay = self.bot.config['settings'][
            'delete_response_delay'
        ]
        self.delete_errors = self.bot.config['settings']['delete_errors']
        self.delete_errors_delay = self.bot.config['settings'][
            'delete_errors_delay'
        ]

    async def setup_roles_message(self, ctx):
        if not self.db:
            logger.error(
                "Database cog is not loaded. Skipping role message setup."
            )
            await send_and_delete(
                ctx,
                content="Error setting up roles. The database is unavailable.",
                delay=self.delete_errors_delay,
                delete_type='error',
            )
            return

        react_channel_id = int(self.config['identifiers']['react_channel_id'])
        react_channel = self.bot.get_channel(react_channel_id)

        if react_channel:
            try:
                # Embed for Preferences
                preferences_embed = create_embed(
                    title="Ethics",
                    description="`Choose your Ethics:`",
                    color_key='primary',
                    fields=[
                        ("🤍 Whitehat", "`For ethical hackers.`", False),
                        ("🖤 Blackhat", "`For unethical hackers.`", False),
                    ],
                    config=self.bot.config,
                    image_url=None
                )
                # Embed for Skill Level
                skill_embed = create_embed(
                    title="Skill Level Roles",
                    description="`Choose your Skill Level:`",
                    color_key='primary',
                    fields=[
                        ("👻 Beginner", "`For new users.`", False),
                        ("💀 Intermediate", "`For experienced users.`", False),
                        ("😈 Advanced", "`For veteran users.`", False),
                    ],
                    config=self.bot.config,
                    image_url=None
                )

                # Embed for Alerts
                alerts_embed = create_embed(
                    title="Alerts",
                    description="`Toggle alerts ON / OFF:`",
                    color_key='primary',
                    fields=[
                        ("🚨 Alerts", "`Get notified about critical vulnerability disclosures.`", False)
                    ],
                    config=self.bot.config,
                    image_url=None
                )

                # Embed for Other Roles
                other_embed = create_embed(
                    title="Interested Roles",
                    description="`Choose your Interests:`",
                    color_key='primary',
                    fields=[
                        ("🌐 Networking", "`Networking related topics.`", False),
                        ("⌨️ Developer", "`Developer related topics.`", False),
                        ("🕸️ Web Development", "`Web application development.`", False,),
                        ("⚙️ Reversing", "`Malware analysis and reverse engineering.`", False,),
                        ("🏹 Pentesting", "`Ethical hacking and penetration testing.`", False,),
                    ],
                    config=self.bot.config,
                    image_url=None
                )

                # Final Embed
                final_embed = create_embed(
                    title="Thank you for choosing PortLords!",
                    description="Please select your desired roles from the menu above. ",
                    color_key='primary',
                    config=self.bot.config,
                )

                skill_message = await react_channel.send(embed=skill_embed)
                preferences_message = await react_channel.send(
                    embed=preferences_embed
                )
                other_message = await react_channel.send(embed=other_embed)
                alerts_message = await react_channel.send(embed=alerts_embed)
                await react_channel.send(embed=final_embed)

                for emoji in ["👻", "💀", "😈"]:
                    await skill_message.add_reaction(emoji)
                for emoji in ["🤍", "🖤"]:
                    await preferences_message.add_reaction(emoji)
                for emoji in ["🌐", "⌨️", "🕸️", "⚙️", "🏹"]:
                    await other_message.add_reaction(emoji)
                for emoji in ["🚨"]:
                    await alerts_message.add_reaction(emoji)

                self.react_messages.extend(
                    [skill_message, preferences_message, other_message, alerts_message]
                )

            except Exception as e:
                logger.error(
                    f"Error setting up reaction roles: {e}", exc_info=True
                )
                await send_and_delete(
                    ctx,
                    content="Error setting up reaction roles. Please check logs.",
                    delay=self.delete_errors_delay,
                    delete_type='error',
                )
        else:
            logger.error(f"React channel not found with ID: {react_channel_id}")
            await send_and_delete(
                ctx,
                content="Error: React channel not found. Please check config.",
                delay=self.delete_errors_delay,
                delete_type='error',
            )

    @commands.command(name="roles", help="Post and set up the reaction roles.")
    @commands.is_owner()
    async def post_roles_message(self, ctx):
        try:
            await self.setup_roles_message(ctx)
        except Exception as e:
            logger.error(f"Error posting roles message: {e}", exc_info=True)
            await send_and_delete(
                ctx,
                content="Error posting roles message. Please check logs.",
                delay=self.delete_errors_delay,
                delete_type='error',
            )

    @post_roles_message.error
    async def post_roles_message_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(
                ctx,
                content=f"`This command is on cooldown. Please try again in {retry_after:.2f} seconds.`",
                delay=self.delete_errors_delay,
                delete_type='error',
            )
        elif isinstance(error, commands.NotOwner):
            await send_and_delete(
                ctx,
                content="`Error: You do not have permission to use this command.`",
                delay=self.delete_errors_delay,
                delete_type='error',
            )
        else:
            logger.error(f"Unexpected error occurred: {error}", exc_info=True)
            await send_and_delete(
                ctx,
                content="`An unexpected error occurred. Please try again later.`",
                delay=self.delete_errors_delay,
                delete_type='error',
            )

    async def handle_reaction(self, payload: discord.RawReactionActionEvent, add: bool):
        try:
            if payload.user_id == self.bot.user.id:
                return

            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            if message in self.react_messages:
                role_id = self.reaction_roles.get(payload.emoji.name)
                if role_id is None:
                    return

                role = guild.get_role(role_id)
                if role is None:
                    logger.error(f"Role with ID {role_id} not found.")
                    return

                if add and role not in member.roles:
                    await member.add_roles(role)
                    await self.db.execute(
                        "INSERT OR IGNORE INTO UserRoles (user_id, role_id, assigned_at) VALUES (?, ?, ?)",
                        (member.id, role.id, discord.utils.utcnow()),
                    )
                elif not add and role in member.roles:
                    await member.remove_roles(role)
                    await self.db.execute(
                        "DELETE FROM UserRoles WHERE user_id = ? AND role_id = ?",
                        (member.id, role.id),
                    )

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(
                f"Error {'adding' if add else 'removing'} role {role.name} to user {member.mention}: {e}"
            )
        except discord.NotFound:
            logger.warning(
                f"Message, channel, or user not found for reaction event (payload: {payload})"
            )
        except Exception as e:
            logger.error(
                f"An error occurred while processing a reaction {'add' if add else 'remove'} event: {e}",
                exc_info=True,
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.handle_reaction(payload, add=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.handle_reaction(payload, add=False)

def setup(bot):
    bot.add_cog(Roles(bot))
