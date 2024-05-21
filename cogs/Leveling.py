import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import asyncio

class LevelingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.create_tables())
        self.cooldowns = {}  # Track user cooldowns

    async def create_tables(self):
        async with aiosqlite.connect('leveling.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_levels (
                    user_id INTEGER,
                    guild_id INTEGER,
                    level INTEGER DEFAULT 1,
                    xp INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, guild_id)
                )
            ''')
            await db.commit()

    async def add_experience(self, user_id, guild_id, xp):
        try:
            async with aiosqlite.connect('leveling.db') as db:
                await db.execute('''
                    INSERT INTO user_levels (user_id, guild_id, xp)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_id, guild_id) DO UPDATE
                    SET xp = xp + ?
                ''', (user_id, guild_id, xp, xp))
                await db.commit()
        except Exception as e:
            print(f"An error occurred while adding experience: {e}")

    async def check_level_up(self, user_id, guild_id):
        async with aiosqlite.connect('leveling.db') as db:
            async with db.execute('SELECT xp, level FROM user_levels WHERE user_id = ? AND guild_id = ?', (user_id, guild_id)) as cursor:
                row = await cursor.fetchone()
                if row:
                    xp, level = row
                    if xp >= (level * 100):  # You can adjust the XP requirement for leveling up
                        await db.execute('UPDATE user_levels SET level = ?, xp = ? WHERE user_id = ? AND guild_id = ?', (level + 1, 0, user_id, guild_id))
                        await db.commit()
                        return True
        return False

    async def gain_experience(self, message):
        user_id = message.author.id
        guild_id = message.guild.id

        # Check if the user has a profile, if not, add them to the database with level 1
        async with aiosqlite.connect('leveling.db') as db:
            async with db.execute('SELECT user_id FROM user_levels WHERE user_id = ? AND guild_id = ?', (user_id, guild_id)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    await db.execute('INSERT INTO user_levels (user_id, guild_id) VALUES (?, ?)', (user_id, guild_id))
                    await db.commit()
                    await message.channel.send(f"Welcome {message.author.mention} to the leveling system! You've been added at level 1.")

        if user_id not in self.cooldowns or (user_id in self.cooldowns and (message.created_at - self.cooldowns[user_id]).total_seconds() > 60):  # 60 seconds cooldown
            await self.add_experience(user_id, guild_id, 10)  # Adjust XP gain as needed
            self.cooldowns[user_id] = message.created_at
            print(self.cooldowns)
            if await self.check_level_up(user_id, guild_id):
                await message.channel.send(f'Congratulations {message.author.mention}, you leveled up!')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        await self.gain_experience(message)

    @app_commands.command(name="profile", description="View your leveling profile")
    @app_commands.guild_only()
    async def profile(self, interaction: discord.Interaction):
        user_id = interaction.author.id
        guild_id = interaction.guild.id
        async with aiosqlite.connect('leveling.db') as db:
            async with db.execute('SELECT level, xp FROM user_levels WHERE user_id = ? AND guild_id = ?', (user_id, guild_id)) as cursor:
                row = await cursor.fetchone()
                if row:
                    level, xp = row
                    await interaction.response.send_message(content=f'**Level:** {level}\n**XP:** {xp}', ephemeral=True)
                else:
                    await interaction.response.send_message(content="You haven't gained any experience yet!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(LevelingCog(bot))