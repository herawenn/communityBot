import discord
import asyncio
import random
from discord.ext import commands, tasks
import logging
import json
import datetime
from helpers import send_and_delete, create_embed  # type: ignore

logger = logging.getLogger(__name__)

class Quiz(commands.Cog):
    def __init__(self, bot: commands.Bot):
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
        self.question_message = None
        self.active_quiz = False
        self.answers = {}
        self.delete_responses = self.bot.config['settings']['delete_responses']
        self.delete_response_delay = self.bot.config['settings']['delete_response_delay']
        self.delete_errors = self.bot.config['settings']['delete_errors']
        self.delete_errors_delay = self.bot.config['settings']['delete_errors_delay']
        self.delete_commands = self.bot.config['settings']['delete_commands']
        self.delete_command_delay = self.bot.config['settings']['delete_command_delay']
        self.db = self.bot.get_cog('Database')
        if self.bot.config['features']['quiz']:
            self.quiz_task.start()

    def load_questions(self) -> list:
        try:
            with open('files/json/questions.json', 'r') as f:
                questions_data = json.load(f)
                questions = questions_data.get('Questions', [])
                return questions
        except FileNotFoundError:
            logger.error("Question file not found. Please create 'files/json/questions.json'.")
            return []
        except json.JSONDecodeError:
            logger.error("Invalid JSON format in the question file.")
            return []

    @commands.command(name="quiz", help="Start a cybersecurity quiz.")
    @commands.is_owner()
    async def start_quiz(self, ctx: commands.Context):
        try:
            if self.active_quiz:
                await send_and_delete(ctx, content="`A quiz is already in progress.`", delay=self.delete_response_delay)
                return

            self.active_quiz = True
            self.answers = {}
            if self.delete_commands and ctx.message:
                await ctx.message.delete(delay=self.delete_command_delay)
            await self.ask_question(ctx)

        except Exception as e:
            logger.error(f"An unexpected error occurred in start_quiz: {e}", exc_info=True)
            await send_and_delete(ctx, content="An error occurred while starting the quiz. Please try again later.",
                                  delay=self.delete_errors_delay, delete_type='error')
            self.active_quiz = False

    async def ask_question(self, ctx: commands.Context):
        self.current_question = random.choice(self.questions)
        question_type = self.current_question.get('Type', 'Multiple Choice')

        if question_type == 'Multiple Choice':
            await self.handle_multiple_choice_question(ctx)
        elif question_type == 'Fill in the Blank':
            await self.handle_fill_in_the_blank_question(ctx)
        elif question_type == 'True/False':
            await self.handle_true_false_question(ctx)
        else:
            logger.error(f"Invalid question type: {question_type}")
            await self.start_quiz(ctx)

    async def handle_multiple_choice_question(self, ctx: commands.Context):
        question = self.current_question.get('Question', '')
        if not question:
            logger.error("Question is empty. Skipping this question.")
            await self.start_quiz(ctx)
            return

        options = self.current_question.get('Options', [])
        if not options:
            logger.error("Options are empty. Skipping this question.")
            await self.start_quiz(ctx)
            return

        answer = self.current_question.get('Correct_Answer', '')
        if not answer:
            logger.error("Correct answer is empty. Skipping this question.")
            await self.start_quiz(ctx)
            return

        random.shuffle(options)

        options_text = '\n'.join([f"{chr(ord('🇦') + i)} {option}" for i, option in enumerate(options)])
        self.question_message = await ctx.send(f"Question: {question}\n\n{options_text}")

        for i, option in enumerate(options):
            await self.question_message.add_reaction(chr(ord('🇦') + i))

        def check(reaction: discord.Reaction, user: discord.User):
            return user != self.bot.user and reaction.message == self.question_message and str(
                reaction.emoji) in [chr(ord('🇦') + i) for i in range(len(options))]

        correct_answers = 0
        for i in range(3):
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                user_choice = chr(ord('🇦') + options.index(answer))
                if str(reaction.emoji) == user_choice and user.id not in self.answers:
                    self.answers[user.id] = True
                    await send_and_delete(ctx, content=f"{user.mention} is correct!", delay=self.delete_response_delay)
                    await self.give_points(user)
                    await self.question_message.clear_reactions()
                    correct_answers += 1
                    if correct_answers == 3:
                        break
                else:
                    await send_and_delete(ctx,
                                          content=f"{user.mention} has already answered or is incorrect.",
                                          delay=self.delete_response_delay)
            except asyncio.TimeoutError:
                if correct_answers == 0:
                    await ctx.send(f"Time's up! The answer was: {answer}")
                break

        await self.question_message.delete()
        self.question_message = None
        self.active_quiz = False

    async def handle_true_false_question(self, ctx: commands.Context):
        question = self.current_question.get('Question', '')
        answer = self.current_question.get('Correct_Answer', '').lower()

        if not question or answer not in ['true', 'false']:
            logger.error("Invalid True/False question format. Skipping.")
            await self.start_quiz(ctx)
            return

        embed = create_embed(title="Cybersecurity Quiz",
                              color_key='primary',
                              fields=[("Question", question, False)],
                              config=self.bot.config
                              )
        self.question_message = await ctx.send(embed=embed)

        await self.question_message.add_reaction('✅')
        await self.question_message.add_reaction('❌')

        def check(reaction: discord.Reaction, user: discord.User):
            return user != self.bot.user and reaction.message == self.question_message and str(
                reaction.emoji) in ['✅', '❌']

        correct_answers = 0
        for i in range(3):
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)

                if (str(reaction.emoji) == '✅' and answer == 'true') or (
                        str(reaction.emoji) == '❌' and answer == 'false') and user.id not in self.answers:
                    self.answers[user.id] = True
                    await send_and_delete(ctx, content=f"{user.mention} is correct!", delay=self.delete_response_delay)
                    await self.give_points(user)
                    await self.question_message.clear_reactions()
                    correct_answers += 1
                    if correct_answers == 3:
                        break
                else:
                    await send_and_delete(ctx,
                                          content=f"{user.mention} has already answered or is incorrect.",
                                          delay=self.delete_response_delay)
            except asyncio.TimeoutError:
                if correct_answers == 0:
                    await ctx.send(f"Time's up! The answer was: {answer.capitalize()}")
                break

        await self.question_message.delete()
        self.question_message = None
        self.active_quiz = False


    async def handle_fill_in_the_blank_question(self, ctx: commands.Context):
        question = self.current_question.get('Question', '')
        answer = self.current_question.get('Correct_Answer', '').lower()

        if not question or not answer:
            logger.error("Invalid Fill in the Blank question format. Skipping.")
            await self.start_quiz(ctx)
            return

        embed = create_embed(title="Cybersecurity Quiz",
                              color_key='primary',
                              fields=[("Question", question, False)],
                              config=self.bot.config
                              )
        self.question_message = await ctx.send(embed=embed)

        def check(message: discord.Message):
            return message.author != self.bot.user and message.channel == ctx.channel

        correct_answers = 0
        for i in range(3):
            try:
                user_message = await self.bot.wait_for('message', timeout=30.0, check=check)
                user_answer = user_message.content.strip().lower()

                if user_answer == answer and user_message.author.id not in self.answers:
                    self.answers[user_message.author.id] = True
                    await send_and_delete(ctx, content=f"{user_message.author.mention} is correct!",
                                          delay=self.delete_response_delay)
                    await self.give_points(user_message.author)
                    correct_answers += 1
                    if correct_answers == 3:
                        break
                else:
                    await send_and_delete(ctx,
                                          content=f"{user_message.author.mention} has already answered or is incorrect.",
                                          delay=self.delete_response_delay)

            except asyncio.TimeoutError:
                if correct_answers == 0:
                    await ctx.send(f"Time's up! The answer was: {answer}")
                break

        await self.question_message.delete()
        self.question_message = None
        self.active_quiz = False

    async def give_points(self, member: discord.Member):
        try:
            database_cog = self.bot.get_cog('Database')
            if database_cog:
                with database_cog.db_conn:
                    db_cursor = database_cog.db_cursor
                    db_cursor.execute("SELECT current_tier, points FROM Users WHERE user_id = ?", (member.id,))
                    row = db_cursor.fetchone()
                    if row:
                        current_tier, points = row
                        points += self.tier_points[current_tier]
                        db_cursor.execute("UPDATE Users SET points = ? WHERE user_id = ?", (points, member.id))
                        logger.info(f"Quiz points awarded to {member.name} for Tier {current_tier}")
                    else:
                        logger.error(f"User with ID {member.id} not found in the database.")
            else:
                logger.error("Database cog not found.")

            await self.update_user_quiz_stats(member.id)

        except Exception as e:
            logger.error(f"An unexpected error occurred in give_points: {e}", exc_info=True)

    async def update_user_quiz_stats(self, user_id: int):
        try:
            await self.db.execute(
                "UPDATE Users SET correct_quiz_answers = correct_quiz_answers + 1 WHERE user_id = ?",
                (user_id,)
            )
        except Exception as e:
            logger.error(f"Error updating user quiz stats: {e}", exc_info=True)

    @commands.command(name='leaderboard', help="Displays the quiz leaderboard.")
    @commands.cooldown(1, 30, commands.BucketType.channel)
    async def leaderboard(self, ctx: commands.Context):
        try:
            top_users = await self.db.fetch(
                "SELECT username, correct_quiz_answers FROM Users ORDER BY correct_quiz_answers DESC LIMIT 5"
            )

            if not top_users:
                await send_and_delete(ctx, content="`No quiz answers recorded yet.`", delay=self.delete_response_delay)
                return

            embed = create_embed(title="Points Leaderboard",
                                  description="",
                                  color_key='primary',
                                  config=self.bot.config
                                  )
            for i, user in enumerate(top_users):
                embed.add_field(name=f"{i+1}. {user[0]}", value=f"`{user[1]} Correct Answers`", inline=False)
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error displaying leaderboard: {e}")
            await ctx.send(f"`An error occurred while displaying the leaderboard.`")

    @tasks.loop(hours=12)
    async def quiz_task(self):
        try:
            if not self.bot.config['features']['quiz']:
                return
            channel_id = int(self.bot.config['identifiers']['quiz_channel_id'])
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.error("Invalid quiz channel ID in config.json.")
                return
            await self.start_quiz(channel)
        except Exception as e:
            logger.error(f"An error occurred in the quiz task: {e}", exc_info=True)

    @quiz_task.before_loop
    async def before_quiz_task(self):
        await self.bot.wait_until_ready()
        now = datetime.datetime.now()
        next_run = now.replace(hour=12, minute=0, second=0, microsecond=0)
        if next_run < now:
            next_run += datetime.timedelta(days=1)
        await asyncio.sleep((next_run - now).total_seconds())

def setup(bot: commands.Bot):
    bot.add_cog(Quiz(bot))
