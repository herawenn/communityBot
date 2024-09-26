import discord
import humanize
import zipfile
from discord.ext import commands, tasks
import json
import random
import logging
import os
from helpers import send_and_delete, create_embed  # type:ignore

logger = logging.getLogger(__name__)

class Nefarious(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.data = self.load_data()
        self.delete_commands = self.bot.config['settings']['delete_commands']
        self.delete_command_delay = self.bot.config['settings']['delete_command_delay']
        self.delete_responses = self.bot.config['settings']['delete_responses']
        self.delete_response_delay = self.bot.config['settings']['delete_response_delay']
        self.delete_errors = self.bot.config['settings']['delete_errors']
        self.delete_errors_delay = self.bot.config['settings']['delete_errors_delay']
        self.posted_files = self.load_posted_files()

        self.fullz_message = None
        self.stealer_message = None

        self.fullz_file = None
        self.stealer_file = None

    def load_data(self) -> list:
        data = []
        try:
            with open(self.config['paths']['fullz_path'], 'r', encoding='utf-8') as f:
                for line in f:
                    entry = json.loads(line)
                    data.append(entry)
                return data
        except FileNotFoundError:
            logger.error("Data file not found.")
            return []
        except json.JSONDecodeError:
            logger.error("Invalid JSON format in the data file.")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading data: {e}", exc_info=True)
            return []

    def load_posted_files(self) -> set:
        try:
            with open(self.config['paths']['posted_files_path'], 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except FileNotFoundError:
            logger.warning("Posted files record not found. Creating a new one.")
            self.create_posted_files_record()
            return set()
        except json.JSONDecodeError:
            logger.error("Invalid JSON format in the posted files record.")
            return set()
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading posted files: {e}", exc_info=True)
            return set()

    def create_posted_files_record(self):
        try:
            with open(self.config['paths']['posted_files_path'], 'w', encoding='utf-8') as f:
                json.dump([], f)
        except Exception as e:
            logger.error(f"An unexpected error occurred while creating the posted files record: {e}", exc_info=True)

    def save_posted_files(self):
        try:
            with open(self.config['paths']['posted_files_path'], 'w', encoding='utf-8') as f:
                json.dump(list(self.posted_files), f)
        except Exception as e:
            logger.error(f"An unexpected error occurred while saving posted files: {e}", exc_info=True)

    @commands.command(name="fullz", help="Sends a random fullz.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def fullzies(self, ctx: commands.Context):
        try:
            if self.data:
                random_entry = random.choice(self.data)
                formatted_entry = "\n".join(f"{key}: {value}" for key, value in random_entry.items())

                embed = create_embed(
                    title=" ",
                    description=f"```\n{formatted_entry}\n```",
                    color_key='primary',
                    config=self.bot.config,
                    footer_text=self.config['embeds']['embed_footer'],
                    image_url=self.config['embeds']['embed_banner']
                )

                self.fullz_file = None

                if self.fullz_message:
                    message = await ctx.channel.fetch_message(self.fullz_message.id)
                    await message.clear_reactions()
                    await message.add_reaction("📥")
                    await message.add_reaction("🗑️")
                else:
                    self.fullz_message = await ctx.send(embed=embed)
                    await self.fullz_message.add_reaction("📥")
                    await self.fullz_message.add_reaction("🗑️")

            else:
                await send_and_delete(ctx, content="No data available.", delay=self.delete_errors_delay, delete_type='error')

            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

        except Exception as e:
            logger.error(f"An unexpected error occurred in fullzies: {e}", exc_info=True)
            await send_and_delete(ctx, content="An error occurred while generating an entry. Please try again later.",
                                delay=self.delete_errors_delay, delete_type='error')

    @commands.command(name="stealer", help="Sends a stealer log.")
    async def stealzies(self, ctx: commands.Context):
        try:
            directory = self.config['paths']['stealzies_path']
            files = [f for f in os.listdir(directory) if f.endswith('.zip')]

            if not files:
                await send_and_delete(ctx, content="No zip files available.", delay=self.delete_errors_delay, delete_type='error')
                return

            file = random.choice(files)
            file_path = os.path.join(directory, file)

            file_size = os.path.getsize(file_path)
            file_size_str = humanize.naturalsize(file_size)

            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                num_files = len(zip_ref.namelist())

            embed = discord.Embed(
                title=" ",
                description=f"**`{file}`**",
                color=int(self.config['embeds']['embed_colors']['primary'], 16)
            )
            embed.add_field(name="Size:", value=f"**`{file_size_str}`**", inline=True)
            embed.add_field(name="Files:", value=f"**`{num_files}`**", inline=True)
            embed.set_footer(text=self.config['embeds']['embed_footer'])
            embed.set_image(url=self.config['embeds']['embed_banner'])

            self.stealer_file = file_path

            if self.stealer_message:
                message = await ctx.channel.fetch_message(self.stealer_message.id)
                await message.clear_reactions()
                await message.add_reaction("📥")
                await message.add_reaction("🗑️")
            else:
                self.stealer_message = await ctx.send(embed=embed)
                await self.stealer_message.add_reaction("📥")
                await self.stealer_message.add_reaction("🗑️")

            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

        except Exception as e:
            logger.error(f"An unexpected error occurred in stealzies_log: {e}", exc_info=True)
            await send_and_delete(ctx, content="An error occurred while posting the file. Please try again later.",
                                delay=self.delete_errors_delay, delete_type='error')

    @tasks.loop(minutes=60)
    async def update_fullz_embed_task(self):
        if not self.bot.config['features'].get('fullz', False):
            return

        try:
            if self.data:
                random_entry = random.choice(self.data)
                formatted_entry = "\n".join(f"{key}: {value}" for key, value in random_entry.items())

                embed = create_embed(
                    title=" ",
                    description=f"```\n{formatted_entry}\n```",
                    color_key='primary',
                    config=self.bot.config,
                    footer_text=self.config['embeds']['embed_footer'],
                    image_url=self.config['embeds']['embed_banner']
                )

                if self.fullz_message:
                    message = await self.bot.get_channel(self.fullz_message.channel.id).fetch_message(self.fullz_message.id)
                    await message.clear_reactions()
                    await message.add_reaction("📥")
                    await message.add_reaction("🗑️")
                    await message.edit(embed=embed)
                else:
                    channel_id = self.config['identifiers']['fullz_channel_id']
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        self.fullz_message = await channel.send(embed=embed)
                        await self.fullz_message.add_reaction("📥")
                        await self.fullz_message.add_reaction("🗑️")
                    else:
                        logger.error("Channel not found for fullz embed.")

        except Exception as e:
            logger.error(f"An unexpected error occurred while updating the fullz embed: {e}", exc_info=True)

    @tasks.loop(minutes=5)
    async def update_stealer_embed_task(self):
        if not self.bot.config['features'].get('stealer', False):
            return

        try:
            directory = self.config['paths']['stealzies_path']
            files = [f for f in os.listdir(directory) if f.endswith('.zip')]

            if not files:
                return

            file = random.choice(files)
            file_path = os.path.join(directory, file)

            file_size = os.path.getsize(file_path)
            file_size_str = humanize.naturalsize(file_size)

            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                num_files = len(zip_ref.namelist())

            embed = discord.Embed(
                title=" ",
                description=f"**`{file}`**",
                color=int(self.config['embeds']['embed_colors']['primary'], 16)
            )
            embed.add_field(name="Size:", value=f"**`{file_size_str}`**", inline=True)
            embed.add_field(name="Files:", value=f"**`{num_files}`**", inline=True)
            embed.set_footer(text=self.config['embeds']['embed_footer'])
            embed.set_image(url=self.config['embeds']['embed_banner'])

            if self.stealer_message:
                message = await self.bot.get_channel(self.stealer_message.channel.id).fetch_message(self.stealer_message.id)
                await message.clear_reactions()
                await message.add_reaction("📥")
                await message.add_reaction("🗑️")
                await message.edit(embed=embed)
            else:
                channel_id = self.config['identifiers']['stealer_channel_id']
                channel = self.bot.get_channel(channel_id)
                if channel:
                    self.stealer_message = await channel.send(embed=embed)
                    await self.stealer_message.add_reaction("📥")
                    await self.stealer_message.add_reaction("🗑️")
                else:
                    logger.error("Channel not found for stealer embed.")

        except Exception as e:
            logger.error(f"An unexpected error occurred while updating the stealer embed: {e}", exc_info=True)

    async def handle_reaction(self, payload):
        try:
            channel = self.bot.get_channel(payload.channel_id)

            if isinstance(channel, discord.TextChannel):
                guild = channel.guild
                member = guild.get_member(payload.user_id)

                if member.bot:
                    return

                message = await channel.fetch_message(payload.message_id)

                if self.fullz_message is not None and message.id == self.fullz_message.id and payload.emoji.name == "📥":
                    if self.fullz_file:
                        await channel.send(file=discord.File(self.fullz_file))
                        self.fullz_file = None
                elif self.fullz_message is not None and message.id == self.fullz_message.id and payload.emoji.name == "🗑️":
                    await self.fullz_message.delete()
                    self.fullz_message = None
                elif self.stealer_message is not None and message.id == self.stealer_message.id and payload.emoji.name == "📥":
                    if self.stealer_file:
                        await channel.send(file=discord.File(self.stealer_file))
                        self.stealer_file = None
                elif self.stealer_message is not None and message.id == self.stealer_message.id and payload.emoji.name == "🗑️":
                    await self.stealer_message.delete()
                    self.stealer_message = None

            else:
                logger.info("Reaction added/removed in a DM channel. Ignoring.")

        except Exception as e:
            logger.error(f"An unexpected error occurred while handling reactions: {e}", exc_info=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.handle_reaction(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.handle_reaction(payload)

def setup(bot: commands.Bot):
    bot.add_cog(Nefarious(bot))
