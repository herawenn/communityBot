import asyncio
import discord
import logging

logger = logging.getLogger(__name__)

async def send_and_delete(ctx, content=None, embed=None, file=None, delay=None, delete_type='response'):
    try:
        if delete_type == 'command' and ctx.bot.config['settings']['delete_commands']:
            await asyncio.sleep(ctx.bot.config['settings']['delete_command_delay'])
            await ctx.message.delete()

        if content or embed or file:
            message = await ctx.send(content=content, embed=embed, file=file)

            if delete_type == 'response' and ctx.bot.config['settings']['delete_responses']:
                await asyncio.sleep(delay)
                await message.delete()

            return message
    except Exception as e:
        logger.error(f"An error occurred in send_and_delete: {e}")
