import discord
from discord.ext import commands


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Đảm bảo database đã sẵn sàng
        if not self.bot.db: return

        # Truy xuất ID kênh từ SQLite
        async with self.bot.db.execute(
                "SELECT welcome_channel_id FROM server_configs WHERE guild_id = ?",
                (member.guild.id,)
        ) as cursor:
            result = await cursor.fetchone()

        if result and result[0]:
            channel_id = result[0]
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
        if not self.bot.db: return

        # Truy xuất ID kênh từ SQLite
        async with self.bot.db.execute(
                "SELECT welcome_channel_id FROM server_configs WHERE guild_id = ?",
                (member.guild.id,)
        ) as cursor:
            result = await cursor.fetchone()

        if result and result[0]:
            channel_id = result[0]
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