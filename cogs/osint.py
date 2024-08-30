import discord
from discord.ext import commands
import aiohttp
import os
import math
import json
import logging
import asyncio
from helpers import send_and_delete

logger = logging.getLogger(__name__)

class Osint(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # Use 'bot' instead of 'client'
        self.config = self.load_config()
        self.dehashed_api_key = os.getenv('DEHASHED_API_KEY')
        self.results_limit = self.config['apis']['dehashed'].get('results_limit', 10)
        self.delete_commands = self.config['settings']['delete_commands']
        self.delete_command_delay = self.config['settings']['delete_command_delay']
        self.delete_responses = self.config['settings']['delete_responses']
        self.delete_response_delay = self.config['settings']['delete_response_delay']
        self.delete_errors = self.config['settings']['delete_errors']
        self.delete_errors_delay = self.config['settings']['delete_errors_delay']

    def load_config(self):
        try:
            with open('files/json/config.json', 'r') as f:
                config = json.load(f)
            return config
        except json.JSONDecodeError as e:
            logger.error(f"Failed to load configuration file: {e}")
            return None

    async def fetch_dehashed_data(self, query_type, query, page):
        url = f"https://api.dehashed.com/search?query={query_type}:'{query}'&size=100&page={page}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Basic {self.dehashed_api_key}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Failed to fetch data from API: {response.status} - {await response.text()}")
                    return None

    def split_message(self, text):
        chunks = []
        while len(text) > 0:
            if len(text) > 4000:
                split_index = text.rfind('\n', 0, 4000)
                if split_index == -1:
                    split_index = 4000
                chunks.append(text[:split_index])
                text = text[split_index:]
            else:
                chunks.append(text)
                text = ""
        return chunks

    def format_entry(self, entry):
        formatted_entry = []
        if entry.get('email'):
            formatted_entry.append(f"email: {entry['email']}")
        if entry.get('ip_address'):
            formatted_entry.append(f"ip: {entry['ip_address']}")
        if entry.get('username'):
            formatted_entry.append(f"username: {entry['username']}")
        if entry.get('password'):
            formatted_entry.append(f"password: {entry['password']}")
        if entry.get('hashed_password'):
            formatted_entry.append(f"hashed_password: {entry['hashed_password']}")
        if entry.get('name'):
            formatted_entry.append(f"name: {entry['name']}")
        if entry.get('vin'):
            formatted_entry.append(f"vin: {entry['vin']}")
        if entry.get('address'):
            formatted_entry.append(f"address: {entry['address']}")
        if entry.get('phone'):
            formatted_entry.append(f"phone: {entry['phone']}")
        if entry.get('database_name'):
            formatted_entry.append(f"database_name: {entry['database_name']}")

        return "\n".join(formatted_entry)

    @commands.command(name='search', help="Search Private dbs for OSINT data. Usage: ..search <query_type> <query>.  Example: ..search email example@example.com")
    @commands.cooldown(1, 300, commands.BucketType.user) # Rate Limit
    async def search(self, ctx, query_type: str, *, query: str):
        try:
            search_message = await ctx.send(f"`Searching Dehashed for {query_type}: {query}...`")

            data = await self.fetch_dehashed_data(query_type, query, 1)

            if data and data.get('entries'):
                total = data.get('total', 0)
                total_pages = math.ceil(total / 100)

                limited_entries = data.get("entries", [])[:self.results_limit]
                response_text = f"Search: {query}\nPage 1/{total_pages}\n\n"
                response_text += "\n".join([self.format_entry(part) for part in limited_entries])

                chunks = self.split_message(response_text)
                for chunk in chunks:
                    message = await ctx.send(f"```\n{chunk}\n```")

                if total_pages > 1:
                    await message.add_reaction("⬅️")
                    await message.add_reaction("➡️")

            else:
                await send_and_delete(ctx, "`No results found.`", delay=self.delete_response_delay)

        except Exception as e:
            logger.error(f"An error occurred in search: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred while searching. Please try again later.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        message = reaction.message
        if message.author != self.bot.user:
            return

        if "Search:" not in message.content:
            return

        search = message.content.split("Search: ")[1].split("\nPage")[0]
        page = int(message.content.split("\nPage")[1].split("/")[0])
        total_pages = int(message.content.split("\nPage")[1].split("/")[1])

        if reaction.emoji == "⬅️" and page > 1:
            new_page = page - 1
        elif reaction.emoji == "➡️" and page < total_pages:
            new_page = page + 1
        else:
            return

        query_type, query = search.split(": ", 1)
        data = await self.fetch_dehashed_data(query_type, query, new_page)

        if data and data.get('entries'):
            limited_entries = data.get("entries", [])[:self.results_limit]
            response_text = f"Search: {query}\nPage {new_page}/{total_pages}\n\n"
            response_text += "\n".join([self.format_entry(part) for part in limited_entries])

            chunks = self.split_message(response_text)
            for chunk in chunks:
                new_message = await message.channel.send(f"```\n{chunk}\n```")

            if total_pages > 1:
                await new_message.add_reaction("⬅️")
                await new_message.add_reaction("➡️")

            if self.delete_responses:
                await asyncio.sleep(self.delete_response_delay)
                await message.delete()
                await new_message.delete()

        else:
            no_results_message = await message.channel.send("`No results found.`")
            if self.delete_responses:
                await asyncio.sleep(self.delete_response_delay)
                await no_results_message.delete()
                await message.delete()

async def setup(bot):
    await bot.add_cog(Osint(bot))
