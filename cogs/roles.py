import discord
from discord.ext import commands
from discord import app_commands
import json
import os


class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'config.json'

    def get_data(self):
        if not os.path.exists(self.config_file):
            return {"reaction_roles": {}, "welcome_channels": {}}
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_data(self, data):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    @app_commands.command(name="setup_roles", description="Tạo bảng chọn Role tự động")
    @app_commands.describe(title="Tiêu đề (VD: Lấy role)")
    async def setup_roles(self, interaction: discord.Interaction, title: str,
                          emoji1: str, role1: discord.Role,
                          emoji2: str = None, role2: discord.Role = None,
                          emoji3: str = None, role3: discord.Role = None,
                          emoji4: str = None, role4: discord.Role = None,
                          emoji5: str = None, role5: discord.Role = None,
                          emoji6: str = None, role6: discord.Role = None,
                          emoji7: str = None, role7: discord.Role = None,
                          emoji8: str = None, role8: discord.Role = None,
                          emoji9: str = None, role9: discord.Role = None,
                          emoji10: str = None, role10: discord.Role = None):

        # 1. Gom các cặp dữ liệu
        pairs = [
            (emoji1, role1), (emoji2, role2), (emoji3, role3), (emoji4, role4), (emoji5, role5),
            (emoji6, role6), (emoji7, role7), (emoji8, role8), (emoji9, role9), (emoji10, role10)
        ]

        # 2. Tự động xây dựng Description giống hệt mẫu
        # Dòng hướng dẫn cố định
        header = "Bấm vào nút bên dưới để nhận hoặc gỡ role của bạn.\n\n"

        # Danh sách các Role kèm dấu chấm tròn
        role_list = []
        valid_pairs = []

        for emo, role in pairs:
            if emo and role:
                # Định dạng: • Emoji RoleName (hoặc chỉ • RoleName tùy bạn)
                # Mình khuyên nên để kèm Emoji để người dùng biết bấm vào cái nào nhé
                role_list.append(f"• {emo} {role.name}")
                valid_pairs.append((emo, role))

                # 1. Dòng hướng dẫn (Thêm \n\u200b để tạo khoảng trống nhỏ phía dưới dòng tiêu đề)
                header = "Bấm vào nút bên dưới để nhận hoặc gỡ role của bạn.\n\u200b\n"

                role_list = []
                valid_pairs = []

                for emo, role in pairs:
                    if emo and role:
                        # SỬA TẠI ĐÂY:
                        # - Dùng role.mention để hiện màu
                        # - Thêm \n ở cuối mỗi dòng để giãn cách
                        role_list.append(f"• {emo} **{role.mention}**\n")
                        valid_pairs.append((emo, role))

                # 2. Nối các dòng bằng \n (kết hợp với \n ở trên sẽ tạo ra khoảng cách kép)
                full_description = header + "\n".join(role_list)

                # 3. Tạo Embed (Giữ màu 0x2b2d31 nếu muốn ẩn khung, hoặc 0xffffff để hiện khung trắng cho nổi)
                embed = discord.Embed(
                    title=f"**{title}**",  # In đậm tiêu đề
                    description=full_description,
                    color=0x2b2d31
                )

        # 3. Tạo và gửi Embed (Màu 0x2b2d31 là màu xám tối đặc trưng của Discord)
        embed = discord.Embed(title=title, description=full_description, color=0x2b2d31)

        await interaction.response.send_message(embed=embed)

        # 4. Lưu ID và thả Reaction (Phần này giữ nguyên như cũ)
        sent_msg = await interaction.original_response()
        data = self.get_data()
        msg_id = str(sent_msg.id)
        data["reaction_roles"][msg_id] = {}

        for emo, role in valid_pairs:
            await sent_msg.add_reaction(emo)
            data["reaction_roles"][msg_id][emo] = role.id

        self.save_data(data)

    # --- PHẦN LISTENER (Xử lý khi người dùng nhấn/gỡ emoji) ---

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot: return
        data = self.get_data()
        msg_id = str(payload.message_id)
        emoji = str(payload.emoji)

        if msg_id in data.get("reaction_roles", {}):
            role_id = data["reaction_roles"][msg_id].get(emoji)
            if role_id:
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(role_id)
                if role:
                    await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        data = self.get_data()
        msg_id = str(payload.message_id)
        emoji = str(payload.emoji)

        if msg_id in data.get("reaction_roles", {}):
            role_id = data["reaction_roles"][msg_id].get(emoji)
            if role_id:
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(role_id)
                member = guild.get_member(payload.user_id)
                if role and member:
                    await member.remove_roles(role)


# --- ĐÂY LÀ PHẦN BẠN ĐANG THIẾU ---
async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))