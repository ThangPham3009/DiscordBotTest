import discord
from discord import app_commands
from discord.ext import commands, tasks
import feedparser
import asyncio


class Facebook(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_facebook.start()

    def cog_unload(self):
        self.check_facebook.cancel()

    @tasks.loop(minutes=10.0)  # Với rss.app, 10 phút là cực kỳ ổn định
    async def check_facebook(self):
        await self.bot.wait_until_ready()
        if not self.bot.db: return

        # Lấy rss_url từ database thay vì page_username
        async with self.bot.db.execute(
                "SELECT id, guild_id, rss_url, role_ids, last_post_id FROM facebook_feeds") as cursor:
            feeds = await cursor.fetchall()

        if feeds:
            print(f"🔄 [Facebook] Đang tiến hành quét {len(feeds)} nguồn cấp RSS.app...")

        for feed_id, guild_id, rss_url, role_ids, last_id in feeds:
            try:
                # Đọc thẳng dữ liệu từ link rss.app
                feed = await asyncio.to_thread(feedparser.parse, rss_url)

                if not feed.entries:
                    continue

                latest_entry = feed.entries[0]

                # rss.app trả về link bài viết rất chuẩn, dùng luôn link này làm ID để đối chiếu
                new_post_id = latest_entry.link

                if last_id is None or new_post_id != last_id:
                    # Tự động lấy tên Fanpage từ tiêu đề của nguồn RSS
                    page_name = feed.feed.title if 'title' in feed.feed else "Một trang Facebook"

                    print(f"🆕 [Facebook] Tìm thấy bài mới của {page_name}")

                    async with self.bot.db.execute(
                            "SELECT facebook_channel_id FROM server_configs WHERE guild_id = ?",
                            (guild_id,)
                    ) as config_cursor:
                        channel_result = await config_cursor.fetchone()

                    if channel_result and channel_result[0]:
                        channel_id = channel_result[0]
                        channel = self.bot.get_channel(channel_id)
                        if not channel:
                            try:
                                channel = await self.bot.fetch_channel(channel_id)
                            except:
                                channel = None

                        if channel:
                            # Xử lý chuỗi Role IDs
                            ping_message = ""
                            if role_ids:
                                id_list = role_ids.split(",")
                                ping_message = " ".join([f"<@&{r_id}>" for r_id in id_list if r_id.strip()])

                            await channel.send(
                                f"{ping_message}\n"
                                f"📢 **{page_name}** vừa có bài đăng mới!\n"
                                f"🔗 Link: {latest_entry.link}"
                            )
                            print(f"✅ Đã gửi bài đăng của {page_name} vào kênh {channel.name}")

                    # Cập nhật ID bài viết (link) mới nhất vào DB
                    await self.bot.db.execute(
                        "UPDATE facebook_feeds SET last_post_id = ? WHERE id = ?",
                        (new_post_id, feed_id)
                    )
                    await self.bot.db.commit()
                else:
                    print(f"💤 Nguồn {rss_url} chưa có bài mới.")

                await asyncio.sleep(3)

            except Exception as e:
                print(f"❌ Lỗi khi quét RSS của {rss_url}: {e}")

    @app_commands.command(name="set_facebook_channel", description="[Admin] Cài đặt kênh nhận thông báo Facebook")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_facebook_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.db.execute(
            "INSERT INTO server_configs (guild_id, facebook_channel_id) VALUES (?, ?) "
            "ON CONFLICT(guild_id) DO UPDATE SET facebook_channel_id = excluded.facebook_channel_id",
            (interaction.guild_id, channel.id)
        )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ Đã lưu kênh nhận thông báo Facebook: {channel.mention}")

    @app_commands.command(name="set_facebook_ping",
                          description="[Admin] Thêm nguồn RSS từ rss.app để theo dõi Facebook")
    @app_commands.describe(
        rss_link="Đường link XML copy từ rss.app (Ví dụ: https://rss.app/feeds/xxx.xml)",
        role1="Role thứ 1 cần ping",
        role2="Role thứ 2 (Tùy chọn)",
        role3="Role thứ 3 (Tùy chọn)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def set_facebook_ping(
            self,
            interaction: discord.Interaction,
            rss_link: str,
            role1: discord.Role,
            role2: discord.Role = None,
            role3: discord.Role = None
    ):
        # Lấy danh sách ID
        selected_roles = [role1, role2, role3]
        role_ids_list = [str(role.id) for role in selected_roles if role is not None]
        role_ids_str = ",".join(role_ids_list)

        await self.bot.db.execute(
            "INSERT INTO facebook_feeds (guild_id, rss_url, role_ids) VALUES (?, ?, ?)",
            (interaction.guild_id, rss_link.strip(), role_ids_str)
        )
        await self.bot.db.commit()

        mentions_str = " ".join([f"<@&{r_id}>" for r_id in role_ids_list])
        await interaction.response.send_message(
            f"✅ Đã thêm nguồn cấp dữ liệu vào danh sách theo dõi.\n"
            f"🔔 Khi có bài mới, các Role sau sẽ được gọi: {mentions_str}"
        )


async def setup(bot):
    await bot.add_cog(Facebook(bot))