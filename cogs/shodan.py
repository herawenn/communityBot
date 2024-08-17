import asyncio
import logging
import shodan
import discord
from discord.ext import commands, tasks
import math

logger = logging.getLogger(__name__)

class Shodan(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.shodan_api = shodan.Shodan(self.bot.config['apis']['shodan']['api_key'])
        self.delete_commands: bool = self.bot.config['settings']['delete_commands']
        self.delete_command_delay: int = self.bot.config['settings']['delete_command_delay']
        self.delete_responses: bool = self.bot.config['settings']['delete_responses']
        self.delete_response_delay: int = self.bot.config['settings']['delete_response_delay']

    @commands.command(name="shodanhelp", help="Displays help for the Shodan commands.")
    async def shodan_help(self, ctx: commands.Context) -> None:
        embed = discord.Embed(title="Shodan Command Help", description="", color=int(self.bot.config['embeds']['embed_colors']['primary'], 16))
        embed.add_field(name="`shodanhost <ip>`", value="`Get detailed information about a specific host.`", inline=False)
        embed.add_field(name="`shodansearch <query>`", value="`Search Shodan for specific terms.`", inline=False)
        embed.add_field(name="`shodanscan <ip>`", value="`Scan a specific host using Shodan.`", inline=False)
        embed.add_field(name="`shodanscanstatus <scan_id>`", value="`Check the status of a Shodan scan.`", inline=False)
        embed.add_field(name="`shodanscanresults <scan_id>`", value="`Get the results of a Shodan scan.`", inline=False)
        embed.set_image(url="https://i.imgur.com/MfPGDFu.png")

#       embed.add_field(name="\u200b", value="\u200b", inline=False)  # Empty field

        embed.add_field(name="", value="**`                     Our Top Picks:                     `**", inline=False)
        embed.add_field(name=":video_game: `Minecraft Servers`", value="`Search for Minecraft servers.`", inline=False)
        embed.add_field(name=":camera: `IP Cameras`", value="`Search for IP cameras.`", inline=False)
        embed.add_field(name=":computer: `RDP Devices`", value="`Search for RDP enabled devices.`", inline=False)

        help_message = await ctx.send(embed=embed)

        await help_message.add_reaction("🎮")  # Minecraft Servers
        await help_message.add_reaction("📸")  # IP Cameras
        await help_message.add_reaction("💻")  # RDP Devices

        if self.delete_responses:
            await asyncio.sleep(self.delete_response_delay)
            await help_message.delete()

        if self.delete_commands:
            await ctx.message.delete()

    @commands.command(name="shodanhost", help="Get information about a specific host.")
    async def shodan_host(self, ctx: commands.Context, ip: str) -> None:
        try:
            host = self.shodan_api.host(ip)
            embed = discord.Embed(
                title=f"Shodan Host Information for {ip}",
                description=f"**IP:** {host['ip_str']}\n**Organization:** {host['org']}\n**OS:** {host['os']}\n**Ports:** {', '.join(map(str, host['ports']))}",
                color=int(self.bot.config['embeds']['embed_colors']['primary'], 16)
            )
            embed.set_footer(text=self.bot.config['embeds']['embed_footer'])

            # Add vulnerabilities if available
            if 'vulns' in host and host['vulns']:
                vulns = ', '.join(host['vulns'])
                embed.add_field(name=":warning: Vulnerabilities", value=vulns, inline=False)

            # Add open ports information
            if 'data' in host:
                for item in host['data']:
                    port = item['port']
                    service = item.get('product', 'Unknown')
                    version = item.get('version', 'Unknown')
                    embed.add_field(name=f":computer: Port {port}", value=f"**Service:** {service}\n**Version:** {version}", inline=False)

            message = await ctx.send(embed=embed)

            if self.delete_responses:
                await asyncio.sleep(self.delete_response_delay)
                await message.delete()

            if self.delete_commands:
                await ctx.message.delete()

        except shodan.APIError as e:
            logger.error(f"Shodan API error: {e}")
            await ctx.send(f"An error occurred while fetching host information: {e}")

    def generate_embeds(self, results, query, page_size=5):
        embeds = []
        total_results = results['total']
        pages = math.ceil(total_results / page_size)

        for page in range(pages):
            embed = discord.Embed(
                title=f"Shodan Search Results for '{query}' (Page {page + 1}/{pages})",
                description=f"**Total Results:** {total_results}",
                color=int(self.bot.config['embeds']['embed_colors']['primary'], 16)
            )
            start_index = page * page_size
            end_index = start_index + page_size
            for match in results['matches'][start_index:end_index]:
                embed.add_field(
                    name=f"IP: {match['ip_str']}",
                    value=f"**Port:** {match['port']}\n**Data:** {match['data']}",
                    inline=False
                )
            embed.set_footer(text=self.bot.config['embeds']['embed_footer'])
            embeds.append(embed)

        return embeds

    @commands.command(name="shodansearch", help="Search Shodan for specific terms.")
    async def shodan_search(self, ctx: commands.Context, *, query: str) -> None:
        try:
            results = self.shodan_api.search(query)
            embeds = self.generate_embeds(results, query)

            if not embeds:
                await ctx.send("No results found.")
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

            if self.delete_responses:
                await asyncio.sleep(self.delete_response_delay)
                await message.delete()

            if self.delete_commands:
                await ctx.message.delete()

        except shodan.APIError as e:
            logger.error(f"Shodan API error: {e}")
            await ctx.send(f"An error occurred while searching Shodan: {e}")

    @commands.command(name="shodanscan", help="Scan a specific host using Shodan.")
    async def shodan_scan(self, ctx: commands.Context, ip: str) -> None:
        try:
            scan = self.shodan_api.scan(ip)
            embed = discord.Embed(
                title=f"Shodan Scan Results for {ip}",
                description=f"**Scan ID:** {scan['id']}",
                color=int(self.bot.config['embeds']['embed_colors']['primary'], 16)
            )
            embed.set_footer(text=self.bot.config['embeds']['embed_footer'])

            message = await ctx.send(embed=embed)

            if self.delete_responses:
                await asyncio.sleep(self.delete_response_delay)
                await message.delete()

            if self.delete_commands:
                await ctx.message.delete()

        except shodan.APIError as e:
            logger.error(f"Shodan API error: {e}")
            await ctx.send(f"An error occurred while scanning the host: {e}")

    @commands.command(name="shodanscanstatus", help="Check the status of a Shodan scan.")
    async def shodan_scan_status(self, ctx: commands.Context, scan_id: str) -> None:
        try:
            scan_status = self.shodan_api.scan_status(scan_id)
            embed = discord.Embed(
                title=f"Shodan Scan Status for ID {scan_id}",
                description=f"**Status:** {scan_status['status']}",
                color=int(self.bot.config['embeds']['embed_colors']['primary'], 16)
            )
            embed.set_footer(text=self.bot.config['embeds']['embed_footer'])

            message = await ctx.send(embed=embed)

            if self.delete_responses:
                await asyncio.sleep(self.delete_response_delay)
                await message.delete()

            if self.delete_commands:
                await ctx.message.delete()

        except shodan.APIError as e:
            logger.error(f"Shodan API error: {e}")
            await ctx.send(f"An error occurred while checking the scan status: {e}")

    @commands.command(name="shodanscanresults", help="Get the results of a Shodan scan.")
    async def shodan_scan_results(self, ctx: commands.Context, scan_id: str) -> None:
        try:
            scan_results = self.shodan_api.scan_results(scan_id)
            embed = discord.Embed(
                title=f"Shodan Scan Results for ID {scan_id}",
                description=f"**Results:** {scan_results}",
                color=int(self.bot.config['embeds']['embed_colors']['primary'], 16)
            )
            embed.set_footer(text=self.bot.config['embeds']['embed_footer'])

            message = await ctx.send(embed=embed)

            if self.delete_responses:
                await asyncio.sleep(self.delete_response_delay)
                await message.delete()

            if self.delete_commands:
                await ctx.message.delete()

        except shodan.APIError as e:
            logger.error(f"Shodan API error: {e}")
            await ctx.send(f"An error occurred while retrieving the scan results: {e}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return

        if reaction.message.author.id != self.bot.user.id:
            return

        if reaction.emoji == "🎮":
            await self.shodan_search(reaction.message.channel, query="minecraft")
        elif reaction.emoji == "📸":
            await self.shodan_search(reaction.message.channel, query="webcamxp")
        elif reaction.emoji == "💻":
            await self.shodan_search(reaction.message.channel, query="port:3389")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Shodan(bot))

