import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.db = await aiosqlite.connect('moderation.db')
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS bans (
                user_id INTEGER PRIMARY KEY,
                reason TEXT
            )
        ''')
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS profanity (
                word TEXT PRIMARY KEY
            )
        ''')
        await self.db.commit()

    async def cog_unload(self):
        await self.db.close()

    @app_commands.command(name="ban", description="Ban a user from the server.")
    @app_commands.guild_only()
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.User, reason: str):
        await interaction.guild.ban(user, reason=reason)
        await self.db.execute('INSERT INTO bans (user_id, reason) VALUES (?, ?)', (user.id, reason))
        await self.db.commit()
        await interaction.response.send_message(f'Banned {user} for: {reason}')

    @app_commands.command(name="unban", description="Unban a user")
    @app_commands.guild_only()
    @app_commands.default_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: int):
        user = await self.bot.fetch_user(user_id)
        await interaction.guild.unban(user)
        async with aiosqlite.connect('moderation.db') as db:
            await db.execute('DELETE FROM bans WHERE user_id = ?', (user_id,))
            await db.commit()
        await interaction.response.send_message(f'{user} has been unbanned', ephemeral=True)

    @app_commands.command(name="add_profanity", description="Add a word to the profanity filter.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    async def add_profanity(self, interaction: discord.Interaction, word: str):
        cursor = await self.db.execute('SELECT word FROM profanity')
        rows = await cursor.fetchall()
        profanity_words = [row[0] for row in rows]
        if word in profanity_words:
            await interaction.response.send_message(f"{word} already in list")
            return
        await self.db.execute('INSERT INTO profanity (word) VALUES (?)', (word.lower(),))
        await self.db.commit()
        await interaction.response.send_message(f'Added "{word}" to the profanity filter.')

    @app_commands.command(name="remove_profanity", description="Remove a word from the profanity filter.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    async def remove_profanity(self, interaction: discord.Interaction, word: str):
        await self.db.execute('DELETE FROM profanity WHERE word = ?', (word.lower(),))
        await self.db.commit()
        await interaction.response.send_message(f'Removed "{word}" from the profanity filter.')

    @app_commands.command(name="assign_role", description="Assign a role to a user")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_roles=True)
    async def assign_role(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        await member.add_roles(role)
        async with aiosqlite.connect('moderation.db') as db:
            await db.execute('INSERT OR IGNORE INTO role_assignments (guild_id, role_id) VALUES (?, ?)',
                             (member.guild.id, role.id))
            await db.commit()
        await interaction.response.send_message(f'Role {role.name} assigned to {member}', ephemeral=True)

    @app_commands.command(name="remove_role", description="Remove a role from a user")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_roles=True)
    async def remove_role(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        await member.remove_roles(role)
        async with aiosqlite.connect('moderation.db') as db:
            await db.execute('DELETE FROM role_assignments WHERE guild_id = ? AND role_id = ?',
                             (member.guild.id, role.id))
            await db.commit()
        await interaction.response.send_message(f'Role {role.name} removed from {member}', ephemeral=True)

    @app_commands.command(name="list_roles", description="List all roles")
    @app_commands.guild_only()
    async def list_roles(self, interaction: discord.Interaction):
        roles = [role.name for role in interaction.guild.roles]
        await interaction.response.send_message("\n".join(roles), ephemeral=True)

    # @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        cursor = await self.db.execute('SELECT word FROM profanity')
        rows = await cursor.fetchall()
        profanity_words = [row[0] for row in rows]
        if any(word in message.content.lower() for word in profanity_words):
            await message.delete()
            await message.channel.send(f'{message.author.mention}, your message contained inappropriate language and was removed.')

async def setup(bot):
    await bot.add_cog(Moderation(bot))