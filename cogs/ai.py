import logging
import asyncio
import json
import discord
import tempfile
import os
import re
from discord import File
from discord.ext import commands
from typing import Dict
import google.generativeai as genai
from helpers import send_and_delete

logger = logging.getLogger(__name__)

CONFIG_PATH = 'files/json/config.json'

def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config

config = load_config(CONFIG_PATH)

genai_api_key = os.getenv('GEMINI_API_KEY')
model_name = config['apis']['gemini']['model']
temperature = config['apis']['gemini']['temperature']
chat_prompt = config['apis']['gemini']['chat_prompt']
aiscan_prompt = config['apis']['gemini']['aiscan_prompt']
ai_channel_id = config['identifiers']['ai_channel_id']

genai.configure(api_key=genai_api_key)

generation_config = {"temperature": temperature, "top_p": 0.95, "top_k": 0, "max_output_tokens": 8192}

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
        self.ai_channel_id = ai_channel_id

    async def log_action(self, ctx, action, message):
        logging_cog = self.bot.get_cog('Logging')
        if logging_cog:
            await logging_cog.log_message(f"{action.capitalize()} Action: {message}")

    def validate_ip_address(self, ip: str) -> bool:
        regex = "^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        if re.search(regex, ip):
            return True
        else:
            return False

    async def get_response(self, user_input: str, user_id: str, prompt: str) -> str:
        try:
            convo = model.start_chat(history=[])
            convo.send_message(f"{prompt} {user_input}")
            response = convo.last.text
            return response

        except Exception as e:
            logger.error(f"Error making request to AI API: {e}", exc_info=True)
            return "Error: Unable to connect to AI API."

    async def send_response_as_file(self, ctx: commands.Context, response: str, filename: str) -> None:
        try:
            with tempfile.NamedTemporaryFile(delete=True, mode='w', newline='') as temp_file:
                temp_file.write(response)
                temp_file.flush()

                await ctx.send(file=File(temp_file.name, filename=filename))

                if self.delete_responses:
                    logger.info(f"Scheduling deletion of response message: {ctx.message.content}")
                    await asyncio.sleep(self.delete_response_delay)
                    try:
                        await ctx.message.delete()
                        logger.info(f"Deleted response message: {ctx.message.content}")
                    except discord.HTTPException as e:
                        logger.error(f"Failed to delete response message: {ctx.message.content}, Error: {e}")
                    except Exception as e:
                        logger.error(f"An unexpected error occurred while deleting response message: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while sending response as file: {e}", exc_info=True)

    @commands.command(name='chat', help="Converse with PortLords.AI.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def chat(self, ctx: commands.Context, *, message: str) -> None:
        if ctx.channel.id != self.ai_channel_id:
            await ctx.send(f"This command can only be used in <#{self.ai_channel_id}>.")
            return

        try:
            user_id: str = str(ctx.author.id)

            async with ctx.typing():
                response = await self.get_response(message, user_id, chat_prompt)

            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            self.conversation_history[user_id].append({"role": "user", "content": message})
            self.conversation_history[user_id].append({"role": "assistant", "content": response})

            await self.send_response_as_file(ctx, response, 'response.txt')

            await self.log_action(ctx, "chat", f"Chat command used by {ctx.author.mention} in {ctx.channel.mention}: {message}")
        except Exception as e:
            logger.error(f"An unexpected error occurred in chat command: {e}", exc_info=True)
            await send_and_delete(ctx, "`An unexpected error occurred. Please try again later.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

    @chat.error
    async def chat_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        try:
            error_message = f"`Error: An unexpected error occurred. Please try again later.`"
            response_message = await ctx.send(error_message)
            logger.error(f"Unexpected error occurred: {error}")

            if self.delete_responses:
                await asyncio.sleep(self.delete_response_delay)
                await response_message.delete()
        except Exception as e:
            logger.error(f"An unexpected error occurred in chat_error: {e}", exc_info=True)

    @commands.command(name='aiscan', help="Generate a vulnerability assessment for a given IP address.")
    @commands.cooldown(1, 300, commands.BucketType.user)  # Rate Limit
    async def aiscan(self, ctx: commands.Context, ip_address: str) -> None:
        if ctx.channel.id != self.ai_channel_id:
            await ctx.send(f"This command can only be used in <#{self.ai_channel_id}>.")
            return

        try:
            user_id: str = str(ctx.author.id)

            async with ctx.typing():
                response = await self.get_response(f"IP address: {ip_address}", user_id, aiscan_prompt)

            if not self.validate_ip_address(ip_address):
                error_message = await ctx.send(f"`Error: Invalid IP address format.`")
                await self.delete_message_after_delay(error_message, self.delete_response_delay)
                return

            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            self.conversation_history[user_id].append({"role": "user", "content": f"Generate a vulnerability assessment for the IP address {ip_address}."})
            self.conversation_history[user_id].append({"role": "assistant", "content": response})

            await self.send_response_as_file(ctx, response, 'vuln_assessment.txt')

            await self.log_action(ctx, "aiscan", f"Aiscan command used by {ctx.author.mention} in {ctx.channel.mention}: {ip_address}")
        except Exception as e:
            logger.error(f"An unexpected error occurred in aiscan command: {e}", exc_info=True)
            await send_and_delete(ctx, "`An unexpected error occurred. Please try again later.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')

    async def delete_message_after_delay(self, message: discord.Message, delay: int) -> None:
        if self.delete_responses:
            await asyncio.sleep(delay)
            try:
                await message.delete()
            except discord.HTTPException as e:
                logger.error(f"Failed to delete message: {message.content}, Error: {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred while deleting message: {e}")

    def is_valid_ip_address(self, ip_address: str) -> bool:
        ip_regex = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
        return bool(ip_regex.match(ip_address))

    async def evaluate_code(self, code_snippet: str, question: str) -> bool:
        prompt = f"Is this code snippet a valid and correct answer to the following question: {question}\n\nCode Snippet:\n{code_snippet}\n\nAnswer with 'Yes' or 'No'."
        try:
            convo = model.start_chat(history=[])
            convo.send_message(prompt)
            response = convo.last.text
            return response.strip().lower() == 'yes'
        except Exception as e:
            logger.error(f"Error making request to AI API for code evaluation: {e}", exc_info=True)
            return False

    async def handle_code_submission(self, ctx: commands.Context, question: str, code_snippet: str) -> bool:
        is_code_correct = await self.evaluate_code(code_snippet, question)
        if is_code_correct:
            await ctx.author.send(f"```\n{code_snippet}\n```\n`Code is correct!`")
            return True
        else:
            await ctx.author.send(f"```\n{code_snippet}\n```\n`Code does not meet the requirements.`")
            return False

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PortlordsAI(bot))
