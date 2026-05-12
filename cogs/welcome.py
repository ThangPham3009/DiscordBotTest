import discord
from discord.ext import commands
import json


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'config.json'

    @commands.Cog.listener()
    async def on_member_join(self, member):
        with open(self.config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        channel_id = data['welcome_channels'].get(str(member.guild.id))
        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                # Embed tối giản không ảnh banner
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
        with open(self.config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        channel_id = data['welcome_channels'].get(str(member.guild.id))
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