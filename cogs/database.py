import discord
from discord.ext import commands
import asyncio
import logging
import sqlite3
from typing import Dict
from contextlib import asynccontextmanager
from helpers import send_and_delete
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.db_path = self.config['paths']['database_path']
        self.db_conn = None
        self.db_cursor = None
        self._init_database()

    def _init_database(self):
        try:
            if not os.path.exists(self.db_path):
                logger.info(f"Creating new database at {self.db_path}")
                self.db_conn = sqlite3.connect(self.db_path)
                self.db_cursor = self.db_conn.cursor()
                self._create_tables()
            else:
                logger.info(f"Connecting to existing database at {self.db_path}")
                self.db_conn = sqlite3.connect(self.db_path)
                self.db_cursor = self.db_conn.cursor()
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            self.db_conn = None
            self.db_cursor = None

    def _create_tables(self):
        try:
            # Create Users Table
            self.db_cursor.execute('''
                CREATE TABLE Users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    points INTEGER DEFAULT 0,
                    current_tier INTEGER DEFAULT 1,
                    joined_at DATETIME,
                    last_active DATETIME,
                    verified BOOLEAN DEFAULT FALSE,
                    muted_until DATETIME,
                    ban_reason TEXT,
                    warn_count INTEGER DEFAULT 0
                )
            ''')

            # Create ShodanScans Table
            self.db_cursor.execute('''
                CREATE TABLE ShodanScans (
                    scan_id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    target_ip TEXT,
                    status TEXT,
                    started_at DATETIME,
                    completed_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES Users(user_id)
                )
            ''')

            # Create QuizQuestions Table
            self.db_cursor.execute('''
                CREATE TABLE QuizQuestions (
                    question_id INTEGER PRIMARY KEY,
                    question TEXT,
                    answer TEXT,
                    type TEXT,
                    options TEXT,
                    difficulty INTEGER
                )
            ''')

            # Create QuizAnswers Table
            self.db_cursor.execute('''
                CREATE TABLE QuizAnswers (
                    answer_id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    question_id INTEGER,
                    answer_given TEXT,
                    correct BOOLEAN,
                    answered_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES Users(user_id),
                    FOREIGN KEY (question_id) REFERENCES QuizQuestions(question_id)
                )
            ''')

            # Create Logs Table
            self.db_cursor.execute('''
                CREATE TABLE Logs (
                    log_id INTEGER PRIMARY KEY,
                    message TEXT,
                    timestamp DATETIME
                )
            ''')

            # Create LogPrivacyCommands Table
            self.db_cursor.execute('''
                CREATE TABLE LogPrivacyCommands (
                    log_id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    command TEXT,
                    timestamp DATETIME
                )
            ''')

            # Create Roles Table
            self.db_cursor.execute('''
                CREATE TABLE Roles (
                    role_id INTEGER PRIMARY KEY,
                    name TEXT
                )
            ''')

            # Create UserRoles Table
            self.db_cursor.execute('''
                CREATE TABLE UserRoles (
                    user_id INTEGER,
                    role_id INTEGER,
                    assigned_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES Users(user_id),
                    FOREIGN KEY (role_id) REFERENCES Roles(role_id)
                )
            ''')

            # Create Executables Table for the Builder
            self.db_cursor.execute('''
                CREATE TABLE Executables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    filename TEXT,
                    version TEXT,
                    properties TEXT,
                    created_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES Users(user_id)
                )
            ''')
            self.db_conn.commit()
            logger.info("Database tables created successfully.")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")

    @asynccontextmanager
    async def get_connection(self):
        try:
            yield self.db_conn, self.db_cursor
        except Exception as e:
            logger.error(f"Error getting database connection: {e}")
        finally:
            pass

    async def execute(self, query, params=None):
        try:
            if params:
                self.db_cursor.execute(query, params)
            else:
                self.db_cursor.execute(query)
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error executing database query: {e}")

    async def fetch(self, query, params=None):
        try:
            if params:
                self.db_cursor.execute(query, params)
            else:
                self.db_cursor.execute(query)
            rows = self.db_cursor.fetchall()
            return rows
        except Exception as e:
            logger.error(f"Error fetching database data: {e}")

    async def fetch_one(self, query, params=None):
        try:
            if params:
                self.db_cursor.execute(query, params)
            else:
                self.db_cursor.execute(query)
            row = self.db_cursor.fetchone()
            return row
        except Exception as e:
            logger.error(f"Error fetching database data: {e}")

    @commands.command(name='adduser', help='Adds a test user to the database.')
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def add_user(self, ctx, user_id: int, username: str):
        try:
            await self.execute(
                "INSERT OR IGNORE INTO Users (user_id, username, joined_at) VALUES (?, ?, ?)",
                (user_id, username, datetime.now())
            )
            await send_and_delete(ctx, f"`User '{username}' added to the database.`", delay=self.bot.config['settings']['delete_response_delay'])
        except Exception as e:
            logger.error(f"Error adding user to database: {e}")
            await send_and_delete(ctx, "`An error occurred while adding the user.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')

    @commands.command(name='getuser', help='Retrieves information about a user from the database.')
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def get_user(self, ctx, user_id: int):
        try:
            user_data = await self.fetch("SELECT * FROM Users WHERE user_id = ?", (user_id,))
            if user_data:
                user = user_data[0]
                await send_and_delete(ctx, f"```\nuser_id: {user[0]}\nusername: {user[1]}\npoints: {user[2]}\ncurrent_tier: {user[3]}\njoined_at: {user[4]}\nlast_active: {user[5]}\nverified: {user[6]}\nmuted_until: {user[7]}\nbanned: {user[8]}\nwarn_count: {user[9]}\n```", delay=self.bot.config['settings']['delete_response_delay'])
            else:
                await send_and_delete(ctx, f"`User with ID {user_id} not found in the database.`", delay=self.bot.config['settings']['delete_response_delay'])
        except Exception as e:
            logger.error(f"Error retrieving user from database: {e}")
            await send_and_delete(ctx, "`An error occurred while retrieving the user.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')

    @commands.command(name='updateuserpoints', help='Updates the points for a user in the database.')
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def update_user_points(self, ctx, user_id: int, points: int):
        try:
            await self.execute(
                "UPDATE Users SET points = ? WHERE user_id = ?",
                (points, user_id)
            )
            await send_and_delete(ctx, f"`Points for user with ID {user_id} updated to {points}.`", delay=self.bot.config['settings']['delete_response_delay'])
        except Exception as e:
            logger.error(f"Error updating user points: {e}")
            await send_and_delete(ctx, "`An error occurred while updating user points.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')

    @commands.command(name='updateusertier', help='Updates the tier for a user in the database.')
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def update_user_tier(self, ctx, user_id: int, tier: int):
        try:
            await self.execute(
                "UPDATE Users SET current_tier = ? WHERE user_id = ?",
                (tier, user_id)
            )
            await send_and_delete(ctx, f"`Tier for user with ID {user_id} updated to {tier}.`", delay=self.bot.config['settings']['delete_response_delay'])
        except Exception as e:
            logger.error(f"Error updating user tier: {e}")
            await send_and_delete(ctx, "`An error occurred while updating user tier.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')

    @commands.command(name='updateuserverified', help='Updates the verified status for a user in the database.')
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def update_user_verified(self, ctx, user_id: int, verified: bool):
        try:
            await self.execute(
                "UPDATE Users SET verified = ? WHERE user_id = ?",
                (verified, user_id)
            )
            await send_and_delete(ctx, f"`Verified status for user with ID {user_id} updated to {verified}.`", delay=self.bot.config['settings']['delete_response_delay'])
        except Exception as e:
            logger.error(f"Error updating user verified status: {e}")
            await send_and_delete(ctx, "`An error occurred while updating user verified status.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')

    @commands.command(name='updateusermuteduntil', help='Updates the muted_until timestamp for a user in the database.')
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def update_user_muted_until(self, ctx, user_id: int, muted_until_timestamp: str):
        try:
            muted_until = datetime.strptime(muted_until_timestamp, "%Y-%m-%d %H:%M:%S")
            await self.execute(
                "UPDATE Users SET muted_until = ? WHERE user_id = ?",
                (muted_until, user_id)
            )
            await send_and_delete(ctx, f"`Muted until timestamp for user with ID {user_id} updated to {muted_until_timestamp}.`", delay=self.bot.config['settings']['delete_response_delay'])
        except Exception as e:
            logger.error(f"Error updating user muted until timestamp: {e}")
            await send_and_delete(ctx, "`An error occurred while updating user muted until timestamp.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')

    @commands.command(name='updateuserbanreason', help='Updates the ban reason for a user in the database.')
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def update_user_ban_reason(self, ctx, user_id: int, ban_reason: str):
        try:
            await self.execute(
                "UPDATE Users SET ban_reason = ? WHERE user_id = ?",
                (ban_reason, user_id)
            )
            await send_and_delete(ctx, f"`Ban reason for user with ID {user_id} updated to {ban_reason}.`", delay=self.bot.config['settings']['delete_response_delay'])
        except Exception as e:
            logger.error(f"Error updating user ban reason: {e}")
            await send_and_delete(ctx, "`An error occurred while updating user ban reason.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')

    @commands.command(name='updateuserwarncount', help='Updates the warn count for a user in the database.')
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def update_user_warn_count(self, ctx, user_id: int, warn_count: int):
        try:
            await self.execute(
                "UPDATE Users SET warn_count = ? WHERE user_id = ?",
                (warn_count, user_id)
            )
            await send_and_delete(ctx, f"`Warn count for user with ID {user_id} updated to {warn_count}.`", delay=self.bot.config['settings']['delete_response_delay'])
        except Exception as e:
            logger.error(f"Error updating user warn count: {e}")
            await send_and_delete(ctx, "`An error occurred while updating user warn count.`", delay=self.bot.config['settings']['delete_errors_delay'], delete_type='error')

async def setup(bot):
    await bot.add_cog(Database(bot))
