import discord
from discord import app_commands
from discord.ext import commands


class ConfessModal(discord.ui.Modal, title='Gửi Lời Thổ Lộ Ẩn Danh'):
    # Ô nhập liệu
    content = discord.ui.TextInput(
        label='Nội dung confession',
        style=discord.TextStyle.long,
        placeholder='Hãy viết những gì bạn muốn nói ở đây...',
        required=True,
        max_length=1000
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        configs = self.bot.server_configs["guilds"]

        # 1. Kiểm tra xem server đã cài đặt kênh chưa
        if guild_id not in configs or "confession_channel" not in configs[guild_id]:
            await interaction.response.send_message(
                "❌ Server này chưa thiết lập kênh confession. Hãy nhờ Admin dùng lệnh `/set_confession`!",
                ephemeral=True
            )
            return

        conf_channel_id = configs[guild_id]["confession_channel"]
        target_channel = interaction.guild.get_channel(conf_channel_id)

        if not target_channel:
            await interaction.response.send_message("❌ Không tìm thấy kênh confession đã thiết lập!", ephemeral=True)
            return

        # 2. Xử lý số thứ tự (ID) và Lưu log dữ liệu
        configs[guild_id]["last_confession_id"] = configs[guild_id].get("last_confession_id", 0) + 1
        conf_id = configs[guild_id]["last_confession_id"]

        # Lưu log (ẩn danh với người dùng nhưng lưu lại cho Admin/Bot chủ nếu cần check)
        if "confession_logs" not in configs[guild_id]:
            configs[guild_id]["confession_logs"] = []

        configs[guild_id]["confession_logs"].append({
            "id": conf_id,
            "user_id": interaction.user.id,
            "content": self.content.value
        })

        # 3. Ghi dữ liệu xuống file (Thông qua hàm ở main.py)
        self.bot.save_configs()

        # 4. Gửi Embed vào kênh
        embed = discord.Embed(
            title=f"🌸 Yuri Confession #{conf_id}",
            description=self.content.value,
            color=0xff99cc
        )
        embed.set_footer(text="Gõ /confess để gửi lời thổ lộ ẩn danh")

        await target_channel.send(embed=embed)
        await interaction.response.send_message(f"✅ Đã gửi Confession #{conf_id} thành công!", ephemeral=True)


class Confession(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_confession", description="[Admin] Thiết lập kênh nhận confession")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_confession(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)

        # Khởi tạo vùng nhớ cho server nếu chưa có
        if guild_id not in self.bot.server_configs["guilds"]:
            self.bot.server_configs["guilds"][guild_id] = {}

        # Lưu ID kênh vào RAM
        self.bot.server_configs["guilds"][guild_id]["confession_channel"] = channel.id

        # Lưu xuống file JSON
        self.bot.save_configs()

        await interaction.response.send_message(f"✅ Đã thiết lập {channel.mention} làm kênh nhận Confession!",
                                                ephemeral=True)

    @app_commands.command(name="confess", description="Gửi một lời thổ lộ ẩn danh")
    async def confess(self, interaction: discord.Interaction):
        # Truyền bot vào Modal để Modal có thể gọi hàm save_configs()
        await interaction.response.send_modal(ConfessModal(self.bot))


async def setup(bot):
    await bot.add_cog(Confession(bot))