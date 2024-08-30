import discord
import asyncio
import random
from discord.ext import commands
import logging
import json
from helpers import send_and_delete

logger = logging.getLogger(__name__)

class Quiz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.tier_points = {
            1: 10,
            2: 50,
            3: 75,
            4: 100,
            5: 200
        }
        self.questions = self.load_questions()
        self.current_question = None
        self.active_quiz = False
        self.answers = []
        self.delete_responses = self.bot.config['settings']['delete_responses']
        self.delete_response_delay = self.bot.config['settings']['delete_response_delay']
        self.delete_errors = self.bot.config['settings']['delete_errors']
        self.delete_errors_delay = self.bot.config['settings']['delete_errors_delay']

    async def send_and_delete(self, ctx: discord.ext.commands.Context, message: str = None, embed: discord.Embed = None, delay: int = None, delete_type: str = "response") -> None:
        try:
            if message is None and embed is None:
                return

            sent_message = await ctx.send(content=message, embed=embed)

            if delay is not None:
                if delete_type == "response" and self.bot.config['settings']['delete_responses']:
                    await asyncio.sleep(delay)
                    await sent_message.delete()
                elif delete_type == "command" and self.bot.config['settings']['delete_commands']:
                    await asyncio.sleep(delay)
                    await ctx.message.delete()
                elif delete_type == "error" and self.bot.config['settings']['delete_errors']:
                    await asyncio.sleep(delay)
                    await sent_message.delete()

        except discord.HTTPException as e:
            logger.error(f"Failed to delete message: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while sending and deleting a message: {e}", exc_info=True)

    def load_questions(self):
        try:
            with open('files/json/questions.json', 'r') as f:
                return json.load(f)['questions']
        except FileNotFoundError:
            logger.error("`Question file not found. Please create 'files/json/questions.json'.`")
            return []
        except json.JSONDecodeError:
            logger.error("`Invalid JSON format in the question file.`")
            return []

    async def safe_delete_message(self, message, delay):
        try:
            await asyncio.sleep(delay)
            await message.delete()
        except discord.NotFound:
            logger.warning(f"Message not found: {message.id}")
        except Exception as e:
            logger.error(f"An error occurred while deleting message {message.id}: {e}", exc_info=True)


    @commands.command(name="quiz", help="Start a cybersecurity quiz.")
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def start_quiz(self, ctx: commands.Context):
        try:
            if self.active_quiz:
                await send_and_delete(ctx, "`A quiz is already in progress.`", delay=self.delete_response_delay)
                return

            self.active_quiz = True
            self.answers = []
            self.current_question = random.choice(self.questions)

            if self.current_question['type'] == 'multiple_choice':
                await self.handle_multiple_choice_question(ctx)
            elif self.current_question['type'] == 'code':
                await self.handle_code_question(ctx)
            elif self.current_question['type'] == 'direct_message':
                await self.handle_direct_message_question(ctx)
            else:
                await ctx.send("`Invalid question type. Please check your 'questions.json' file.`")

            self.active_quiz = False
            self.current_question = None
            self.answers = []

        except Exception as e:
            logger.error(f"An unexpected error occurred in start_quiz: {e}", exc_info=True)
            await send_and_delete(ctx, "`An error occurred while starting the quiz. Please try again later.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')

    async def handle_code_question(self, ctx: commands.Context):
        question = self.current_question['question']
        expected_code = self.current_question['answer']

        question_message = await ctx.send(f"`Question: {question}`\n`Submit your code snippet as a direct message (DM) to the bot.`")

        def check(message):
            return message.author != self.bot.user and isinstance(message.channel, discord.DMChannel) and message.content.lower() == expected_code.lower()

        for i in range(3):
            try:
                response = await self.bot.wait_for('message', timeout=60.0, check=check)
                await self.send_and_delete(ctx, f"{response.author.mention} `is correct!`", delay=1)
                await self.give_points(response.author)
                await question_message.delete()
                break
            except asyncio.TimeoutError:
                await ctx.send(f"`Time's up! The answer was: {answer}`")
                break
        await question_message.delete()

    async def handle_multiple_choice_question(self, ctx: commands.Context):
        question = self.current_question['question']
        options = self.current_question['options']
        answer = self.current_question['answer']

        options_text = '\n'.join([f"{chr(ord('🇦') + i)} {option}" for i, option in enumerate(options)])
        question_message = await ctx.send(f"`Question: {question}\n\n{options_text}`")

        for i, option in enumerate(options):
            await question_message.add_reaction(chr(ord('🇦') + i))

        def check(reaction, user):
            return user != self.bot.user and reaction.message == question_message and str(reaction.emoji) in [chr(ord('🇦') + i) for i in range(len(options))]

        for i in range(3):
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                user_choice = chr(ord('🇦') + options.index(answer))
                if str(reaction.emoji) == user_choice:
                    self.answers.append(user.id)
                    await self.send_and_delete(ctx, f"{user.mention} `is correct!`", delay=1)
                    await self.give_points(user)
                    await question_message.clear_reactions()
                    if len(self.answers) == 3:
                        break
                else:
                    await self.send_and_delete(ctx, f"{user.mention} `is incorrect.`", delay=1)
            except asyncio.TimeoutError:
                await ctx.send(f"`Time's up! The answer was: {answer}`")
                break
        await question_message.delete()

    async def handle_direct_message_question(self, ctx: commands.Context):
        question = self.current_question['question']
        answer = self.current_question['answer']

        question_message = await ctx.send(f"`Question: {question}`\n`Submit your answer as a direct message (DM) to the bot.`")

        def check(message):
            return message.author != self.bot.user and isinstance(message.channel, discord.DMChannel) and message.content.lower() == answer.lower()

        try:
            response = await self.bot.wait_for('message', timeout=60.0, check=check)
            await self.send_and_delete(ctx, f"{response.author.mention} `is correct!`", delay=1)
            await self.give_points(response.author)
            await question_message.delete()
        except asyncio.TimeoutError:
            await ctx.send(f"`Time's up! The answer was: {answer}`")
        finally:
            await question_message.delete()

    async def give_points(self, member: discord.Member):
        try:
            database_cog = self.bot.get_cog('Database')
            if database_cog:
                db_cursor = database_cog.db_cursor
                async with database_cog.db_conn:
                    await db_cursor.execute("SELECT current_tier FROM Users WHERE user_id = ?", (member.id,))
                    current_tier = (await db_cursor.fetchone())[0]
                    points = self.tier_points[current_tier]
                    await db_cursor.execute("UPDATE Users SET points = points + ? WHERE user_id = ?", (points, member.id))
                    await self.bot.get_cog('Achievements').check_tier_progression(member.id)

                    achievement_cog = self.bot.get_cog('Achievements')
                    if achievement_cog:
                        for challenge_id, challenge_data in achievement_cog.challenges.items():
                            if challenge_data['tier_id'] == current_tier and challenge_data['points'] <= points:
                                await achievement_cog.handle_challenge_completion(None, member.id, challenge_data["name"])

                    logger.info(f"Quiz points awarded to {member.name} for Tier {current_tier}")
            else:
                logger.error("Database cog not found.")
        except Exception as e:
            logger.error(f"An unexpected error occurred in give_points: {e}", exc_info=True)

async def setup(bot):
    await bot.add_cog(Quiz(bot))
