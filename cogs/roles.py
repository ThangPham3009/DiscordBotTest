import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite


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

        await interaction.response.defer()  # Tránh bị timeout nếu thêm nhiều reaction

        # 1. Xử lý các cặp Emoji - Role
        raw_pairs = [(emoji1, role1), (emoji2, role2), (emoji3, role3), (emoji4, role4), (emoji5, role5)]
        valid_pairs = [(emo, role) for emo, role in raw_pairs if emo and role]

        # 2. Xây dựng Embed
        description = "Bấm vào các cảm xúc bên dưới để nhận hoặc gỡ vai trò.\n\n"
        description += "\n".join([f"• {emo} **{role.mention}**" for emo, role in valid_pairs])

        embed = discord.Embed(title=f"**{title}**", description=description, color=0x2b2d31)

        # 3. Gửi Embed và lấy Message ID
        sent_msg = await interaction.followup.send(embed=embed)

        # 4. Lưu vào SQLite và thêm Reaction
        for emo, role in valid_pairs:
            try:
                await sent_msg.add_reaction(emo)
                # Lưu từng cặp emoji-role vào database
                await self.bot.db.execute('''
                                          INSERT INTO reaction_roles (message_id, guild_id, emoji, role_id)
                                          VALUES (?, ?, ?, ?)
                                          ''', (sent_msg.id, interaction.guild.id, str(emo), role.id))
            except Exception as e:
                print(f"❗ Lỗi thêm reaction/lưu DB {emo}: {e}")

        await self.bot.db.commit()

    # --- LISTENER XỬ LÝ REACTION ---

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot: return

        # Truy vấn role_id từ database dựa trên msg_id và emoji
        async with self.bot.db.execute(
                "SELECT role_id FROM reaction_roles WHERE message_id = ? AND emoji = ?",
                (payload.message_id, str(payload.emoji))
        ) as cursor:
            result = await cursor.fetchone()

        if result:
            role_id = result[0]
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(role_id)
            if role:
                try:
                    await payload.member.add_roles(role)
                except discord.Forbidden:
                    print(f"❌ Thiếu quyền cấp Role tại Guild {payload.guild_id}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # Lưu ý: on_raw_reaction_remove không có payload.member
        async with self.bot.db.execute(
                "SELECT role_id FROM reaction_roles WHERE message_id = ? AND emoji = ?",
                (payload.message_id, str(payload.emoji))
        ) as cursor:
            result = await cursor.fetchone()

        if result:
            role_id = result[0]
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(role_id)
            member = guild.get_member(payload.user_id)

            if role and member:
                try:
                    await member.remove_roles(role)
                except discord.Forbidden:
                    print(f"❌ Thiếu quyền gỡ Role tại Guild {payload.guild_id}")


async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))