import discord
from discord import utils
from discord.ext import commands
import logging
import sqlite3
from typing import Dict
import os
from datetime import datetime
from helpers import send_and_delete, create_embed  # type: ignore

logger = logging.getLogger(__name__)

class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.db_path = self.config['paths']['database_path']
        self.db_conn = None
        self.db_cursor = None
        self.delete_commands = self.bot.config['settings']['delete_commands']
        self.delete_command_delay = self.bot.config['settings']['delete_command_delay']
        self.delete_responses = self.bot.config['settings']['delete_responses']
        self.delete_response_delay = self.bot.config['settings']['delete_response_delay']
        self.delete_errors = self.bot.config['settings']['delete_errors']
        self.delete_errors_delay = self.bot.config['settings']['delete_errors_delay']
        self.existing_tables = []

        self._init_database()

    def _init_database(self):
        try:
            self.db_conn = sqlite3.connect(self.db_path)
            self.db_cursor = self.db_conn.cursor()

            self._create_tables()

            logger.info(f"Database initialized: {self.db_path}")

            initial_tiers = self.config.get('tiers', [])
            for tier in initial_tiers:
                self.db_cursor.execute(
                    "INSERT OR IGNORE INTO Tiers (tier_id, name, role_name, required_points) VALUES (?, ?, ?, ?)",
                    (tier['tier_id'], tier['name'], tier['role_name'], tier['required_points'])
                )
            self.db_conn.commit()

        except Exception as e:
            logger.error(f"Error initializing database: {e}", exc_info=True)

    def _create_tables(self):
        self.db_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        self.existing_tables = [row[0] for row in self.db_cursor.fetchall()]

        if 'Users' not in self.existing_tables:
            try:
                # Create Users Table
                self.db_cursor.execute('''
                    CREATE TABLE Users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT NOT NULL DEFAULT 'n/a',
                        points INTEGER DEFAULT 0,
                        current_tier INTEGER DEFAULT 1,
                        correct_quiz_answers INTEGER DEFAULT 0,
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        verified BOOLEAN DEFAULT FALSE,
                        muted_until TIMESTAMP,
                        ban_reason TEXT DEFAULT 'n/a',
                        warn_count INTEGER DEFAULT 0
                    )
                ''')
                self.db_cursor.execute("CREATE INDEX idx_user_id ON Users (user_id)")
            except Exception as e:
                logger.error(f"Error creating Users table: {e}")

        if 'QuizQuestions' not in self.existing_tables:
            try:
                # Create QuizQuestions Table
                self.db_cursor.execute('''
                    CREATE TABLE QuizQuestions (
                        question_id INTEGER PRIMARY KEY,
                        question TEXT DEFAULT 'n/a',
                        answer TEXT DEFAULT 'n/a',
                        type TEXT DEFAULT 'n/a',
                        options TEXT DEFAULT 'n/a'
                    )
                ''')
                self.db_cursor.execute("CREATE INDEX idx_question_id ON QuizQuestions (question_id)")
            except Exception as e:
                logger.error(f"Error creating QuizQuestions table: {e}")

        if 'QuizAnswers' not in self.existing_tables:
            try:
                # Create QuizAnswers Table
                self.db_cursor.execute('''
                    CREATE TABLE QuizAnswers (
                        answer_id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        question_id INTEGER,
                        answer_given TEXT DEFAULT 'n/a',
                        correct BOOLEAN,
                        answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES Users(user_id),
                        FOREIGN KEY (question_id) REFERENCES QuizQuestions(question_id)
                    )
                ''')
                self.db_cursor.execute("CREATE INDEX idx_answer_id ON QuizAnswers (answer_id)")
                self.db_cursor.execute("CREATE INDEX idx_user_id_answers ON QuizAnswers (user_id)")
                self.db_cursor.execute("CREATE INDEX idx_question_id_answers ON QuizAnswers (question_id)")
            except Exception as e:
                logger.error(f"Error creating QuizAnswers table: {e}")

        if 'Logs' not in self.existing_tables:
            try:
                # Create Logs Table
                self.db_cursor.execute('''
                    CREATE TABLE Logs (
                        log_id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        channel TEXT DEFAULT 'n/a',
                        command TEXT DEFAULT 'n/a',
                        message TEXT DEFAULT 'n/a',
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                self.db_cursor.execute("CREATE INDEX idx_log_id ON Logs (log_id)")
            except Exception as e:
                logger.error(f"Error creating Logs table: {e}")

        if 'Roles' not in self.existing_tables:
            try:
                # Create Roles Table
                self.db_cursor.execute('''
                    CREATE TABLE Roles (
                        role_id INTEGER PRIMARY KEY,
                        name TEXT DEFAULT 'n/a'
                    )
                ''')
                self.db_cursor.execute("CREATE INDEX idx_role_id ON Roles (role_id)")
            except Exception as e:
                logger.error(f"Error creating Roles table: {e}")

        if 'UserRoles' not in self.existing_tables:
            try:
                # Create UserRoles Table
                self.db_cursor.execute('''
                    CREATE TABLE UserRoles (
                        user_id INTEGER,
                        role_id INTEGER,
                        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES Users(user_id),
                        FOREIGN KEY (role_id) REFERENCES Roles(role_id)
                    )
                ''')
                self.db_cursor.execute("CREATE INDEX idx_user_id_roles ON UserRoles (user_id)")
                self.db_cursor.execute("CREATE INDEX idx_role_id_roles ON UserRoles (role_id)")
            except Exception as e:
                logger.error(f"Error creating UserRoles table: {e}")

        if 'ChatLogs' not in self.existing_tables:
            try:
                # Create ChatLogs Table
                self.db_cursor.execute('''
                    CREATE TABLE ChatLogs (
                        log_id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        message TEXT DEFAULT 'n/a',
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES Users(user_id)
                    )
                ''')
                self.db_cursor.execute("CREATE INDEX idx_log_id_chat ON ChatLogs (log_id)")
                self.db_cursor.execute("CREATE INDEX idx_user_id_chat ON ChatLogs (user_id)")
            except Exception as e:
                logger.error(f"Error creating ChatLogs table: {e}")

        if 'Tiers' not in self.existing_tables:
            try:
                # Create Tiers Table
                self.db_cursor.execute('''
                    CREATE TABLE Tiers (
                        tier_id INTEGER PRIMARY KEY,
                        name TEXT DEFAULT 'n/a',
                        role_name TEXT DEFAULT 'n/a',
                        required_points INTEGER DEFAULT 0
                    )
                ''')
                self.db_cursor.execute("CREATE INDEX idx_tier_id ON Tiers (tier_id)")
            except Exception as e:
                logger.error(f"Error creating Tiers table: {e}")

    # --- Database Helpers ---

    async def execute(self, query, params=None):
        try:
            if self.db_conn is None:
                logger.error("Database connection is not initialized.")
                return
            if params:
                self.db_cursor.execute(query, params)
            else:
                self.db_cursor.execute(query)
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error executing database query: {e}", exc_info=True)

    async def fetch(self, query, params=None):
        try:
            if self.db_conn is None:
                logger.error("Database connection is not initialized.")
                return
            if params:
                self.db_cursor.execute(query, params)
            else:
                self.db_cursor.execute(query)
            rows = self.db_cursor.fetchall()
            return rows
        except Exception as e:
            logger.error(f"Error fetching database data: {e}", exc_info=True)

    async def fetch_one(self, query, params=None):
        try:
            if self.db_conn is None:
                logger.error("Database connection is not initialized.")
                return
            if params:
                self.db_cursor.execute(query, params)
            else:
                self.db_cursor.execute(query)
            row = self.db_cursor.fetchone()
            return row
        except Exception as e:
            logger.error(f"Error fetching database data: {e}", exc_info=True)

    async def get_all_tiers(self):
        return await self.fetch("SELECT * FROM Tiers ORDER BY required_points")

    async def get_tier_by_id(self, tier_id: int):
        return await self.fetch_one("SELECT * FROM Tiers WHERE tier_id = ?", (tier_id,))

    async def get_tier_by_points(self, points: int):
        return await self.fetch_one("SELECT * FROM Tiers WHERE required_points <= ? ORDER BY required_points DESC LIMIT 1", (points,))

    # --- Commands ---

    @commands.command(name='allusers', help='Displays the total number of users in the database.')
    @commands.is_owner()
    async def get_all_users(self, ctx):
        try:
            user_count = await self.fetch_one("SELECT COUNT(*) FROM Users")
            if user_count:
                await ctx.send(f"`{user_count[0]} Users`")
            else:
                await ctx.send("`No users found in the database.`")
        except Exception as e:
            logger.error(f"Error retrieving user count: {e}", exc_info=True)
            await ctx.send("`An error occurred while retrieving the user count.`")

    @commands.command(name='adduser', help='Adds a test user to the database.')
    @commands.is_owner()
    async def add_user(self, ctx, user_id: int, username: str):
        try:
            await self.execute(
                "INSERT OR IGNORE INTO Users (user_id, username, joined_at) VALUES (?, ?, ?)",
                (user_id, username, datetime.now())
            )
            embed = create_embed(title='Database Action',
                                  description=f"`User '{username}' added to the database.`",
                                  color_key='primary',
                                  config=self.bot.config
                                  )
            await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)
            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

        except Exception as e:
            logger.error(f"Error adding user to database: {e}", exc_info=True)
            await send_and_delete(ctx, content="`An error occurred while adding the user.`", delay=self.delete_errors_delay, delete_type='error')

    @add_user.error
    async def add_user_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(ctx,
                                content=f"`This command is on cooldown. Please try again in {retry_after:.2f} seconds.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again later.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

    async def add_new_user(self, user_id: int, username: str):
        try:
            await self.execute(
                "INSERT OR IGNORE INTO Users (user_id, username, joined_at, current_tier, last_active) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, datetime.now(), 1, datetime.now())
            )
            logger.info(f"New user added to the database: {username} (ID: {user_id})")
        except Exception as e:
            logger.error(f"Error adding new user to database: {e}", exc_info=True)

    @commands.command(name='getuser', help='Retrieves information about a user from the database.')
    @commands.is_owner()
    async def get_user(self, ctx, user_id: int):
        try:
            user_data = await self.fetch("SELECT * FROM Users WHERE user_id = ?", (user_id,))
            if user_data:
                user = user_data[0]

                total_commands_run = await self.fetch(
                    "SELECT COUNT(*) FROM Logs WHERE user_id = ?", (user_id,)
                )
                total_commands_run = total_commands_run[0][0] if total_commands_run else 0

                correct_quiz_answers = user[10]

                total_commands_run = await self.fetch(
                    "SELECT COUNT(*) FROM Logs WHERE user_id = ?", (user_id,)
                )
                total_commands_run = total_commands_run[0][0] if total_commands_run else 0

                correct_quiz_answers = user[4]

                response_text = f"""
 ```{user[1]} [{user[0]}]

Tier: {user[3]}
Points: {user[2]}
Questions: {correct_quiz_answers}

Warnings: {user[10]}
Muted: {user[8] is not None}
Bans: {user[9] is not None}

Commands: {total_commands_run}```
                """

                embed = create_embed(title=f" ",
                                      description=response_text,
                                      color_key='primary',
                                      config=self.bot.config
                                      )
                await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)

            else:
                await send_and_delete(ctx, content=f"`User with ID {user_id} not found.`",
                                      delay=self.delete_response_delay)

            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

        except Exception as e:
            logger.error(f"Error retrieving user from database: {e}", exc_info=True)
            await send_and_delete(ctx, content="`An error occurred while retrieving the user.`", delay=self.delete_errors_delay, delete_type='error')

    @get_user.error
    async def get_user_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(ctx,
                                content=f"`This command is on cooldown. Please try again in {retry_after:.2f} seconds.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again later.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

    @commands.command(name='userpoints', help='Updates the points for a user in the database.')
    @commands.is_owner()
    async def update_user_points(self, ctx, user_id: int, points: int):
        try:
            await self.execute(
                "UPDATE Users SET points = ? WHERE user_id = ?",
                (points, user_id)
            )
            embed = create_embed(title='Database Action',
                                  description=f"`Points for user with ID {user_id} updated to {points}.`",
                                  color_key='primary',
                                  config=self.bot.config
                                  )
            await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)
            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)

        except Exception as e:
            logger.error(f"Error updating user points: {e}", exc_info=True)
            await send_and_delete(ctx, content="`An error occurred while updating user points.`", delay=self.delete_errors_delay, delete_type='error')

    @update_user_points.error
    async def update_user_points_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(ctx,
                                content=f"`This command is on cooldown. Please try again in {retry_after:.2f} seconds.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again later.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

    @commands.command(name='usertier', help='Updates the tier for a user in the database.')
    @commands.is_owner()
    async def update_user_tier(self, ctx, user_id: int, tier: int):
        try:
            await self.execute(
                "UPDATE Users SET current_tier = ? WHERE user_id = ?",
                (tier, user_id)
            )
            embed = create_embed(title='Database Action',
                                  description=f"`Tier for user with ID {user_id} updated to {tier}.`",
                                  color_key='primary',
                                  config=self.bot.config
                                  )
            await send_and_delete(ctx, embed=embed, delay=self.delete_response_delay)
            if self.delete_commands:
                await ctx.message.delete(delay=self.delete_command_delay)
        except Exception as e:
            logger.error(f"Error updating user tier: {e}", exc_info=True)
            await send_and_delete(ctx, content="`An error occurred while updating user tier.`", delay=self.delete_errors_delay, delete_type='error')

    @update_user_tier.error
    async def update_user_tier_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await send_and_delete(ctx,
                                content=f"`This command is on cooldown. Please try again in {retry_after:.2f} seconds.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')
        else:
            logger.error(f"Unexpected error occurred: {error}", exc_info=True)
            await send_and_delete(ctx, content="`An unexpected error occurred. Please try again later.`",
                                delay=self.bot.config['settings']['delete_errors_delay'],
                                delete_type='error')

def setup(bot):
    bot.add_cog(Database(bot))
