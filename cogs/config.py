import discord
from discord import app_commands
from discord.ext import commands

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_welcome", description="Cài đặt kênh chào mừng")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_welcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.db.execute(
            "INSERT INTO server_configs (guild_id, welcome_channel_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET welcome_channel_id = excluded.welcome_channel_id",
            (interaction.guild_id, channel.id)
        )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ Đã lưu kênh chào mừng: {channel.mention}")

    @app_commands.command(name="setup_cf", description="Cài đặt kênh confession")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_cf(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.db.execute(
            "INSERT INTO server_configs (guild_id, confession_channel_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET confession_channel_id = excluded.confession_channel_id",
            (interaction.guild_id, channel.id)
        )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ Đã lưu kênh confession: {channel.mention}")

    # Lệnh mới thêm vào cho Twitter
    @app_commands.command(name="setup_twitter", description="Cài đặt kênh nhận thông báo Twitter")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_twitter(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.db.execute(
            "INSERT INTO server_configs (guild_id, twitter_channel_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET twitter_channel_id = excluded.twitter_channel_id",
            (interaction.guild_id, channel.id)
        )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ Đã lưu kênh nhận thông báo Twitter: {channel.mention}")

async def setup(bot):
    await bot.add_cog(Config(bot))