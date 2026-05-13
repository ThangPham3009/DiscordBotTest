import discord
from discord import app_commands
from discord.ext import commands


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="say", description="Để bot nói hộ bạn ngay tại kênh này")
    @app_commands.describe(
        message="Nội dung tin nhắn (Dùng \n để xuống dòng)",
        reply_to_id="ID tin nhắn muốn trả lời (Để trống nếu gửi mới)"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def say(self, interaction: discord.Interaction,
                  message: str,
                  reply_to_id: str = None):

        # Lấy kênh hiện tại nơi lệnh được thực thi
        channel = interaction.channel

        try:
            # 1. Xử lý xuống dòng
            processed_message = message.replace("\\n", "\n")

            # 2. Gửi tin nhắn (có hoặc không có Reply)
            if reply_to_id:
                try:
                    target_msg = await channel.fetch_message(int(reply_to_id))
                    await target_msg.reply(processed_message)
                except Exception:
                    await channel.send(processed_message)
            else:
                await channel.send(processed_message)

            # 3. Phản hồi bí mật cho người dùng lệnh
            await interaction.response.send_message("✅ Đã gửi!", ephemeral=True)

            # --- LOGGING (Lưu vết Admin điều khiển bot) ---
            guild_id = str(interaction.guild.id)
            log_channel_id = self.bot.server_configs["guilds"].get(guild_id, {}).get("mod_log_channel")

            if log_channel_id:
                log_channel = interaction.guild.get_channel(log_channel_id)
                if log_channel:
                    log_embed = discord.Embed(
                        title="⚠️ Nhật ký Proxy Chat",
                        description=f"Admin {interaction.user.mention} đã dùng bot để chat tại {channel.mention}.",
                        color=0x2f3136
                    )
                    log_embed.add_field(name="Nội dung", value=message)
                    await log_channel.send(embed=log_embed)

        except discord.Forbidden:
            await interaction.response.send_message("❌ Bot không có quyền gửi tin nhắn ở đây!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Lỗi: {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Utility(bot))