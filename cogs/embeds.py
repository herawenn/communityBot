import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class Embeds(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_banner = self.bot.config['embeds']['embed_banner']
        self.embed_footer = self.bot.config['embeds']['embed_footer']
        self.embed_colors = self.bot.config['embeds']['embed_colors']
        self.delete_response_delay = self.bot.config['settings']['delete_response_delay']
        self.delete_responses = self.bot.config['settings']['delete_responses']

    async def send_and_delete(self, ctx, message):
        sent_message = await ctx.send(message)
        if self.delete_responses:
            await sent_message.delete(delay=self.delete_response_delay)

    @commands.command(name='obfuscate_embed')
    async def obfuscate_embed(self, ctx: commands.Context):
        obf_channel_id = int(self.bot.config['identifiers']['obf_channel_id'])
        logger.info(f"Command used in channel: {ctx.channel.id}, Obfuscation channel ID: {obf_channel_id}")

        if ctx.channel.id != obf_channel_id:
            await self.send_and_delete(ctx, "This command can only be used in the obfuscation channel.")
            return

        embed = discord.Embed(
            title="**Obfuscation Channel Information**",
            description="Welcome to the Obfuscation channel.",
            color=int(self.embed_colors['primary'], 16)
        )
        embed.add_field(name="Purpose", value="This channel is dedicated to obfuscating files and code.", inline=False)
        embed.add_field(name="Features", value="`Use the bot to obfuscate your files and code.`", inline=False)
        embed.add_field(name="Help Command", value="Use `!brutehelp` for more detailed information.", inline=False)
        embed.set_image(url=self.embed_banner)
        embed.set_footer(text=self.embed_footer)

        embed_message = await ctx.send(embed=embed)
        if self.delete_responses:
            await ctx.message.delete()
            await embed_message.delete(delay=self.delete_response_delay)

    @commands.command(name='exploit_embed')
    async def exploit_embed(self, ctx: commands.Context):
        exploit_channel_id = int(self.bot.config['identifiers']['exploit_channel_id'])
        logger.info(f"Command used in channel: {ctx.channel.id}, Exploit channel ID: {exploit_channel_id}")

        if ctx.channel.id != exploit_channel_id:
            await self.send_and_delete(ctx, "This command can only be used in the exploit channel.")
            return

        embed = discord.Embed(
            title="**Exploit Channel Information**",
            description="Welcome to the Exploit channel.",
            color=int(self.embed_colors['primary'], 16)
        )
        embed.add_field(name="Purpose", value="This channel is dedicated to browsing and downloading exploits from exploitDB.", inline=False)
        embed.add_field(name="Features", value="`Use the bot to search for exploits and vulnerabilities.`", inline=False)
        embed.add_field(name="Help Command", value="Use `!exploithelp` for more detailed information.", inline=False)
        embed.set_image(url=self.embed_banner)
        embed.set_footer(text=self.embed_footer)

        embed_message = await ctx.send(embed=embed)
        if self.delete_responses:
            await ctx.message.delete()
            await embed_message.delete(delay=self.delete_response_delay)

    @commands.command(name='ai_embed')
    async def ai_embed(self, ctx: commands.Context):
        ai_channel_id = int(self.bot.config['identifiers']['ai_channel_id'])
        logger.info(f"Command used in channel: {ctx.channel.id}, AI channel ID: {ai_channel_id}")

        if ctx.channel.id != ai_channel_id:
            await self.send_and_delete(ctx, "This command can only be used in the AI channel.")
            return

        embed = discord.Embed(
            title="**AI Channel Information**",
            description="Welcome to the PortLordsAI channel.",
            color=int(self.embed_colors['primary'], 16)
        )
        embed.add_field(name="Purpose", value="This channel is dedicated to conversing with the AI and seeking assistance with coding and AI-related queries.", inline=False)
        embed.add_field(name="Features", value="`Interact with the AI, ask questions, and share code snippets.`", inline=False)
        embed.add_field(name="Help Command", value="Use `!aihelp` for more detailed information.", inline=False)
        embed.set_image(url=self.embed_banner)
        embed.set_footer(text=self.embed_footer)

        embed_message = await ctx.send(embed=embed)
        if self.delete_responses:
            await ctx.message.delete()
            await embed_message.delete(delay=self.delete_response_delay)

    @commands.command(name='shodan_embed')
    async def shodan_embed(self, ctx: commands.Context):
        shodan_channel_id = int(self.bot.config['identifiers']['shodan_channel_id'])
        logger.info(f"Command used in channel: {ctx.channel.id}, Shodan channel ID: {shodan_channel_id}")

        if ctx.channel.id != shodan_channel_id:
            await self.send_and_delete(ctx, "This command can only be used in the Shodan channel.")
            return

        embed = discord.Embed(
            title="**Shodan Channel Information**",
            description="Welcome to the Shodan channel.",
            color=int(self.embed_colors['primary'], 16)
        )
        embed.add_field(name="Purpose", value="This channel is dedicated to searching for devices and vulnerabilities using Shodan.", inline=False)
        embed.add_field(name="Features", value="`Use the bot to perform Shodan searches and get detailed information.`", inline=False)
        embed.add_field(name="Help Command", value="Use `!shodanhelp` for more detailed information.", inline=False)
        embed.set_image(url=self.embed_banner)
        embed.set_footer(text=self.embed_footer)

        embed_message = await ctx.send(embed=embed)
        if self.delete_responses:
            await ctx.message.delete()
            await embed_message.delete(delay=self.delete_response_delay)

    @commands.command(name='phishing_embed')
    async def phishing_embed(self, ctx: commands.Context):
        phishing_channel_id = int(self.bot.config['identifiers']['phishing_channel_id'])
        logger.info(f"Command used in channel: {ctx.channel.id}, Phishing channel ID: {phishing_channel_id}")

        if ctx.channel.id != phishing_channel_id:
            await self.send_and_delete(ctx, "This command can only be used in the phishing channel.")
            return

        embed = discord.Embed(
            title="**Phishing Channel Information**",
            description="Welcome to the Phishing channel.",
            color=int(self.embed_colors['primary'], 16)
        )
        embed.add_field(name="Purpose", value="This channel is dedicated to creating and discussing phishing techniques.", inline=False)
        embed.add_field(name="Features", value="`Share phishing techniques, discuss strategies, and collaborate with others.`", inline=False)
        embed.add_field(name="Help Command", value="Use `!phishinghelp` for more detailed information.", inline=False)
        embed.set_image(url=self.embed_banner)
        embed.set_footer(text=self.embed_footer)

        embed_message = await ctx.send(embed=embed)
        if self.delete_responses:
            await ctx.message.delete()
            await embed_message.delete(delay=self.delete_response_delay)

async def setup(bot: commands.Bot):
    await bot.add_cog(Embeds(bot))
