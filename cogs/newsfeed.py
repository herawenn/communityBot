import discord
import feedparser
import asyncio
import logging
import aiohttp
import json
import os
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from helpers import create_embed # type:ignore

logger = logging.getLogger(__name__)

class NewsFeed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.news_channel_id = int(self.config['identifiers']['news_channel_id'])
        self.feeds = [
            "https://www.bleepingcomputer.com/feed/",
            "https://feeds.feedburner.com/TheHackersNews",
            "https://www.darkreading.com/rss.xml"
        ]
        self.posted_entries_file = "files/json/posted_entries.json"
        self.posted_entries = self.load_posted_entries()
        if self.bot.config['features']['newsfeed']:
            self.post_news.start()

    def load_posted_entries(self):
        try:
            with open(self.posted_entries_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            with open(self.posted_entries_file, 'w') as f:
                json.dump({}, f)
            return {}

    def save_posted_entries(self):
        with open(self.posted_entries_file, 'w') as f:
            json.dump(self.posted_entries, f)

    @tasks.loop(minutes=60)
    async def post_news(self):
        try:
            if not self.bot.config['features']['newsfeed']:
                return
            channel = self.bot.get_channel(self.news_channel_id)
            if not channel:
                logger.error("Invalid news channel ID in config.json")
                return

            async with aiohttp.ClientSession() as session:
                for feed_url in self.feeds:
                    try:
                        async with session.get(feed_url) as response:
                            if response.status == 200:
                                feed_content = await response.text()
                                feed = feedparser.parse(feed_content)

                                entry = feed.entries[0]
                                entry_id = entry.id

                                if entry_id not in self.posted_entries.get(feed_url, []):
                                    self.posted_entries.setdefault(feed_url, []).append(entry_id)
                                    self.save_posted_entries()

                                    image_url = await self.get_article_image(entry.guid)

                                    embed = create_embed(title=entry.title,
                                                          description=entry.summary,
                                                          color_key='primary',
                                                          config=self.bot.config
                                                          )
                                    embed.set_author(name=feed.feed.title)
                                    embed.url = entry.link
                                    if image_url:
                                        embed.set_image(url=image_url)
                                    await channel.send(embed=embed)

                            else:
                                logger.error(f"Error fetching feed {feed_url}: Status code {response.status}")

                    except Exception as e:
                        logger.error(f"Error parsing feed {feed_url}: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error posting news: {e}", exc_info=True)

    @post_news.before_loop
    async def before_post_news(self):
        await self.bot.wait_until_ready()

    async def get_article_image(self, article_url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(article_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        image_tag = soup.find('meta', property='og:image')
                        if image_tag:
                            return image_tag.get('content')

                    else:
                        logger.error(f"Error fetching article page: {article_url}")
        except Exception as e:
            logger.error(f"Error scraping article page: {article_url} - {e}")
        return None

def setup(bot: commands.Bot):
    bot.add_cog(NewsFeed(bot))
