import discord
from discord import app_commands
from discord.ext import commands

class Confession(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="cf", description="Gửi lời thú nhận ẩn danh")
    @app_commands.describe(content="Nội dung lời thú nhận")
    async def cf(self, interaction: discord.Interaction, content: str):
        await interaction.response.defer(ephemeral=True) # Tránh bị timeout

        async with self.bot.db.execute(
            "SELECT confession_channel_id FROM server_configs WHERE guild_id = ?",
            (interaction.guild_id,)
        ) as cursor:
            result = await cursor.fetchone()

        if result and result[0]:
            channel = self.bot.get_channel(result[0])
            if channel:
                embed = discord.Embed(description=content, color=0xff99cc)
                embed.set_footer(text="Gửi từ Yuri Garden Confession")
                await channel.send("🌸 **Một lời thú nhận ẩn danh mới:**", embed=embed)
                await interaction.followup.send("✅ Đã gửi thành công!", ephemeral=True)
            else:
                await interaction.followup.send("❌ Kênh confession không còn tồn tại.", ephemeral=True)
        else:
            await interaction.followup.send("❌ Server chưa setup kênh confession.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Confession(bot))