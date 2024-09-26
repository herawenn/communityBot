import discord
from discord.ext import commands
import aiohttp
import os
import math
import logging
from helpers import send_and_delete, create_embed # type:ignore

logger = logging.getLogger(__name__)

class Osint(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.dehashed_api_key = os.getenv('DEHASHED_API_KEY')
        self.results_limit = 5
        self.delete_commands = self.config['settings']['delete_commands']
        self.delete_command_delay = self.config['settings']['delete_command_delay']
        self.delete_responses = self.config['settings']['delete_responses']
        self.delete_response_delay = self.config['settings']['delete_response_delay']
        self.delete_errors = self.config['settings']['delete_errors']
        self.delete_errors_delay = self.config['settings']['delete_errors_delay']

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
            if len(text) > 1900:
                split_index = text.rfind('\n', 0, 1900)
                if split_index == -1:
                    split_index = 1900
                chunks.append(text[:split_index])
                text = text[split_index:]
            else:
                chunks.append(text)
                text = ""
        return chunks

    def format_entry(self, entry):
        formatted_entry = []
        for key, value in entry.items():
            formatted_entry.append(f"{key}: {value}")
        return "\n".join(formatted_entry)

    @commands.command(name='search', help="Search Private dbs for OSINT data. Usage: ..search <query_type> <query>.  Example: ..search email example@example.com")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def search(self, ctx, query_type: str, *, query: str):
        try:
            embed = create_embed(title="Open Source Intelligence",
                                  description=f"`Searching for {query_type}: {query}...`",
                                  color_key='primary',
                                  config=self.bot.config
                                  )
            await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)

            data = await self.fetch_dehashed_data(query_type, query, 1)

            if data and data.get('entries'):
                total = data.get('total', 0)
                total_pages = math.ceil(total / 100)

                limited_entries = data.get("entries", [])[:self.results_limit]
                response_text = f"Search: {query}\nPage 1/{total_pages}\n\n"
                response_text += "\n".join([self.format_entry(part) for part in limited_entries])

                chunks = self.split_message(response_text)
                for chunk in chunks:
                    embed = create_embed(title="Results",
                                          description=f"```\n{chunk}\n```",
                                          color_key='primary',
                                          config=self.bot.config
                                          )
                    await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)

                if total_pages > 1:
                    try:
                        await ctx.message.add_reaction("⬅️")
                        await ctx.message.add_reaction("➡️")
                    except discord.errors.NotFound:
                        await send_and_delete(ctx, content="The results message seems to have been deleted. Please try the search again.", delay=self.delete_errors_delay, delete_type='error')
            else:
                await send_and_delete(ctx, content="`No results found.`", delay=self.delete_response_delay)

            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

        except Exception as e:
            logger.error(f"An error occurred in search: {e}", exc_info=True)
            await send_and_delete(ctx, content="`An error occurred while searching. Please try again later.`", delay=self.delete_errors_delay, delete_type='error')

    @search.error
    async def search_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(ctx, content=f"`This command is on cooldown. Please try again in {retry_after:.2f} seconds.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again later.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
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

            await message.delete()

            for chunk in chunks:
                new_message = await message.channel.send(f"```\n{chunk}\n```")

            if total_pages > 1:
                await new_message.add_reaction("⬅️")
                await new_message.add_reaction("➡️")

            try:
                await message.add_reaction("⬅️")
                await message.add_reaction("➡️")

            except discord.errors.NotFound:
                await message.channel.send("The results message seems to have been deleted. Please try the search again.")
            else:
                await message.channel.send("`No results found.`")

def setup(bot):
    bot.add_cog(Osint(bot))
