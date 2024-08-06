import discord
from discord.ext import commands
import json
from bot import logger

with open('config.json') as f:
    config = json.load(f)

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="verification", help="Starts the verification process.")
    async def verification_command(self, ctx):
        logger.info(f"Verification command invoked by {ctx.author} in {ctx.guild}")
        try:
            server = self.bot.get_guild(int(config['server_id']))
            if not server:
                await ctx.send(f"Error: Could not find the server with ID {config['server_id']}. Please check your config.")
                return

            verified_role = discord.utils.get(server.roles, name=config['verified_role_name'])
            if not verified_role:
                await ctx.send(f"Error: Could not find the verified role with name '{config['verified_role_name']}'. Please check your server roles.")
                return

            verification_channel_id = int(config['verification_channel_id'])
            verification_channel = self.bot.get_channel(verification_channel_id)
            if not verification_channel:
                await ctx.send(f"Error: Could not find the verification channel with ID '{verification_channel_id}'. Please check your config.")
                return

            if ctx.channel.id != verification_channel.id:
                await ctx.send(f"Please use this command in the designated verification channel: {verification_channel.mention}")
                return

            embed = discord.Embed(
                title="Agree & Continue",
                description="🗹 `We are not responsible for the actions of our members`",
                color=discord.Color(0x6900ff),
            )
            view = discord.ui.View()
            button = discord.ui.Button(label="Verify", style=discord.ButtonStyle.secondary)

            async def button_callback(interaction):
                try:
                    initial_role_id = config.get('initial_role_id')
                    initial_role = discord.utils.get(interaction.user.guild.roles, id=initial_role_id)
                    if initial_role in interaction.user.roles:
                        await interaction.user.remove_roles(initial_role)
                    await interaction.user.add_roles(verified_role)
                    await interaction.response.send_message("Verification successful!", ephemeral=False)
                    logger.info(f"User {interaction.user} verified successfully in {ctx.guild}")
                except Exception as e:
                    logger.error(f"Error during verification: {e}")
                    await interaction.response.send_message("Error during verification. Please try again later.", ephemeral=False)

            button.callback = button_callback
            view.add_item(button)

            await ctx.send(embed=embed, view=view)
            logger.info(f"Verification embed sent to channel {verification_channel} in {ctx.guild}")

        except Exception as e:
            logger.error(f"An error occurred in the verification command: {e}")
            await ctx.send("An error occurred. Please try again later.")

async def setup(bot):
    await bot.add_cog(Verification(bot))
