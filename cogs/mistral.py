import discord
from discord.ext import commands
import requests
import json
import logging

logger = logging.getLogger(__name__)

class Mistral(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = bot.config['mistral']['api_url']
        self.api_key = bot.config['mistral']['api_key']
        self.model = bot.config['mistral']['model']
        self.temperature = bot.config['mistral']['temperature']
        self.prompt = bot.config['mistral']['prompt']
        self.conversation_history = {}

    async def get_response(self, user_input, user_id):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": self.conversation_history.get(user_id, []) + [{"role": "user", "content": user_input}]
        }
        try:
            response = requests.post(self.api_url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Error making request to Mistral API: {e}")
            return f"Error: Unable to connect to Mistral API"
        response_data = response.json()

        if 'choices' in response_data:
            return response_data['choices'][0]['message']['content']
        else:
            logger.error(f"Invalid response from Mistral API: {response_data}")
            return f"Error: Invalid response from Mistral API"

    @commands.command(name='chat')
    async def chat(self, ctx, *, message: str):
        user_id = str(ctx.author.id)
        response = await self.get_response(message, user_id)

        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = [{"role": "system", "content": self.prompt}]
        self.conversation_history[user_id].append({"role": "user", "content": message})
        self.conversation_history[user_id].append({"role": "assistant", "content": response})

        await ctx.send(response)

async def setup(bot):
    await bot.add_cog(Mistral(bot))
