import discord
from discord import app_commands
from discord.ext import commands, tasks
import feedparser
import asyncio


class Twitter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_twitter.start()

    def cog_unload(self):
        self.check_twitter.cancel()

    @tasks.loop(minutes=10.0)  # 10 phút quét một lần là cực kỳ an toàn
    async def check_twitter(self):
        await self.bot.wait_until_ready()
        if not self.bot.db: return

        async with self.bot.db.execute("SELECT id, guild_id, twitter_user, last_tweet_id FROM twitter_feeds") as cursor:
            feeds = await cursor.fetchall()

        print(f"🔄 [RSS] Đang tiến hành quét {len(feeds)} tài khoản Twitter...")

        for feed_id, guild_id, twitter_user, last_id in feeds:
            try:
                # Sử dụng các instance Nitter công khai làm proxy RSS (Miễn phí, không cần tài khoản)
                rss_url = f"https://nitter.net/{twitter_user}/rss"

                # Đọc dữ liệu RSS
                feed = await asyncio.to_thread(feedparser.parse, rss_url)

                if not feed.entries:
                    print(f"ℹ️ Không tìm thấy bài đăng hoặc tài khoản @{twitter_user} đang khóa.")
                    continue

                latest_entry = feed.entries[0]

                # Lấy ID bài viết từ link (Ví dụ: .../status/123456789 -> ID là 123456789)
                new_tweet_id = latest_entry.link.split('/')[-1].split('#')[0]

                if last_id is None or new_tweet_id != last_id:
                    print(f"🆕 [RSS] Tìm thấy bài mới của @{twitter_user}")

                    async with self.bot.db.execute(
                            "SELECT welcome_channel_id FROM server_configs WHERE guild_id = ?",
                            (guild_id,)
                    ) as config_cursor:
                        channel_result = await config_cursor.fetchone()

                    if channel_result and channel_result[0]:
                        channel = self.bot.get_channel(channel_result[0])
                        if not channel:
                            try:
                                channel = await self.bot.fetch_channel(channel_result[0])
                            except:
                                channel = None

                        if channel:
                            # Gửi link gốc Twitter, Discord sẽ tự tạo Embed preview
                            await channel.send(
                                f"📢 **@{twitter_user}** vừa đăng bài mới!\n"
                                f"🔗 https://twitter.com/{twitter_user}/status/{new_tweet_id}"
                            )
                            print(f"✅ Đã gửi bài của @{twitter_user} vào kênh {channel.name}")

                    # Cập nhật DB
                    await self.bot.db.execute(
                        "UPDATE twitter_feeds SET last_tweet_id = ? WHERE id = ?",
                        (new_tweet_id, feed_id)
                    )
                    await self.bot.db.commit()
                else:
                    print(f"💤 @{twitter_user} không có bài mới.")

                await asyncio.sleep(3)  # Giãn cách nhẹ giữa các tài khoản

            except Exception as e:
                print(f"❌ Lỗi khi quét RSS của @{twitter_user}: {e}")

    @app_commands.command(name="twitter_add", description="[Admin] Thêm tài khoản Twitter vào danh sách theo dõi")
    @app_commands.describe(username="Tên người dùng Twitter (ví dụ: NASA)")
    @app_commands.checks.has_permissions(administrator=True)
    async def twitter_add(self, interaction: discord.Interaction, username: str):
        username = username.replace("@", "").strip()
        await self.bot.db.execute(
            "INSERT INTO twitter_feeds (guild_id, twitter_user) VALUES (?, ?)",
            (interaction.guild_id, username)
        )
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ Đã thêm **@{username}** vào danh sách theo dõi.")


async def setup(bot):
    await bot.add_cog(Twitter(bot))