import asyncio
import json
import logging
from typing import Dict
import discord
from discord.ext import commands
import requests

logger = logging.getLogger(__name__)

class Mistral(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.api_url: str = bot.config['apis']['mistral']['api_url']
        self.api_key: str = bot.config['apis']['mistral']['api_key']
        self.prompt: str = bot.config['apis']['mistral']['prompt']
        self.temperature: float = bot.config['apis']['mistral'][
            'temperature'
        ]
        self.conversation_history: Dict[str, list] = {}

    async def get_response(self, user_input: str, user_id: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "temperature": self.temperature,
            "messages": self.conversation_history.get(user_id, []) +
                        [{"role": "user", "content": user_input}]
        }

        try:
            response = await asyncio.to_thread(
                requests.post,
                self.api_url,
                headers=headers,
                data=json.dumps(data)
            )
            response.raise_for_status()
            response_data = response.json()

            if 'choices' in response_data:
                response_message = response_data['choices'][0]['message'][
                    'content'
                ]
                return response_message
            else:
                error_message = f"Unexpected response format: {response_data}"
                logger.error(error_message)
                return f"Error: {error_message}"

        except requests.RequestException as e:
            logger.error(
                f"Error making request to Mistral API: {e}",
                exc_info=True
            )
            return "Error: Unable to connect to Mistral API."

    @commands.command(name='chat', help="Chat with the AI.")
    async def mistral(self, ctx: commands.Context, *, message: str) -> None:
        user_id: str = str(ctx.author.id)

        if ctx.channel.id != int(self.bot.config['identifiers']['ai_channel_id']):
            await ctx.send("This command can only be used in the designated AI channel.")
            return

        async with ctx.typing():
            response = await self.get_response(message, user_id)

        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = [
                {"role": "system", "content": self.prompt}
            ]
        self.conversation_history[user_id].append(
            {"role": "user", "content": message}
        )
        self.conversation_history[user_id].append(
            {"role": "assistant", "content": response}
        )

        await ctx.send(response)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Mistral(bot))
