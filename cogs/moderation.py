import discord
from discord.ext import commands
from discord import app_commands
import datetime  # Thư viện để xử lý thời gian


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mute", description="Tạm thời cấm một thành viên nhắn tin (Timeout)")
    @app_commands.describe(
        member="Thành viên bạn muốn mute",
        minutes="Số phút muốn mute (tối đa 28 ngày)",
        reason="Lý do mute"
    )
    # Kiểm tra quyền: Chỉ những ai có quyền "Quản lý thành viên" mới dùng được lệnh này
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, minutes: int,
                   reason: str = "Không có lý do"):
        # 1. Kiểm tra tính hợp lệ của thời gian
        if minutes <= 0:
            return await interaction.response.send_message("❌ Số phút phải lớn hơn 0!", ephemeral=True)

        # 2. Tạo khoảng thời gian (duration)
        duration = datetime.timedelta(minutes=minutes)

        try:
            # 3. Thực hiện lệnh Timeout của Discord
            await member.timeout(duration, reason=reason)

            # 4. Phản hồi lại trên Discord
            embed = discord.Embed(
                title="🔇 Đã thực thi lệnh Mute",
                description=f"Thành viên {member.mention} đã bị tạm dừng hoạt động.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Thời gian", value=f"{minutes} phút", inline=True)
            embed.add_field(name="Người thực hiện", value=interaction.user.mention, inline=True)
            embed.add_field(name="Lý do", value=reason, inline=False)

            await interaction.response.send_message(embed=embed)

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Bot không đủ quyền để mute người này (có thể do Role của họ cao hơn Bot).", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Đã có lỗi xảy ra: {e}", ephemeral=True)

    # Lệnh Unmute thủ công nếu muốn gỡ sớm
    @app_commands.command(name="unmute", description="Gỡ lệnh mute sớm cho thành viên")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        try:
            await member.timeout(None)  # Truyền None để gỡ timeout
            await interaction.response.send_message(f"✅ Đã gỡ mute sớm cho {member.mention}.")
        except Exception as e:
            await interaction.response.send_message(f"❌ Không thể gỡ mute: {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Moderation(bot))