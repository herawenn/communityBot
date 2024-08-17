import logging
from typing import Dict
import os
import sys
import asyncio
from discord.ext import commands
import google.generativeai as genai
import json
from discord import File

logger = logging.getLogger(__name__)

CONFIG_PATH = 'config.json'

def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config

config = load_config(CONFIG_PATH)

genai_api_key = config['apis']['gemini']['api_key']
model_name = config['apis']['gemini']['model']
temperature = config['apis']['gemini']['temperature']
prompt = config['apis']['gemini']['prompt']

genai.configure(api_key=genai_api_key)

generation_config = {
    "temperature": temperature,
    "top_p": 0.95,
    "top_k": 0,
    "max_output_tokens": 8192,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config, safety_settings=safety_settings)

class PortlordsAI(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.conversation_history: Dict[str, list] = {}
        self.rate_limit: int = config['settings']['rate_limit']
        self.delete_commands: bool = config['settings']['delete_commands']
        self.delete_command_delay: int = config['settings']['delete_command_delay']
        self.delete_responses: bool = config['settings']['delete_responses']
        self.delete_response_delay: int = config['settings']['delete_response_delay']

    async def get_response(self, user_input: str, user_id: str) -> str:
        try:
            convo = model.start_chat(history=[])
            convo.send_message(f"{prompt} {user_input}")
            response = convo.last.text
            return response

        except Exception as e:
            logger.error(f"Error making request to AI API: {e}", exc_info=True)
            return "Error: Unable to connect to AI API."

    async def send_response_as_file(self, ctx: commands.Context, response: str, filename: str) -> None:
        with open(filename, 'w') as f:
            f.write(response)

        await ctx.send(file=File(filename))

    @commands.command(name='chat', help="Conversate with PortLords.AI")
    async def chat(self, ctx: commands.Context, *, message: str) -> None:
        user_id: str = str(ctx.author.id)

        if ctx.channel.id != int(self.bot.config['identifiers']['ai_channel_id']):
            error_message = await ctx.send(f"```Error: This command can only be used in the designated AI channel.```")
            if self.delete_responses:
                await asyncio.sleep(self.delete_response_delay)
                await error_message.delete()
                await ctx.message.delete()
            return

        async with ctx.typing():
            response = await self.get_response(message, user_id)

        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        self.conversation_history[user_id].append({"role": "user", "content": message})
        self.conversation_history[user_id].append({"role": "assistant", "content": response})

        await self.send_response_as_file(ctx, response, 'response.txt')

        if self.delete_responses:
            await asyncio.sleep(self.delete_response_delay)
            await ctx.message.delete()

    @chat.error
    async def chat_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        error_message = f"```Error: An unexpected error occurred. Please try again later.```"
        response_message = await ctx.send(error_message)
        logger.error(f"Unexpected error occurred: {error}")

        if self.delete_responses:
            await asyncio.sleep(self.delete_response_delay)
            await response_message.delete()

    @commands.command(name='aiscan', help="Generate a vulnerability assessment.")
    async def aiscan(self, ctx: commands.Context) -> None:
        user_id: str = str(ctx.author.id)

        async with ctx.typing():
            response = await self.get_response("Generate a vulnerability assessment.", user_id)

        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        self.conversation_history[user_id].append({"role": "user", "content": "Generate a vulnerability assessment."})
        self.conversation_history[user_id].append({"role": "assistant", "content": response})

        await self.send_response_as_file(ctx, response, 'vuln_assessment.txt')

        if self.delete_responses:
            await asyncio.sleep(self.delete_response_delay)
            await ctx.message.delete()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PortlordsAI(bot))
