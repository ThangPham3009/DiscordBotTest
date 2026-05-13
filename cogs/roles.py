import discord
from discord import app_commands
from discord.ext import commands


class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_roles", description="[Admin] Tạo bảng chọn Role tự động bằng Emoji")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def setup_roles(self, interaction: discord.Interaction, title: str,
                          emoji1: str, role1: discord.Role,
                          emoji2: str = None, role2: discord.Role = None,
                          emoji3: str = None, role3: discord.Role = None,
                          emoji4: str = None, role4: discord.Role = None,
                          emoji5: str = None, role5: discord.Role = None):

        guild_id = str(interaction.guild.id)

        # 1. Xây dựng danh sách cặp Emoji - Role
        raw_pairs = [
            (emoji1, role1), (emoji2, role2), (emoji3, role3), (emoji4, role4), (emoji5, role5)
        ]

        valid_pairs = [(emo, role) for emo, role in raw_pairs if emo and role]

        # 2. Tạo nội dung Embed chuyên nghiệp
        header = "Bấm vào các cảm xúc bên dưới để nhận hoặc gỡ vai trò của bạn.\n\u200b\n"
        role_list_str = "\n".join([f"• {emo} **{role.mention}**" for emo, role in valid_pairs])

        embed = discord.Embed(
            title=f"**{title}**",
            description=header + role_list_str,
            color=0x2b2d31  # Màu xám tối đặc trưng Discord
        )

        # 3. Gửi Embed
        await interaction.response.send_message(embed=embed)
        sent_msg = await interaction.original_response()

        # 4. Lưu dữ liệu vào cache RAM và file JSON
        if guild_id not in self.bot.server_configs["guilds"]:
            self.bot.server_configs["guilds"][guild_id] = {}

        if "reaction_roles" not in self.bot.server_configs["guilds"][guild_id]:
            self.bot.server_configs["guilds"][guild_id]["reaction_roles"] = {}

        msg_id = str(sent_msg.id)
        self.bot.server_configs["guilds"][guild_id]["reaction_roles"][msg_id] = {}

        for emo, role in valid_pairs:
            try:
                await sent_msg.add_reaction(emo)
                self.bot.server_configs["guilds"][guild_id]["reaction_roles"][msg_id][emo] = role.id
            except Exception as e:
                print(f"❗ Không thể thêm reaction {emo}: {e}")

        self.bot.save_configs()

    # --- LISTENER XỬ LÝ REACTION ---

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot: return

        guild_id = str(payload.guild_id)
        msg_id = str(payload.message_id)
        emoji = str(payload.emoji)

        # Truy xuất từ cache RAM
        guild_data = self.bot.server_configs["guilds"].get(guild_id, {})
        role_map = guild_data.get("reaction_roles", {}).get(msg_id)

        if role_map and emoji in role_map:
            role_id = role_map[emoji]
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(role_id)
            if role:
                try:
                    await payload.member.add_roles(role)
                except discord.Forbidden:
                    print(f"❌ Thiếu quyền cấp Role tại Guild {guild_id}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild_id = str(payload.guild_id)
        msg_id = str(payload.message_id)
        emoji = str(payload.emoji)

        guild_data = self.bot.server_configs["guilds"].get(guild_id, {})
        role_map = guild_data.get("reaction_roles", {}).get(msg_id)

        if role_map and emoji in role_map:
            role_id = role_map[emoji]
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(role_id)
            member = guild.get_member(payload.user_id)

            if role and member:
                try:
                    await member.remove_roles(role)
                except discord.Forbidden:
                    print(f"❌ Thiếu quyền gỡ Role tại Guild {guild_id}")


async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))