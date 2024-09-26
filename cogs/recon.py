import asyncio
import logging
from typing import List
import discord
from discord.ext import commands
from helpers import send_and_delete, create_embed, is_valid_ip_address # type:ignore
import shutil
import io
import ipinfo
from PIL import Image, ImageDraw, ImageFont # type:ignore

logger = logging.getLogger(__name__)

class Recon(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.nmap_path = shutil.which("nmap")
        if not self.nmap_path:
            logger.error("Nmap executable not found.")
            raise Exception("Nmap executable not found.")
        self.delete_commands = self.bot.config['settings']['delete_commands']
        self.delete_command_delay = self.bot.config['settings']['delete_command_delay']
        self.delete_responses = self.bot.config['settings']['delete_responses']
        self.delete_response_delay = self.bot.config['settings']['delete_response_delay']
        self.delete_errors = self.bot.config['settings']['delete_errors']
        self.delete_errors_delay = self.bot.config['settings']['delete_errors_delay']
        self.active_scans: List[asyncio.subprocess.Process] = []

    def validate_ip_address(self, ip):
        return is_valid_ip_address(ip)

    @commands.command(name="recon", help="Perform network reconnaissance using Nmap. Usage: ..recon <target>")
    @commands.cooldown(1, 300, commands.BucketType.user)
    @commands.is_owner()
    async def recon(self, ctx: commands.Context, target: str) -> None:
        if not self.validate_ip_address(target):
            await send_and_delete(
                ctx,
                content="`Error: Invalid IP address format.`",
                delay=self.bot.config['settings']['delete_errors_delay'],
                delete_type='error'
            )
            return

        embed = create_embed(title="Select Scan Intensity",
                              description=f"Choose a scan intensity for the target: **{target}**",
                              color_key='primary',
                              config=self.bot.config
                              )
        message = await ctx.send(embed=embed)

        await message.add_reaction('➖')
        await message.add_reaction('⚪')
        await message.add_reaction('➕')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['➖', '⚪', '➕'] and reaction.message.id == message.id

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)

            if str(reaction.emoji) == '➖':
                nmap_command = [self.nmap_path, '-T4', '-F', target, '-oG', '-']  # Minimal (fast, few ports)
            elif str(reaction.emoji) == '⚪':
                nmap_command = [self.nmap_path, '-T4', '-A', target, '-oG', '-']  # Default (timing template 4, OS detection, etc.)
            elif str(reaction.emoji) == '➕':
                nmap_command = [self.nmap_path, '-T4', '-A', '-p-', target, '-oG', '-']  # Intrusive (scan all ports)

            logger.info(f"Running Nmap command: {' '.join(nmap_command)} for target {target}")

            async with ctx.typing():
                process = await asyncio.create_subprocess_exec(
                    *nmap_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                self.active_scans.append(process)
                stdout, stderr = await process.communicate()
                self.active_scans.remove(process)

                if process.returncode == 0:
                    output = stdout.decode("utf-8").strip()
                    visual_output = self.create_visual_nmap_output(output, target)
                    if visual_output:
                        await ctx.send(file=discord.File(visual_output, filename="nmap_visual.png"))
                    else:
                        embed = create_embed(title="Nmap Scan Results",
                                              description=f"```\n{output}\n```",
                                              color_key='primary',
                                              config=self.bot.config
                                              )
                        await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)

        except asyncio.TimeoutError:
            await send_and_delete(ctx, content="`Scan selection timed out.`", delay=self.delete_response_delay)
        except Exception as e:
            logger.error(f"An unexpected error occurred in recon: {e}", exc_info=True)
            await send_and_delete(ctx, content="`An error occurred during the Nmap scan. Please try again later.`", delay=self.delete_errors_delay, delete_type='error')

    @recon.error
    async def recon_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(ctx, content=f"`This command is on cooldown. Please try again in {retry_after:.2f} seconds.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')
        elif isinstance(error, commands.MissingRequiredArgument):
            await send_and_delete(ctx, content="`Error: Please provide a target IP address. Example: ..recon 192.168.1.1`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')
        elif isinstance(error, commands.NotOwner):
            await send_and_delete(ctx, content="`Error: Only the bot owner can use this command.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again later.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

    @commands.command(name="reconhelp", help="Displays help for the 'recon' command.")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def recon_help(self, ctx: commands.Context) -> None:
        try:
            embed = create_embed(
                title="Recon Command Help",
                description="This command performs network reconnaissance using Nmap.",
                color_key='primary',
                fields=[
                    ("Usage", "`..recon <target>`", False),
                    ("Arguments", "`<target>`: The IP address of the target server.", False),
                    ("Scan Intensities", """
                    ➖ **Minimal Scan:** Fast scan with fewer ports (e.g., `nmap -T4 -F <target>`)
                    ⚪ **Default Scan:** Standard Nmap scan with OS detection (e.g., `nmap -T4 -A <target>`)
                    ➕ **Intrusive Scan:** Scans all ports (e.g., `nmap -T4 -A -p- <target>`)
                    """, False),
                    ("Example", "`..recon 192.168.1.10`", False)
                ],
                config=self.bot.config
            )
            await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)
            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

        except Exception as e:
            logger.error(f"An unexpected error occurred in recon_help: {e}", exc_info=True)
            await send_and_delete(
                ctx,
                content="`An error occurred while displaying the help message. Please try again later.`",
                delay=self.delete_errors_delay,
                delete_type='error'
            )

    @recon_help.error
    async def recon_help_error(self, ctx, error):
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

    @commands.command(name="cancelscan", help="Cancels the ongoing Nmap scan.")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def cancel_scan(self, ctx: commands.Context) -> None:
        try:
            if not self.active_scans:
                await send_and_delete(ctx, content="`No active Nmap scans to cancel.`",
                                    delay=self.bot.config['settings']['delete_response_delay'])
                return

            for process in self.active_scans:
                process.kill()

            self.active_scans.clear()
            embed = create_embed(title="Nmap Scans Cancelled",
                                  description="`All active Nmap scans have been cancelled.`",
                                  color_key='primary',
                                  config=self.bot.config
                                  )
            await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)

        except Exception as e:
            logger.error(f"An unexpected error occurred in cancel_scan: {e}", exc_info=True)
            await send_and_delete(ctx, content="`An error occurred while cancelling the scans. Please try again later.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

    @cancel_scan.error
    async def cancel_scan_error(self, ctx, error):
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

    def create_visual_nmap_output(self, nmap_output: str, target_ip: str) -> io.BytesIO:
        try:
            access_token = 'ea26dd751430f6'
            handler = ipinfo.getHandler(access_token)

            background_image_path = 'files/assets/earth.jpg'

            details = handler.getDetails(target_ip)
            latitude = details.latitude
            longitude = details.longitude

            if latitude is not None and longitude is not None:
                img = Image.open(background_image_path)
                draw = ImageDraw.Draw(img)

                map_width, map_height = img.size
                longitude = float(longitude)
                latitude = float(latitude)
                x = int((longitude + 180) * (map_width / 360))
                y = int((90 - latitude) * (map_height / 180))

                marker_size = 30
                draw.ellipse((x - marker_size, y - marker_size, x + marker_size, y + marker_size), fill="red")

                img_data = io.BytesIO()
                img.save(img_data, format="PNG")
                img_data.seek(0)

                return img_data

            else:
                logger.warning(f"No location data found for IP: {target_ip}")
                return None

        except Exception as e:
            logger.error(f"Error creating visual Nmap output: {e}", exc_info=True)
            return None

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Recon(bot))
