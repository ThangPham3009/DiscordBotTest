import discord
from discord import app_commands
from discord.ext import commands

class Twitter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="twitter_add", description="[Admin] Thêm tài khoản theo dõi")
    @app_commands.checks.has_permissions(administrator=True)
    async def twitter_add(self, interaction: discord.Interaction, username: str):
        await self.bot.db.execute("INSERT INTO twitter_feeds (guild_id, twitter_user) VALUES (?, ?)", (interaction.guild_id, username))
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ Đã thêm @{username}")

    @app_commands.command(name="twitter_list", description="Xem danh sách đang theo dõi")
    async def twitter_list(self, interaction: discord.Interaction):
        async with self.bot.db.execute("SELECT twitter_user FROM twitter_feeds WHERE guild_id = ?", (interaction.guild_id,)) as cursor:
            rows = await cursor.fetchall()
        if rows:
            list_str = "\n".join([f"- @{r[0]}" for r in rows])
            await interaction.response.send_message(f"📋 **Danh sách theo dõi:**\n{list_str}")
        else:
            await interaction.response.send_message("Empty list.")

async def setup(bot):
    await bot.add_cog(Twitter(bot))