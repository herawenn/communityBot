import asyncio
import logging
import shodan
import discord
from discord.ext import commands
import math
import os
import re
from helpers import send_and_delete

logger = logging.getLogger(__name__)

class Shodan(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.shodan_api = shodan.Shodan(os.getenv('SHODAN_API_KEY'))
        self.delete_commands: bool = self.bot.config['settings']['delete_commands']
        self.delete_command_delay: int = self.bot.config['settings']['delete_command_delay']
        self.delete_responses: bool = self.bot.config['settings']['delete_responses']
        self.delete_response_delay: int = self.bot.config['settings']['delete_response_delay']
        self.delete_errors: bool = self.bot.config['settings']['delete_errors']
        self.delete_errors_delay: int = self.bot.config['settings']['delete_errors_delay']
        self.shodan_channel_id = self.bot.config['identifiers']['shodan_channel_id']

    def validate_scan_id(self, scan_id):
        try:
            int(scan_id)
            return True
        except ValueError:
            return False

    def validate_ip_address(self, ip):
        regex = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        if re.match(regex, ip):
            return True
        else:
            return False

    @commands.command(name="shodanhelp", help="Displays help for the Shodan commands.")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def shodan_help(self, ctx: commands.Context) -> None:
        if ctx.channel.id != self.shodan_channel_id:
            await send_and_delete(ctx, "`This command can only be used in the designated Shodan channel.`", delay=self.delete_errors_delay, delete_type='error')
            return

        try:
            embed = discord.Embed(title="Shodan Command Help", description="", color=int(self.bot.config['embeds']['embed_colors']['primary'], 16))
            embed.add_field(name="`..shodanhost <ip>`", value="`Get detailed information about a specific host. Example: ..shodanhost 8.8.8.8`", inline=False)
            embed.add_field(name="`..shodansearch <query>`", value="`Search Shodan for specific terms. Example: ..shodansearch 'Apache server'`", inline=False)
            embed.add_field(name="`..shodanscan <ip>`", value="`Scan a specific host using Shodan. Note: Requires Shodan scan credits. Example: ..shodanscan 192.168.1.1`", inline=False)
            embed.add_field(name="`..shodanscanstatus <scan_id>`", value="`Check the status of a Shodan scan. Example: ..shodanscanstatus 7891234567890`", inline=False)
            embed.add_field(name="`..shodanscanresults <scan_id>`", value="`Get the results of a Shodan scan. Example: ..shodanscanresults 7891234567890`", inline=False)
            embed.set_image(url="https://i.imgur.com/MfPGDFu.png")
            embed.set_footer(text=self.bot.config['embeds']['embed_footer'])

            await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)

        except Exception as e:
            logger.error(f"An unexpected error occurred in shodan_help: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred while displaying the help message. Please try again later.`", delay=self.delete_errors_delay, delete_type='error')

    @commands.command(name="shodanhost", help="Get information about a specific host from Shodan. Usage: ..shodanhost <IP address>")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def shodan_host(self, ctx: commands.Context, ip: str) -> None:
        if ctx.channel.id != self.shodan_channel_id:
            await send_and_delete(ctx, "`This command can only be used in the designated Shodan channel.`", delay=self.delete_errors_delay, delete_type='error')
            return

        try:
            if not self.validate_ip_address(ip):
                await send_and_delete(ctx, "`Error: Invalid IP address format.`", delay=self.delete_errors_delay, delete_type='error')
                return

            host = self.shodan_api.host(ip)

            embed = discord.Embed(title=f"Shodan Host Information for {ip}", description=f"**IP:** {host['ip_str']}\n**Organization:** {host.get('org', 'N/A')}\n**OS:** {host.get('os', 'N/A')}\n**Ports:** {', '.join(map(str, host['ports']))}", color=int(self.bot.config['embeds']['embed_colors']['primary'], 16))
            embed.set_footer(text=self.bot.config['embeds']['embed_footer'])

            if 'country_name' in host:
                embed.add_field(name="Country", value=host['country_name'], inline=False)

            if 'isp' in host:
                embed.add_field(name="ISP", value=host['isp'], inline=False)

            if 'vulns' in host and host['vulns']:
                vulns = ', '.join(host['vulns'])
                embed.add_field(name="Vulnerabilities", value=f"`{vulns}`", inline=False)

            if 'data' in host:
                for item in host['data']:
                    port = item['port']
                    service = item.get('product', 'Unknown')
                    version = item.get('version', 'Unknown')
                    embed.add_field(name=f"Port {port}", value=f"**Service:** `{service}`\n**Version:** `{version}`", inline=False)

            await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)

        except shodan.APIError as e:
            logger.error(f"Shodan API error: {e}")
            await send_and_delete(ctx, f"`Shodan API Error: {e}`", delay=self.delete_errors_delay, delete_type='error')
        except Exception as e:
            logger.error(f"An unexpected error occurred in shodan_host: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred while fetching host information. Please try again later.`", delay=self.delete_errors_delay, delete_type='error')

    def generate_embeds(self, results, query, page_size=1):
        try:
            embeds = []
            total_results = results['total']
            pages = math.ceil(total_results / page_size)

            for page in range(pages):
                embed = discord.Embed(title=f"Shodan Search Results for '{query}' (Page {page + 1}/{pages})", description=f"**Total Results:** {total_results}", color=int(self.bot.config['embeds']['embed_colors']['primary'], 16))
                start_index = page * page_size
                end_index = start_index + page_size
                for match in results['matches'][start_index:end_index]:
                    data_str = match['data'].replace('\n', ' ')
                    embed.add_field(name=f"IP: {match['ip_str']}", value=f"**Port:** `{match['port']}`\n**Data:** `{data_str}`", inline=False)
                embed.set_footer(text=self.bot.config['embeds']['embed_footer'])
                embeds.append(embed)

            return embeds
        except Exception as e:
            logger.error(f"An error occurred while generating embeds: {e}", exc_info=True)
            return []

    @commands.command(name="shodansearch", help="Search Shodan for specific terms. Usage: ..shodansearch <search query>")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def shodan_search(self, ctx: commands.Context, *, query: str) -> None:
        if ctx.channel.id != self.shodan_channel_id:
            await send_and_delete(ctx, "`This command can only be used in the designated Shodan channel.`", delay=self.delete_errors_delay, delete_type='error')
            return

        try:
            results = self.shodan_api.search(query)

            embeds = self.generate_embeds(results, query)

            if not embeds:
                await send_and_delete(ctx, "`No results found for the given search query.`", delay=self.delete_errors_delay, delete_type='error')
                return

            current_page = 0
            message = await ctx.send(embed=embeds[current_page])

            if len(embeds) > 1:
                await message.add_reaction("◀️")
                await message.add_reaction("▶️")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]

            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                    if str(reaction.emoji) == "◀️" and current_page > 0:
                        current_page -= 1
                        await message.edit(embed=embeds[current_page])
                        await message.remove_reaction(reaction, user)

                    elif str(reaction.emoji) == "▶️" and current_page < len(embeds) - 1:
                        current_page += 1
                        await message.edit(embed=embeds[current_page])
                        await message.remove_reaction(reaction, user)

                except asyncio.TimeoutError:
                    break

        except shodan.APIError as e:
            logger.error(f"Shodan API error: {e}")
            await send_and_delete(ctx, f"`Shodan API Error: {e}`", delay=self.delete_errors_delay, delete_type='error')
        except Exception as e:
            logger.error(f"An unexpected error occurred in shodan_search: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred while searching Shodan. Please try again later.`", delay=self.delete_errors_delay, delete_type='error')

    @commands.command(name="shodanscan", help="Initiate a Shodan scan on a specific IP. Usage: ..shodanscan <IP address>")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def shodan_scan(self, ctx: commands.Context, ip: str) -> None:
        if ctx.channel.id != self.shodan_channel_id:
            await send_and_delete(ctx, "`This command can only be used in the designated Shodan channel.`", delay=self.delete_errors_delay, delete_type='error')
            return

        try:
            if not self.validate_ip_address(ip):
                await send_and_delete(ctx, "`Error: Invalid IP address format.`", delay=self.delete_errors_delay, delete_type='error')
                return

            scan = self.shodan_api.scan(ip)

            embed = discord.Embed(title=f"Shodan Scan Initiated for {ip}", description=f"**Scan ID:** `{scan['id']}`\n\nUse `..shodanscanstatus <scan_id>` to check the status of your scan.", color=int(self.bot.config['embeds']['embed_colors']['primary'], 16))
            embed.set_footer(text=self.bot.config['embeds']['embed_footer'])

            await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)

        except shodan.APIError as e:
            logger.error(f"Shodan API error: {e}")
            await send_and_delete(ctx, f"`Shodan API Error: {e}`", delay=self.delete_errors_delay, delete_type='error')
        except Exception as e:
            logger.error(f"An unexpected error occurred in shodan_scan: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred while initiating the Shodan scan. Please try again later.`", delay=self.delete_errors_delay, delete_type='error')

    @commands.command(name="shodanscanstatus", help="Check the status of a Shodan scan. Usage: ..shodanscanstatus <scan_id>")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def shodan_scan_status(self, ctx: commands.Context, scan_id: str) -> None:
        if ctx.channel.id != self.shodan_channel_id:
            await send_and_delete(ctx, "`This command can only be used in the designated Shodan channel.`", delay=self.delete_errors_delay, delete_type='error')
            return

        try:
            if not self.validate_scan_id(scan_id):
                await send_and_delete(ctx, "`Error: Invalid scan ID.`", delay=self.delete_errors_delay, delete_type='error')
                return
            scan_id = int(scan_id)

            scan = self.shodan_api.scan_status(scan_id)

            embed = discord.Embed(title=f"Shodan Scan Status for Scan ID: {scan_id}", description=f"**Status:** `{scan['status']}`", color=int(self.bot.config['embeds']['embed_colors']['primary'], 16))
            embed.set_footer(text=self.bot.config['embeds']['embed_footer'])

            await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)

        except shodan.APIError as e:
            logger.error(f"Shodan API error: {e}")
            await send_and_delete(ctx, f"`Shodan API Error: {e}`", delay=self.delete_errors_delay, delete_type='error')
        except Exception as e:
            logger.error(f"An unexpected error occurred in shodan_scan_status: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred while retrieving the scan status. Please try again later.`", delay=self.delete_errors_delay, delete_type='error')

    @commands.command(name="shodanscanresults", help="Get the results of a Shodan scan. Usage: ..shodanscanresults <scan_id>")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def shodan_scan_results(self, ctx: commands.Context, scan_id: str) -> None:
        if ctx.channel.id != self.shodan_channel_id:
            await send_and_delete(ctx, "`This command can only be used in the designated Shodan channel.`", delay=self.delete_errors_delay, delete_type='error')
            return

        try:
            if not self.validate_scan_id(scan_id):
                await send_and_delete(ctx, "`Error: Invalid scan ID.`", delay=self.delete_errors_delay, delete_type='error')
                return

            scan_id = int(scan_id)

            scan = self.shodan_api.scan_results(scan_id)

            if not scan['matches']:
                await send_and_delete(ctx, "`No results found for the given scan ID.`", delay=self.delete_response_delay)
                return

            embeds = self.generate_embeds(scan, f"Scan ID: {scan_id}")

            if not embeds:
                await send_and_delete(ctx, "`Error: An error occurred while generating the results.`", delay=self.delete_errors_delay, delete_type='error')
                return

            current_page = 0
            message = await ctx.send(embed=embeds[current_page])

            if len(embeds) > 1:
                await message.add_reaction("◀️")
                await message.add_reaction("▶️")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]

            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                    if str(reaction.emoji) == "◀️" and current_page > 0:
                        current_page -= 1
                        await message.edit(embed=embeds[current_page])
                        await message.remove_reaction(reaction, user)

                    elif str(reaction.emoji) == "▶️" and current_page < len(embeds) - 1:
                        current_page += 1
                        await message.edit(embed=embeds[current_page])
                        await message.remove_reaction(reaction, user)

                except asyncio.TimeoutError:
                    break

        except shodan.APIError as e:
            logger.error(f"Shodan API error: {e}")
            await send_and_delete(ctx, f"`Shodan API Error: {e}`", delay=self.delete_errors_delay, delete_type='error')
        except Exception as e:
            logger.error(f"An unexpected error occurred in shodan_scan_results: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred while retrieving the scan results. Please try again later.`", delay=self.delete_errors_delay, delete_type='error')

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Shodan(bot))
