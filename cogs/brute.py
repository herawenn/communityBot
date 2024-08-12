import shlex
import asyncio
import logging
import discord
from discord.ext import commands
from discord import File
import os

logger = logging.getLogger(__name__)

class Hydra(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.password_lists_dir = bot.config.get('identifiers', {}).get('password_lists_dir', 'password_lists')
        self.username_lists_dir = bot.config.get('identifiers', {}).get('username_lists_dir', 'username_lists')

    async def run_hydra(self, username_list, password_list, service, target_ip, options=None):
        command = f"hydra -L {username_list} -P {password_list} {service}://{target_ip}"
        if options:
            command += " " + options
        args = shlex.split(command)
        try:
            process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate()
            stdout = stdout.decode('utf-8')
            stderr = stderr.decode('utf-8')
            return stdout, stderr
        except asyncio.TimeoutError:
            logger.error("Timeout error occurred while running Hydra.")
            return None, "Timeout error occurred. Please try again later."
        except Exception as e:
            logger.error(f"Error running Hydra: {e}")
            return None, "An error occurred while executing Hydra. Please try again later."

    @commands.command(name="hydra", help="Brute force an IP using Hydra.")
    @commands.is_owner()
    async def hydra(self, ctx):
        try:
            username_lists = os.listdir(self.username_lists_dir)
            password_lists = os.listdir(self.password_lists_dir)

            embed = discord.Embed(
                title="Hydra Command",
                description="Please choose a username list and password list from the options below.",
                color=int(self.bot.config['embeds']['embed_colors']['primary'], 16)
            )

            embed.add_field(
                name="Username Lists",
                value=", ".join(username_lists),
                inline=False
            )

            embed.add_field(
                name="Password Lists",
                value=", ".join(password_lists),
                inline=False
            )

            await ctx.send(embed=embed)

            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel

            username_list_msg = await self.bot.wait_for('message', check=check)
            username_list = username_list_msg.content

            if username_list not in username_lists:
                await ctx.send("Invalid username list. Please try again.")
                return

            password_list_msg = await self.bot.wait_for('message', check=check)
            password_list = password_list_msg.content

            if password_list not in password_lists:
                await ctx.send("Invalid password list. Please try again.")
                return

            service_msg = await self.bot.wait_for('message', check=check)
            service = service_msg.content

            target_ip_msg = await self.bot.wait_for('message', check=check)
            target_ip = target_ip_msg.content

            options_msg = await self.bot.wait_for('message', check=check)
            options = options_msg.content

            username_list_path = os.path.join(self.username_lists_dir, username_list)
            password_list_path = os.path.join(self.password_lists_dir, password_list)

            stdout, stderr = await self.run_hydra(username_list_path, password_list_path, service, target_ip, options)

            if stdout:
                await ctx.send(f"```{stdout}```")
            else:
                await ctx.send(stderr)

        except Exception as e:
            logger.error(f"An error occurred while executing hydra: {e}")
            await ctx.send("An error occurred while executing Hydra. Please try again later.")

    @commands.command(name="hydrainfo", help="Provides information on how to use the hydra command.")
    async def hydrainfo(self, ctx):
        embed = discord.Embed(
            title="Hydra Command Help Page",
            description="Gives detailed information on using hydra.",
            color=int(self.bot.config['embeds']['embed_colors']['primary'], 16)
        )

        embed.add_field(
            name="Command Explanation",
            value=(
                "The `hydra` command leverages the Hydra tool to perform brute force attacks on various services. "
                "You can specify different options such as the target IP, port, usernames, passwords, and more. "
                "This command is restricted to the bot owner to ensure responsible use."
            ),
            inline=False
        )

        embed.add_field(
            name="Examples",
            value=(
                "*HTTP Basic Auth:*\n"
                "`hydra -l admin -P passlist.txt 192.168.1.1 http-get /private`\n\n"
                "*SSH with Specific Port:*\n"
                "`hydra -l root -P passlist.txt -s 2222 ssh://192.168.1.1`\n\n"
                "*FTP with IP Range:*\n"
                "`hydra -L users.txt -P passlist.txt 192.168.1.1-254 ftp`\n\n"
                "*MySQL with Options:*\n"
                "`hydra -l user -P passlist.txt -f -o results.txt -t 4 mysql://192.168.1.1`\n\n"
                "*rdp service single password:*\n"
                "`hydra -l user -p password rdp://[192.168.1.1]`\n\n"
                "*VNC with password list and specific port:*\n"
                "`hydra -l admin -P passlist.txt -s 5900 vnc://192.168.1.1`\n\n"
                "*Telnet with specific port and username list:*\n"
                "`hydra -L users.txt -P passlist.txt -s 2323 telnet://192.168.1.1`"
            ),
            inline=False
        )

        embed.add_field(
            name="Note",
            value="This command is restricted to the bot owner.",
            inline=False
        )

        embed.set_footer(text=self.bot.config['embeds']['global_footer'])

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Hydra(bot))
