import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from helpers import send_and_delete, create_embed, is_valid_ip_address  # type: ignore
import json
import shutil
import asyncio
import random
import subprocess
import logging

load_dotenv()

logger = logging.getLogger(__name__)

def load_config(config_path: str) -> dict:
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to load configuration file: {e}")
        return None
    except FileNotFoundError as e:
        logging.error(f"Configuration file not found: {e}")
        return None

class Crawler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.delete_responses = self.bot.config['settings']['delete_responses']
        self.delete_response_delay = self.bot.config['settings']['delete_response_delay']
        self.delete_errors = self.bot.config['settings']['delete_errors']
        self.delete_errors_delay = self.bot.config['settings']['delete_errors_delay']
        self.devices_file = "files/json/devices.json"
        self.crawler_channel_id = self.bot.config['identifiers']['crawler_channel_id']
        self.nmap_path = "/usr/bin/nmap"
        self.ip_ranges = {
            "Range1": "141.98.115.0/24",
            "Range2": "141.98.116.0/24",
            "Range3": "141.98.117.0/24",
            "Range4": "141.98.118.0/24"
            # Add more ranges as needed
        }
        self.posted_devices = []
        self.crawl_tasks = {}

    def load_devices(self) -> list:
        try:
            with open(self.devices_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Devices file not found: {self.devices_file}")
            return []
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON format in devices file: {self.devices_file}")
            return []

    @commands.command(name="crawl", help="Crawls the internet updates. Usage: ..crawl <range_name>")
    @commands.is_owner()
    async def crawl(self, ctx: commands.Context, range_name: str = None):
        try:
            if range_name is None:
                for range_name in self.ip_ranges:
                    await self.start_crawl_task(ctx, range_name)
            elif range_name in self.ip_ranges:
                await self.start_crawl_task(ctx, range_name)
            else:
                await send_and_delete(ctx, content=f"`Error: Range '{range_name}' not found in configuration.`",
                                      delay=self.delete_errors_delay, delete_type='error')
        except Exception as e:
            logger.error(f"Error running Nmap scan: {e}", exc_info=True)
            await send_and_delete(ctx, content=f"`Error running Nmap scan: {e}`", delay=self.delete_errors_delay,
                                  delete_type='error')

    async def start_crawl_task(self, ctx, range_name):
        if range_name not in self.crawl_tasks:
            ip_range = self.ip_ranges[range_name]
            self.crawl_tasks[range_name] = self.bot.loop.create_task(self.crawl_range(ctx, ip_range, range_name))
            await send_and_delete(ctx, content=f"`Started crawling range '{range_name}' ({ip_range}).`",
                                  delay=self.delete_response_delay)
        else:
            await send_and_delete(ctx, content=f"`Range '{range_name}' is already being crawled.`",
                                  delay=self.delete_response_delay)

    @commands.command(name="postdevice", help="Posts a random device from devices.json to the channel")
    @commands.is_owner()
    async def post_device(self, ctx: commands.Context):
        devices = self.load_devices()
        if not devices:
            await send_and_delete(ctx, content="`No devices found in devices.json.`", delay=self.delete_response_delay)
            return

        device = random.choice(devices)
        embed = self.create_device_embed(device)
        channel = self.bot.get_channel(self.crawler_channel_id)

        if channel:
            await send_and_delete(channel, content="`Error?`", embed=embed, delay=self.delete_response_delay)
        else:
            logger.error(f"Channel with ID {self.crawler_channel_id} not found.")

    async def crawl_range(self, ctx: commands.Context, ip_range: str, range_name: str):
        try:
            for port in [21, 22, 23, 53, 80, 110, 143, 443, 993, 995, 1194, 2082, 3306, 8222]:
                await self.update_devices_from_nmap(ctx, ip_range, port, range_name)
        except Exception as e:
            logger.error(f"Error crawling range '{range_name}': {e}", exc_info=True)
        finally:
            if range_name in self.crawl_tasks:
                del self.crawl_tasks[range_name]

    async def update_devices_from_nmap(self, ctx: commands.Context, ip_range: str, port: int, range_name: str):
        try:
            command = [self.nmap_path, '-p', str(port), ip_range, '-oG', '-']
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                nmap_output = stdout.decode("utf-8").strip()
                new_devices = self.parse_nmap_output(nmap_output, port)
                self.append_devices_to_json(new_devices)
                if ctx:
                    await send_and_delete(ctx, content=f"`Nmap scan for range '{range_name}' completed on port {port}.`",
                                          delay=self.delete_response_delay)
            else:
                error_output = stderr.decode("utf-8").strip()
                logger.error(f"Nmap failed for range '{range_name}': {error_output}")
                if ctx:
                    await send_and_delete(ctx,
                                          content=f"`Nmap scan for range '{range_name}' failed on port {port}: {error_output}`",
                                          delay=self.delete_errors_delay, delete_type='error')

        except Exception as e:
            logger.error(f"Error running Nmap scan for range '{range_name}': {e}", exc_info=True)
            if ctx:  # Check if ctx is not None before sending a message
                await send_and_delete(ctx, content=f"`Error running Nmap scan for range '{range_name}': {e}`",
                                      delay=self.delete_errors_delay, delete_type='error')

    def parse_nmap_output(self, output, port):
        devices_with_port = []
        lines = output.splitlines()
        for line in lines:
            if f"Ports: {port}/open" in line:
                parts = line.split()
                ip = parts[1]
                hostname = parts[2] if len(parts) > 2 else None
                os = parts[3] if len(parts) > 3 else None
                devices_with_port.append({"ip": ip, "port": port, "hostname": hostname, "os": os})
        return devices_with_port

    def append_devices_to_json(self, new_devices):
        try:
            existing_devices = self.load_devices()
            existing_devices.extend(new_devices)
            with open(self.devices_file, 'w') as f:
                json.dump(existing_devices, f, indent=4)
            logger.info(f"Devices appended to {self.devices_file}")
        except Exception as e:
            logger.error(f"Error appending devices to JSON: {e}", exc_info=True)

    def create_device_embed(self, device: dict) -> discord.Embed:
        fields = [
            ("🌐 Host", f"`{device.get('ip', 'N/A')}`", True),
            ("🚪 Port", f"`{device.get('port', 'N/A')}`", True),
            ("💻 Hostname", f"`{device.get('hostname', 'N/A')}`", True),
            ("💻 OS", f"`{device.get('os', 'N/A')}`", True),
            ("📱 MAC Address", f"`{device.get('mac', 'N/A')}`", True),
            ("🏢 Vendor", f"`{device.get('vendor', 'N/A')}`", True),
        ]
        embed = create_embed(title="PortLords Crawler 🕷️",
                              description="",
                              color_key='primary',
                              fields=fields,
                              config=self.bot.config
                              )
        return embed

    @tasks.loop(minutes=1)
    async def device_poster_task(self):
        try:
            if not self.bot.config['features']['crawler']:
                return

            devices = self.load_devices()
            if not devices:
                logger.warning("No devices found in devices.json. Skipping device posting.")
                return

            device = random.choice(devices)

            while device['ip'] in self.posted_devices:
                device = random.choice(devices)

            self.posted_devices.append(device['ip'])
            embed = self.create_device_embed(device)

            channel = self.bot.get_channel(self.crawler_channel_id)
            if channel:
                await channel.send(embed=embed)
            else:
                logger.error(f"Channel with ID {self.crawler_channel_id} not found.")

        except Exception as e:
            logger.error(f"An error occurred in device_poster_task: {e}", exc_info=True)

    @tasks.loop(hours=1)  # Adjust
    async def start_crawling(self):
        if not self.bot.config['features']['crawler']:
            return
        try:
            for range_name in self.ip_ranges:
                await self.crawl_range(None, self.ip_ranges[range_name], range_name)
        except Exception as e:
            logger.error(f"Error in start_crawling: {e}", exc_info=True)

    @start_crawling.before_loop
    async def before_start_crawling(self):
        await self.bot.wait_until_ready()

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Crawler(bot))
