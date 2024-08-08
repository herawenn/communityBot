import discord
from discord.ext import commands
from youtube_dl import YoutubeDL
import asyncio
from typing import Optional
from discord import FFmpegOpusAudio
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json

with open('config.json') as f:
    config = json.load(f)


# Spotify API Creden
SPOTIFY_CLIENT_SECRET = config.get('spotify_client_secret')
SPOTIFY_CLIENT_ID = config.get('spotify_client_id')


# YDL Options
ytdl_opts = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
}

# YoutubeDL
ydl = YoutubeDL(ytdl_opts)

# Spotify Client Credentials
client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Discord Bot
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Global Variables
voice_client = None
queue = []
current_song = None


# Helper Functions
def get_audio_url(query: str, source: str):
    if source == "youtube":
        try:
            with ydl:
                info = ydl.extract_info(query, download=False)
                url = info["formats"][0]["url"]
        except Exception as e:
            print(f"Error fetching Youtube audio: {e}")
            return None
    elif source == "spotify":
        try:
            results = sp.search(q=query, type="track")
            track_id = results["tracks"]["items"][0]["id"]
            track_info = sp.track(track_id)
            url = track_info["preview_url"]
        except Exception as e:
            print(f"Error fetching Spotify audio: {e}")
            return None
    return url


async def play_next(ctx):
    global voice_client, queue, current_song

    if len(queue) > 0:
        current_song = queue.pop(0)
        try:
            voice_client.play(FFmpegOpusAudio(current_song), after=lambda e: asyncio.run(play_next(ctx)))
        except Exception as e:
            await ctx.send(f"Error playing next song: {e}")
    else:
        current_song = None
        await voice_client.disconnect()


class music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Music Commands
    @commands.command(name="play", help="Plays a song from Youtube, Spotify, or Soundcloud")
    async def play(ctx, query: str, source: Optional[str] = "youtube"):
        global voice_client, queue, current_song

        if not voice_client:
            try:
                voice_client = await ctx.author.voice.channel.connect()
            except Exception as e:
                await ctx.send(f"Error connecting to voice channel: {e}")
                return

        if source not in ["youtube", "spotify"]:
            await ctx.send("Invalid source. Please choose 'youtube' or 'spotify'.")
            return

        audio_url = get_audio_url(query, source)
        if audio_url:
            queue.append(audio_url)
            if not current_song:
                await play_next(ctx)
            else:
                await ctx.send(f"Added '{query}' to the queue.")
        else:
            await ctx.send(f"Could not find a song for '{query}'")

    @commands.command(name="skip", help="Skips the current song")
    async def skip(self, ctx):
        global voice_client, queue, current_song

        if not voice_client:
            await ctx.send("Not connected to a voice channel.")
            return

        if len(queue) > 0:
            current_song = None
            await play_next(ctx)
        else:
            await ctx.send("There are no more songs in the queue.")
            await voice_client.disconnect()

    @commands.command(name="stop", help="Stops the music and disconnects from the voice channel")
    async def stop(self, ctx):
        global voice_client, queue, current_song

        if not voice_client:
            await ctx.send("Not connected to a voice channel.")
            return

        voice_client.stop()
        queue.clear()
        current_song = None
        await voice_client.disconnect()


@bot.event
async def on_voice_state_update(member, before, after):
    global voice_client

    if member == bot.user and after.channel is None:
        voice_client = None


async def setup(bot):
    await bot.add_cog(music.Music(bot))
