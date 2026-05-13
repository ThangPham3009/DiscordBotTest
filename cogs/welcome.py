import discord
from discord import app_commands
from discord.ext import commands


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_welcome", description="[Admin] Thiết lập kênh chào mừng/tạm biệt cho server")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_welcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)

        # Khởi tạo vùng nhớ cho server nếu chưa có
        if guild_id not in self.bot.server_configs["guilds"]:
            self.bot.server_configs["guilds"][guild_id] = {}

        # Lưu ID kênh vào cache trên RAM
        self.bot.server_configs["guilds"][guild_id]["welcome_channel"] = channel.id

        # Ghi xuống file JSON thông qua hàm ở main.py
        self.bot.save_configs()

        await interaction.response.send_message(f"✅ Đã thiết lập {channel.mention} làm kênh chào mừng và tạm biệt!",
                                                ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        # Truy xuất kênh từ cache RAM
        configs = self.bot.server_configs["guilds"].get(guild_id, {})
        channel_id = configs.get("welcome_channel")

        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title=f"✨ Chào mừng {member.name} đã đến với Yuri Garden. ✨",
                    description=(
                        f"▸ Chào mừng bạn đã ghé thăm góc nhỏ của chúng mình.\n\n"
                        f"▸ Bạn nhớ đọc luật ở các kênh hướng dẫn nhé!\n\n"
                        f"▸ Chúc bạn có những giây phút thư giãn tại đây."
                    ),
                    color=0xffc0cb
                )
                embed.set_footer(text="Yuri Garden | #YG")
                await channel.send(f"Chào mừng {member.mention}!", embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_id = str(member.guild.id)
        # Truy xuất kênh từ cache RAM
        configs = self.bot.server_configs["guilds"].get(guild_id, {})
        channel_id = configs.get("welcome_channel")

        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title="🌿 Tạm biệt...",
                    description=f"▸ Một cánh hoa vừa rời khỏi khu vườn. Hy vọng sẽ gặp lại {member.name} vào một ngày không xa!",
                    color=0x2f3136
                )
                await channel.send(f"Tạm biệt {member.mention}!", embed=embed)


async def setup(bot):
    await bot.add_cog(Welcome(bot))