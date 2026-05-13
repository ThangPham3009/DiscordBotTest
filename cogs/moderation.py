import discord
from discord import app_commands
from discord.ext import commands
import datetime


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. Lệnh thiết lập kênh Log cho Admin
    @app_commands.command(name="set_mod_logs", description="[Admin] Thiết lập kênh lưu nhật ký quản trị")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_mod_logs(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)

        if guild_id not in self.bot.server_configs["guilds"]:
            self.bot.server_configs["guilds"][guild_id] = {}

        self.bot.server_configs["guilds"][guild_id]["mod_log_channel"] = channel.id
        self.bot.save_configs()

        await interaction.response.send_message(f"✅ Đã thiết lập {channel.mention} làm kênh nhật ký quản trị!",
                                                ephemeral=True)

    # 2. Lệnh Mute (Timeout)
    @app_commands.command(name="mute", description="Tạm thời cấm một thành viên nhắn tin (Timeout)")
    @app_commands.describe(member="Thành viên bạn muốn mute", minutes="Số phút (tối đa 28 ngày)", reason="Lý do")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, minutes: int,
                   reason: str = "Không có lý do"):
        if minutes <= 0:
            return await interaction.response.send_message("❌ Số phút phải lớn hơn 0!", ephemeral=True)

        duration = datetime.timedelta(minutes=minutes)

        try:
            await member.timeout(duration, reason=reason)

            # Tạo Embed thông báo
            embed = discord.Embed(
                title="🔇 Lệnh Mute đã thực thi",
                description=f"Thành viên {member.mention} đã bị tạm dừng hoạt động.",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="Thời gian", value=f"{minutes} phút", inline=True)
            embed.add_field(name="Người thực hiện", value=interaction.user.mention, inline=True)
            embed.add_field(name="Lý do", value=reason, inline=False)

            # Phản hồi lệnh
            await interaction.response.send_message(embed=embed)

            # --- LOGGING SYSTEM ---
            guild_id = str(interaction.guild.id)
            log_channel_id = self.bot.server_configs["guilds"].get(guild_id, {}).get("mod_log_channel")

            if log_channel_id:
                log_channel = interaction.guild.get_channel(log_channel_id)
                if log_channel:
                    await log_channel.send(embed=embed)

        except discord.Forbidden:
            await interaction.response.send_message("❌ Bot không đủ quyền để mute người này.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Đã có lỗi xảy ra: {e}", ephemeral=True)

    # 3. Lệnh Unmute
    @app_commands.command(name="unmute", description="Gỡ lệnh mute sớm cho thành viên")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        try:
            await member.timeout(None)
            success_msg = f"✅ Đã gỡ mute sớm cho {member.mention}."
            await interaction.response.send_message(success_msg)

            # --- LOGGING SYSTEM ---
            guild_id = str(interaction.guild.id)
            log_channel_id = self.bot.server_configs["guilds"].get(guild_id, {}).get("mod_log_channel")

            if log_channel_id:
                log_channel = interaction.guild.get_channel(log_channel_id)
                if log_channel:
                    log_embed = discord.Embed(
                        title="🔊 Đã gỡ Mute",
                        description=f"Thành viên {member.mention} đã có thể hoạt động trở lại.",
                        color=discord.Color.green(),
                        timestamp=datetime.datetime.now()
                    )
                    log_embed.add_field(name="Người thực hiện", value=interaction.user.mention)
                    await log_channel.send(embed=log_embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Không thể gỡ mute: {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Moderation(bot))