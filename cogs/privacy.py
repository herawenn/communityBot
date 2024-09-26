import discord
from discord.ext import commands, tasks
import asyncio
import logging
import json
import subprocess
import tempfile
import os
import random
import datetime
import aiohttp
from typing import Dict
import string
from helpers import send_and_delete, create_embed  # type: ignore

logger = logging.getLogger(__name__)

class Privacy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = bot.config
        self.db = self.bot.get_cog("Database")
        self.delete_commands = self.bot.config['settings']['delete_commands']
        self.delete_command_delay = self.bot.config['settings']['delete_command_delay']
        self.delete_responses = self.bot.config['settings']['delete_responses']
        self.delete_response_delay = self.bot.config['settings']['delete_response_delay']
        self.delete_errors = self.bot.config['settings']['delete_errors']
        self.delete_errors_delay = self.bot.config['settings']['delete_errors_delay']
        self.tips = None
        self.data_brokers = None
        self.removal_links = None

        self.bot.loop.create_task(self.load_tips())
        self.bot.loop.create_task(self.load_data_brokers())
        self.bot.loop.create_task(self.load_removal_links())
        if self.bot.config['features']['security_tips']:
            self.send_security_tip.start()

    # --- Helper Functions ---

    async def load_json_data(self, file_path: str) -> Dict:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"{file_path} not found.")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON format in {file_path}.")
            return {}

    async def load_tips(self):
        self.tips = await self.load_json_data(self.config['paths']['tips_file_path'])

    async def load_data_brokers(self):
        self.data_brokers = await self.load_json_data(self.config['paths']['brokers_file_path'])

    async def load_removal_links(self):
        self.removal_links = await self.load_json_data(self.config['paths']['removal_file_path'])

    async def log_privacy_command(self, ctx: commands.Context, command: str, *args):
        try:
            log_message = f"User {ctx.author.name}#{ctx.author.discriminator} used command {command} with arguments {args}"
            logger.info(log_message)
        except Exception as e:
            logger.error(f"Error logging privacy command: {e}", exc_info=True)

    # --- Commands ---

    @commands.command(name='privacy', help="Get data removal links for popular data brokers or specific services.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def privacy(self, ctx: commands.Context, service: str = None):
        try:
            if service is None and not self.removal_links:
                await send_and_delete(ctx, content="`No data broker information is available.`", delay=self.delete_response_delay)
                return

            links_per_page = 3
            total_pages = (len(self.removal_links) + links_per_page - 1) // links_per_page

            async def send_page(page_num: int):
                start_index = (page_num - 1) * links_per_page
                end_index = start_index + links_per_page
                page_links = self.removal_links[start_index:end_index]
                fields = [(link_data.get('name', 'N/A'), f"`{link_data.get('link', 'N/A')}`", False)
                          for link_data in page_links]
                embed = create_embed(title="Known Data Brokers",
                                      description="`Usage: ..privacy <service>`\n\n`..privacy Facebook or ..privacy Spotify\n`",
                                      color_key='primary',
                                      fields=fields,
                                      footer_text=f"Page {page_num} of {total_pages}",
                                      config=self.bot.config
                                      )
                if page_num == 1:
                    message = await ctx.send(embed=embed)
                else:
                    message = await embed_message.edit(embed=embed)
                return message

            embed_message = await send_page(1)

            if total_pages > 1:
                await embed_message.add_reaction('◀️')
                await embed_message.add_reaction('▶️')

                def check(reaction: discord.Reaction, user: discord.User):
                    return user == ctx.author and str(reaction.emoji) in ['◀️', '▶️']

                current_page = 1
                while True:
                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                        if str(reaction.emoji) == '▶️' and current_page < total_pages:
                            current_page += 1
                            embed_message = await send_page(current_page)
                        elif str(reaction.emoji) == '◀️' and current_page > 1:
                            current_page -= 1
                            embed_message = await send_page(current_page)
                        await embed_message.remove_reaction(reaction, user)
                    except asyncio.TimeoutError:
                        break

                await self.log_privacy_command(ctx, "privacy")

            else:
                with open("files/json/links.json", 'r') as f:
                    removal_links = json.load(f)

                if service.lower() in removal_links:
                    link = removal_links[service.lower()]
                    await send_and_delete(ctx, content=f"`{service.capitalize()}`\n\n{link}",
                                          delay=self.delete_response_delay)
                    await self.log_privacy_command(ctx, "privacy", service)
                else:
                    await send_and_delete(ctx,
                                          content=f"`Service '{service}' not found. Check the command usage.`",
                                          delay=self.delete_errors_delay, delete_type='error')

            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

        except Exception as e:
            logger.error(f"An unexpected error occurred in privacy: {e}", exc_info=True)
            await send_and_delete(ctx,
                                  content="`An error occurred while processing the command. Please try again later.`",
                                  delay=self.delete_errors_delay, delete_type='error')

    @commands.command(name='username', help="Searches top 500 sites. Usage: ..myusername <username>")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def username(self, ctx: commands.Context, username: str):
        try:
            embed = create_embed(title="Starting Search",
                                  description="`Depending on exposure level, this could take a bit. Results will be sent via DM.`",
                                  color_key='primary',
                                  config=self.bot.config
                                  )
            await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)

            async with ctx.typing():
                process = await asyncio.create_subprocess_exec(
                    'maigret', username, '--no-recursion', '--no-extracting',
                    '--no-progressbar', '--no-color', '--txt', '--timeout', '15',
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode == 0:
                    output = stdout.decode("utf-8").strip()
                    filtered_output = self.filter_output(output)

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
                        temp_file.write(filtered_output.encode("utf-8"))
                        temp_file_path = temp_file.name

                    with open(temp_file_path, 'rb') as file:
                        await ctx.author.send(file=discord.File(file, "usernames.txt"))

                    os.remove(temp_file_path)

                    embed = create_embed(title=" ",
                                          description="`Results sent via DM.`",
                                          color_key='primary',
                                          config=self.bot.config
                                          )
                    await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)

                    await self.log_privacy_command(ctx, "myusername", username)

                else:
                    error_output = stderr.decode("utf-8").strip()
                    logger.error(f"Maigret failed: {error_output}")
                    await send_and_delete(ctx, content=f"`Username search failed: {error_output}`", delay=self.delete_errors_delay, delete_type='error')

            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

        except Exception as e:
            logger.error(f"An unexpected error occurred in footprint: {e}", exc_info=True)
            await send_and_delete(ctx, content="`An error occurred while searching. Please try again later.`", delay=self.delete_errors_delay, delete_type='error')

    @commands.command(name='password', help="Check the strength of a password. Usage: ..ratepassword <password>")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def password(self, ctx: commands.Context, password: str):
        try:
            strength = self.custom_password_strength(password)
            embed = create_embed(title="Password Strength",
                                  description=f"`Password Rating: {strength}/4`",
                                  color_key='primary',
                                  config=self.bot.config
                                  )
            await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)

            await self.log_privacy_command(ctx, "ratepassword", password)
            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

        except Exception as e:
            logger.error(f"An unexpected error occurred in ratepassword: {e}", exc_info=True)
            await send_and_delete(ctx, content="`An error occurred while checking password strength. Please try again later.`", delay=self.delete_errors_delay, delete_type='error')

    def custom_password_strength(self, password: str) -> int:
        length = len(password)
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()-_=+[]{}|;:,.<>?/~`' for c in password)

        score = 0
        if length >= 12:
            score += 1
        if has_upper and has_lower:
            score += 1
        if has_digit:
            score += 1
        if has_special:
            score += 1

        if any(password.lower().count(seq) >= 3 for seq in '0123456789'):
            score -= 1
        if any(seq in password.lower() for seq in ['123', 'abc', 'password', '1234', 'qwerty']):
            score -= 1

        return max(min(score, 4), 0)

    def filter_output(self, output: str) -> str:
        lines = output.splitlines()
        filtered_lines = [line for line in lines if line.startswith('[+]')]
        return '\n'.join(filtered_lines)

    @commands.command(name='hibp', help="Check if an email has been involved in data breaches. Usage: ..hibp <email>")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def hibp(self, ctx: commands.Context, email: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}") as response:
                    if response.status == 200:
                        data = await response.json()
                        breaches = [breach['Name'] for breach in data]
                        description = f"{email} has been involved in the following breaches:\n" + "\n".join(breaches)
                    else:
                        description = f"{email} has not been involved in any known data breaches."

            embed = create_embed(title="Have i Been Pwned",
                                  description=description,
                                  color_key='primary',
                                  config=self.bot.config
                                  )
            await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)
            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

        except Exception as e:
            logger.error(f"An unexpected error occurred in hibp: {e}", exc_info=True)
            await send_and_delete(ctx, content="`An error occurred while checking for data breaches. Please try again later.`", delay=self.delete_errors_delay, delete_type='error')

    @commands.command(name='privacytips', help="Provide privacy tips and best practices.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def privacy_tips(self, ctx: commands.Context):
        try:
            if not self.tips:
                await send_and_delete(ctx, content="`No privacy tips available.`", delay=self.delete_response_delay)
                return

            random_tip = random.choice(self.tips)

            embed = create_embed(title="PSA From PortLords",
                                  description=f"```{random_tip}```",
                                  color_key='primary',
                                  config=self.bot.config
                                  )
            await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)

            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

        except Exception as e:
            logger.error(f"An unexpected error occurred in privacy_tips: {e}", exc_info=True)
            await send_and_delete(ctx, content="`An error occurred while fetching privacy tips. Please try again later.`", delay=self.delete_errors_delay, delete_type='error')

    @tasks.loop(hours=12)
    async def send_security_tip(self):
        try:
            if not self.bot.config['features']['security_tips']:
                return
            channel = self.bot.get_channel(int(self.bot.config['identifiers']['security_channel_id']))
            if channel:
                if self.tips:
                    random_tip = random.choice(self.tips)
                    embed = create_embed(title="A PortLords PSA",
                                          description=f"```{random_tip}```",
                                          color_key='primary',
                                          config=self.bot.config
                                          )
                    sent_message = await channel.send(embed=embed)
                    if self.bot.config['settings']['delete_responses']:
                        await asyncio.sleep(self.bot.config['settings']['delete_response_delay'])
                        await sent_message.delete()
                else:
                    logger.error("No tips found in tips.json. Skipping tip.")
        except Exception as e:
            logger.error(f"Error sending security tip: {e}", exc_info=True)

    @commands.command(name='crack', help="Attempt to crack a hash using Hashcat. Usage: ..crack <hash> <hash_type>")
    @commands.is_owner()
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def crack_hash(self, ctx: commands.Context, hash: str, hash_type: str = "sha1"):
        try:
            if not hash:
                await send_and_delete(ctx, content="`Error: Please provide a hash to crack.`",
                                      delay=self.delete_errors_delay, delete_type='error')
                return

            if hash_type not in ["md5", "sha1", "sha256", "sha512"]:
                await send_and_delete(ctx, content="`Error: Invalid hash type. Supported types: md5, sha1, sha256, sha512`",
                                      delay=self.delete_errors_delay, delete_type='error')
                return

            wordlist_path = self.generate_wordlist(ctx)

            hashcat_command = [
                "hashcat", "-m", f"{self.get_hashcat_mode(hash_type)}", "-a", "0",
                "-w", "3", "-o", "results.txt",
                wordlist_path, hash
            ]

            async with ctx.typing():
                process = await asyncio.create_subprocess_exec(
                    *hashcat_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

            if process.returncode == 0:
                results_file = os.path.join(os.getcwd(), "results.txt")
                if os.path.exists(results_file):
                    with open(results_file, 'r') as f:
                        results = f.read().strip()
                    await send_and_delete(ctx, content=f"`Results for hash '{hash}':`\n```\n{results}\n```",
                                          delay=self.delete_response_delay)
                    os.remove(results_file)
                else:
                    await send_and_delete(ctx, content=f"`No matching passwords found for hash '{hash}'.`",
                                          delay=self.delete_response_delay)
            else:
                error_output = stderr.decode("utf-8").strip()
                await send_and_delete(ctx, content=f"`Hash cracking failed: {error_output}`",
                                      delay=self.delete_errors_delay, delete_type='error')

            os.remove(wordlist_path)

        except Exception as e:
            logger.error(f"An error occurred while cracking the hash: {e}", exc_info=True)
            await send_and_delete(ctx, content="`An error occurred while cracking the hash. Please try again later.`",
                                  delay=self.delete_errors_delay, delete_type='error')

    def get_hashcat_mode(self, hash_type: str) -> str:
        hashcat_modes = {
            "md5": "0",
            "sha1": "1000",
            "sha256": "1400",
            "sha512": "1700"
        }
        return hashcat_modes.get(hash_type, "1000")

    def generate_wordlist(self, ctx) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            wordlist = [''.join(random.choice(string.ascii_lowercase) for i in range(random.randint(6, 10)))
                       for _ in range(100)]
            temp_file.write('\n'.join(wordlist).encode('utf-8'))
            temp_file_path = temp_file.name
        return temp_file_path

def setup(bot: commands.Bot):
    bot.add_cog(Privacy(bot))
