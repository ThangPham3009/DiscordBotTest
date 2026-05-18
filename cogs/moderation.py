import discord
from discord import app_commands
from discord.ext import commands
import datetime


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mute", description="Mute thành viên")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, minutes: int,
                   reason: str = "Không có lý do"):
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await interaction.response.send_message(f"🤫 Đã mute {member.mention} trong {minutes} phút.")

    @app_commands.command(name="unmute", description="Gỡ lệnh mute sớm cho thành viên")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        try:
            await member.timeout(None)  # Gỡ timeout bằng cách set về None
            await interaction.response.send_message(f"🔓 Đã gỡ mute cho {member.mention}")
        except Exception as e:
            await interaction.response.send_message(f"❌ Lỗi: {e}", ephemeral=True)

    @app_commands.command(name="myorder", description="Xem số thứ tự gia nhập")
    async def myorder(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        async with self.bot.db.execute(
                "SELECT join_order FROM member_stats WHERE guild_id = ? AND user_id = ?",
                (interaction.guild_id, target.id)
        ) as cursor:
            result = await cursor.fetchone()

        if result:
            await interaction.response.send_message(f"👤 {target.display_name} là thành viên thứ **{result[0]}**.")
        else:
            await interaction.response.send_message("❌ Chưa có dữ liệu.", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        async with self.bot.db.execute("SELECT MAX(join_order) FROM member_stats WHERE guild_id = ?",
                                       (member.guild.id,)) as cursor:
            res = await cursor.fetchone()
            new_order = (res[0] or 0) + 1
        await self.bot.db.execute("INSERT OR IGNORE INTO member_stats VALUES (?, ?, ?)",
                                  (member.guild.id, member.id, new_order))
        await self.bot.db.commit()


async def setup(bot):
    await bot.add_cog(Moderation(bot))