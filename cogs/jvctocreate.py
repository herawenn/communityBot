import discord
from discord.ext import commands


class JVCtoCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def jvctocreate(self, ctx, name: str):
        """Creates a voice channel with VC commands for owner control.

        Args:
            ctx (commands.Context): The context of the command.
            name (str): The name of the voice channel to create.
        """

        # Check if the user has permission to create channels
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("You do not have permission to create channels.")
            return

        # Create the voice channel
        channel = await ctx.guild.create_voice_channel(name)

        # Set the owner of the channel to the user who created it
        await channel.set_permissions(ctx.author, manage_channels=True, mute_members=True, deafen_members=True, kick_members=True)

        # Send a message confirming the channel creation
        await ctx.send(f"Created voice channel: {channel.mention}")

        # Add a message to the channel with the commands
        await channel.send("**Welcome to {channel.name}!**")
        await channel.send("**Commands:**")
        await channel.send("`!lock` - Locks the channel, preventing others from joining.")
        await channel.send("`!unlock` - Unlocks the channel, allowing others to join.")
        await channel.send("`!muteall` - Mutes all users in the channel.")
        await channel.send("`!unmuteall` - Unmutes all users in the channel.")
        await channel.send("`!kickall` - Kicks all users from the channel.")
        await channel.send("`!mute <member>` - Mutes a specific user.")
        await channel.send("`!unmute <member>` - Unmutes a specific user.")
        await channel.send("`!kick <member>` - Kicks a specific user from the channel.")

    @commands.command()
    async def lock(self, ctx):
        """Locks the current voice channel, preventing others from joining."""

        # Check if the user is in a voice channel
        if not ctx.author.voice:
            await ctx.send("You are not in a voice channel.")
            return

        # Check if the user has permission to manage the channel
        if not ctx.author.voice.channel.permissions_for(ctx.author).manage_channels:
            await ctx.send("You do not have permission to manage this channel.")
            return

        # Lock the channel
        await ctx.author.voice.channel.set_permissions(ctx.guild.default_role, connect=False)
        await ctx.send("Channel locked.")

    @commands.command()
    async def unlock(self, ctx):
        """Unlocks the current voice channel, allowing others to join."""

        # Check if the user is in a voice channel
        if not ctx.author.voice:
            await ctx.send("You are not in a voice channel.")
            return

        # Check if the user has permission to manage the channel
        if not ctx.author.voice.channel.permissions_for(ctx.author).manage_channels:
            await ctx.send("You do not have permission to manage this channel.")
            return

        # Unlock the channel
        await ctx.author.voice.channel.set_permissions(ctx.guild.default_role, connect=True)
        await ctx.send("Channel unlocked.")

    @commands.command()
    async def muteall(self, ctx):
        """Mutes all users in the current voice channel."""

        # Check if the user is in a voice channel
        if not ctx.author.voice:
            await ctx.send("You are not in a voice channel.")
            return

        # Check if the user has permission to manage the channel
        if not ctx.author.voice.channel.permissions_for(ctx.author).manage_channels:
            await ctx.send("You do not have permission to manage this channel.")
            return

        # Mute all users in the channel
        for member in ctx.author.voice.channel.members:
            if member != ctx.author:
                await member.edit(mute=True)
        await ctx.send("All users muted.")

    @commands.command()
    async def unmuteall(self, ctx):
        """Unmutes all users in the current voice channel."""

        # Check if the user is in a voice channel
        if not ctx.author.voice:
            await ctx.send("You are not in a voice channel.")
            return

        # Check if the user has permission to manage the channel
        if not ctx.author.voice.channel.permissions_for(ctx.author).manage_channels:
            await ctx.send("You do not have permission to manage this channel.")
            return

        # Unmute all users in the channel
        for member in ctx.author.voice.channel.members:
            if member != ctx.author:
                await member.edit(mute=False)
        await ctx.send("All users unmuted.")

    @commands.command()
    async def kickall(self, ctx):
        """Kicks all users from the current voice channel."""

        # Check if the user is in a voice channel
        if not ctx.author.voice:
            await ctx.send("You are not in a voice channel.")
            return

        # Check if the user has permission to manage the channel
        if not ctx.author.voice.channel.permissions_for(ctx.author).manage_channels:
            await ctx.send("You do not have permission to manage this channel.")
            return

        # Kick all users from the channel
        for member in ctx.author.voice.channel.members:
            if member != ctx.author:
                await member.move_to(None)
        await ctx.send("All users kicked.")

    @commands.command()
    async def mute(self, ctx, member: discord.Member):
        """Mutes a specific user in the current voice channel."""

        # Check if the user is in a voice channel
        if not ctx.author.voice:
            await ctx.send("You are not in a voice channel.")
            return

        # Check if the user has permission to manage the channel
        if not ctx.author.voice.channel.permissions_for(ctx.author).manage_channels:
            await ctx.send("You do not have permission to manage this channel.")
            return

        # Check if the target user is in the same voice channel
        if member not in ctx.author.voice.channel.members:
            await ctx.send("That user is not in this voice channel.")
            return

        # Mute the target user
        await member.edit(mute=True)
        await ctx.send(f"{member.mention} muted.")

    @commands.command()
    async def unmute(self, ctx, member: discord.Member):
        """Unmutes a specific user in the current voice channel."""

        # Check if the user is in a voice channel
        if not ctx.author.voice:
            await ctx.send("You are not in a voice channel.")
            return

        # Check if the user has permission to manage the channel
        if not ctx.author.voice.channel.permissions_for(ctx.author).manage_channels:
            await ctx.send("You do not have permission to manage this channel.")
            return

        # Check if the target user is in the same voice channel
        if member not in ctx.author.voice.channel.members:
            await ctx.send("That user is not in this voice channel.")
            return

        # Unmute the target user
        await member.edit(mute=False)
        await ctx.send(f"{member.mention} unmuted.")

    @commands.command()
    async def kick(self, ctx, member: discord.Member):
        """Kicks a specific user from the current voice channel."""

        # Check if the user is in a voice channel
        if not ctx.author.voice:
            await ctx.send("You are not in a voice channel.")
            return

        # Check if the user has permission to manage the channel
        if not ctx.author.voice.channel.permissions_for(ctx.author).manage_channels:
            await ctx.send("You do not have permission to manage this channel.")
            return

        # Check if the target user is in the same voice channel
        if member not in ctx.author.voice.channel.members:
            await ctx.send("That user is not in this voice channel.")
            return

        # Kick the target user from the channel
        await member.move_to(None)
        await ctx.send(f"{member.mention} kicked.")


def setup(bot):
    bot.add_cog(JVCtoCreate(bot))
