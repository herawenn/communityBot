import asyncio
import logging
import shodan
import aiohttp
import discord
from discord.ext import commands
import math
import os
import re
from helpers import send_and_delete, create_embed, is_valid_ip_address  # type: ignore
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CENSYS_API_ID = os.getenv('CENSYS_API_ID')
CENSYS_API_SECRET = os.getenv('CENSYS_API_SECRET')
CENSYS_GPT_API_KEY = os.getenv('CENSYS_GPT_API_KEY')
SHODAN_API_KEY = os.getenv('SHODAN_API_KEY')

class Shodan(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.config = bot.config
        self.shodan_api = shodan.Shodan(os.getenv('SHODAN_API_KEY'))
        self.delete_commands = self.bot.config['settings']['delete_commands']
        self.delete_command_delay = self.bot.config['settings']['delete_command_delay']
        self.delete_responses = self.bot.config['settings']['delete_responses']
        self.delete_response_delay = self.bot.config['settings']['delete_response_delay']
        self.delete_errors = self.bot.config['settings']['delete_errors']
        self.delete_errors_delay = self.bot.config['settings']['delete_errors_delay']
        self.db = self.bot.get_cog('Database')

    def validate_ip_address(self, ip: str) -> bool:
        return is_valid_ip_address(ip)

    @commands.command(name="host", help="Get information about a specific host from Shodan. Usage: ..host <IP address>")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def shodan_host(self, ctx: commands.Context, ip: str) -> None:
        try:
            if not self.validate_ip_address(ip):
                await send_and_delete(ctx, content="`Invalid IP address.` 😕", delay=self.delete_errors_delay,
                                      delete_type='error')
                return

            host = self.shodan_api.host(ip)

            fields = [
                ("IP 🌐", host['ip_str'], False),
                ("Organization 🏢", host.get('org', 'N/A'), False),
                ("OS 💻", host.get('os', 'N/A'), False),
                ("Ports 🔢", ', '.join(map(str, host['ports'])), False)
            ]

            if 'country_name' in host:
                fields.append(("Country 🌍", host['country_name'], False))
            if 'isp' in host:
                fields.append(("ISP 📡", host['isp'], False))
            if 'vulns' in host and host['vulns']:
                vulns = ', '.join(host['vulns'])
                fields.append(("Vulnerabilities 🦹‍♀️", f"`{vulns}`", False))

            if 'data' in host:
                for item in host['data']:
                    port = item['port']
                    service = item.get('product', 'Unknown')
                    version = item.get('version', 'Unknown')
                    fields.append((f"Port {port} 🔢",
                                  f"**Service:** `{service}` 🔍 **Version:** `{version}` 💻", False))

            embeds = self.create_paginated_embeds(fields, f"Shodan Host Info for {ip} 🌐", " ")

            if not embeds:
                await send_and_delete(ctx, content="`No results found.` 😕", delay=self.delete_errors_delay,
                                      delete_type='error')
                return

            current_page = 0
            message = await ctx.send(embed=embeds[current_page])
            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

            if len(embeds) > 1:
                await message.add_reaction("◀️")
                await message.add_reaction("➡️")

            def check(reaction: discord.Reaction, user: discord.User) -> bool:
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
            await send_and_delete(ctx, content=f"`Shodan API Error: {e}` 💥", delay=self.delete_errors_delay,
                                  delete_type='error')
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await send_and_delete(ctx, content="`Failed to fetch host info. Please try again.` 💥",
                                  delay=self.delete_errors_delay, delete_type='error')

    @shodan_host.error
    async def shodan_host_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(ctx, content=f"Whoa, slow down! Try again in {retry_after:.2f} seconds.` ⏳",
                                  delay=self.bot.config['settings']['delete_errors_delay'],
                                  delete_type='error')
        else:
            logger.error(f"An error occurred: {error}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again.` 💥",
                                  delay=self.bot.config['settings']['delete_errors_delay'],
                                  delete_type='error')


    def create_paginated_embeds(self, fields: list, title: str, description: str, page_size: int = 5) -> list:
        embeds = []
        total_pages = math.ceil(len(fields) / page_size)
        for page in range(total_pages):
            embed = create_embed(
                title=title,
                description=description,
                color_key='primary',
                config=self.bot.config
            )
            for i in range(page * page_size, min((page + 1) * page_size, len(fields))):
                embed.add_field(name=fields[i][0], value=fields[i][1], inline=fields[i][2])
            embeds.append(embed)
        return embeds

    async def search_censys(self, query: str) -> list:
        url = "https://censys.io/api"
        headers = {
            "Authorization": f"Basic {CENSYS_API_ID}:{CENSYS_API_SECRET}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        }

        data = {
            "query": query,
            "page": 1,
            "fields": ["ip", "protocols", "location.country", "autonomous_system.name", "services"]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    devices = result['results']
                    return devices
                else:
                    logger.error(f"Error searching Censys: {response.status} - {await response.text()}")
                    return []

    def create_device_embed(self, device: dict) -> discord.Embed:
        ip = device.get("ip", "N/A")
        country = device.get("location", {}).get("country", "N/A")
        asn = device.get("autonomous_system", {}).get("name", "N/A")
        protocols = device.get("protocols", [])
        services_info = []
        for service in device.get("services", []):
            service_name = service.get("service_name", "N/A")
            port = service.get("port", "N/A")
            banner = service.get("banner", "N/A")
            services_info.append(f"**Service:** `{service_name}`\n**Port:** `{port}`\n**Banner:** ```\n{banner}\n```")

        services_str = "\n\n".join(services_info)

        embed = create_embed(title=f"Censys Device Info - {ip}",
                              description="",
                              color_key='primary',
                              config=self.bot.config
                              )
        embed.add_field(name="IP", value=f"`{ip}`", inline=True)
        embed.add_field(name="Country", value=f"`{country}`", inline=True)
        embed.add_field(name="ASN", value=f"`{asn}`", inline=True)
        embed.add_field(name="Protocols", value=f"`{' '.join(protocols)}`", inline=False)

        split_descriptions = []
        current_description = ""
        for line in services_str.splitlines():
            if len(current_description) + len(line) + 1 > 1024:
                split_descriptions.append(current_description)
                current_description = line
            else:
                current_description += "\n" + line if current_description else line
        if current_description:
            split_descriptions.append(current_description)

        for i, description in enumerate(split_descriptions):
            embed.add_field(name="Services" if i == 0 else " ", value=description, inline=False)

        return embed

    @commands.command(name="censys", help="Search Censys using preset queries.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def censys(self, ctx: commands.Context):
        try:
            preset_reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
            preset_queries = [
                'services.service_name: MINECRAFT',
                'labels: webcam',
                'protocols: "modbus" or protocols: "s7"',
                'labels: "iot" and services.service_name: "HTTP" and http.body: "camera"',
                'protocols: "23/telnet"'
            ]

            embed = create_embed(title="Censys Preset Searches",
                                  description="Choose a preset search:\n\n"
                                              "1️⃣ `Minecraft Servers`\n"
                                              "2️⃣ `Webcams`\n"
                                              "3️⃣ `Industrial Control Systems`\n"
                                              "4️⃣ `IoT Devices with Cameras`\n"
                                              "5️⃣ `Devices with Telnet`",
                                  color_key='primary',
                                  config=self.bot.config
                              )
            message = await ctx.send(embed=embed)

            for reaction in preset_reactions:
                await message.add_reaction(reaction)

            def reaction_check(reaction: discord.Reaction, user: discord.User) -> bool:
                return user == ctx.author and str(reaction.emoji) in preset_reactions

            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=reaction_check)
                query = preset_queries[preset_reactions.index(str(reaction.emoji))]
                await message.delete()

                devices = await self.search_censys(query)
                if devices:
                    pages = self.paginate_results(devices, per_page=3)
                    await self.send_paginated_results(ctx, pages)
                else:
                    await send_and_delete(ctx, content="No devices found for the selected query.",
                                          delay=self.delete_response_delay)
            except asyncio.TimeoutError:
                await send_and_delete(ctx, content="Input timed out.", delay=self.delete_response_delay)

            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

        except Exception as e:
            logger.error(f"Error in censys command: {e}", exc_info=True)
            await send_and_delete(ctx, content=f"Error processing Censys search: {e}",
                                  delay=self.delete_errors_delay, delete_type='error')

    def paginate_results(self, devices: list, per_page: int) -> list:
        pages = []
        for i in range(0, len(devices), per_page):
            page = devices[i:i + per_page]
            pages.append(page)
        return pages

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Shodan(bot))
