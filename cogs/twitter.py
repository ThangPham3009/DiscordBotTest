import discord
from discord.ext import commands, tasks
from discord import app_commands
import feedparser
import json
import os
import asyncio
import aiohttp


class TwitterTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'config.json'
        # Bắt đầu vòng lặp quét bài
        self.check_twitter.start()

    def get_data(self):
        """Đọc dữ liệu từ file config.json"""
        if not os.path.exists(self.config_file):
            return {"twitter": {"channel_id": None, "accounts": {}}}
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_data(self, data):
        """Lưu dữ liệu vào file config.json"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    # --- CÁC LỆNH SLASH COMMAND ---

    @app_commands.command(name="twitter_setup", description="Đặt kênh nhận thông báo Twitter")
    @app_commands.describe(channel="Kênh văn bản muốn bot gửi bài đăng vào")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def twitter_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        data = self.get_data()
        if "twitter" not in data:
            data["twitter"] = {"channel_id": None, "accounts": {}}

        data["twitter"]["channel_id"] = channel.id
        self.save_data(data)
        await interaction.response.send_message(f"✅ Đã đặt kênh thông báo Twitter là {channel.mention}")

    @app_commands.command(name="twitter_add", description="Thêm tài khoản Twitter vào danh sách theo dõi")
    @app_commands.describe(username="Tên người dùng (VD: elonmusk)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def twitter_add(self, interaction: discord.Interaction, username: str):
        username = username.replace("@", "").lower()
        data = self.get_data()

        if "twitter" not in data:
            data["twitter"] = {"channel_id": None, "accounts": {}}
        if "accounts" not in data["twitter"]:
            data["twitter"]["accounts"] = {}

        if username in data["twitter"]["accounts"]:
            await interaction.response.send_message(f"❌ `@{username}` đã có trong danh sách.", ephemeral=True)
        else:
            data["twitter"]["accounts"][username] = "0"
            self.save_data(data)
            await interaction.response.send_message(f"✅ Đã thêm `@{username}` vào danh sách theo dõi.")

    @app_commands.command(name="twitter_remove", description="Xóa tài khoản khỏi danh sách theo dõi")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def twitter_remove(self, interaction: discord.Interaction, username: str):
        username = username.replace("@", "").lower()
        data = self.get_data()

        if "twitter" in data and username in data["twitter"].get("accounts", {}):
            del data["twitter"]["accounts"][username]
            self.save_data(data)
            await interaction.response.send_message(f"🗑️ Đã ngừng theo dõi `@{username}`.")
        else:
            await interaction.response.send_message(f"❌ Không tìm thấy `@{username}`.", ephemeral=True)

    @app_commands.command(name="twitter_list", description="Xem danh sách tài khoản Twitter đang theo dõi")
    async def twitter_list(self, interaction: discord.Interaction):
        data = self.get_data()
        accounts = data.get("twitter", {}).get("accounts", {})

        if not accounts:
            return await interaction.response.send_message("Danh sách đang trống.")

        list_str = "\n".join([f"• @{user}" for user in accounts.keys()])
        embed = discord.Embed(title="📋 Twitter Follow List", description=list_str, color=0x1DA1F2)
        await interaction.response.send_message(embed=embed)

    # --- HỆ THỐNG QUÉT TỰ ĐỘNG ---

    @tasks.loop(minutes=2.0)
    async def check_twitter(self):
        data = self.get_data()
        twitter_config = data.get("twitter", {})
        channel_id = twitter_config.get("channel_id")
        accounts = twitter_config.get("accounts", {})

        if not channel_id or not accounts:
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        async with aiohttp.ClientSession() as session:
            for username, last_id in accounts.items():
                try:
                    # Sử dụng instance Nitter (Có thể thay nitter.net bằng nitter.cz hoặc nitter.it)
                    rss_url = f"https://nitter.net/{username}/rss"

                    async with session.get(rss_url, timeout=15) as response:
                        if response.status == 200:
                            xml_data = await response.text()
                            feed = feedparser.parse(xml_data)

                            if not feed.entries:
                                # Console log để bạn biết instance đang bị "Empty Feed"
                                print(f"⚠️ @{username}: Kết nối OK nhưng Nitter trả về danh sách trống.")
                                continue
                        else:
                            print(f"❌ @{username}: Lỗi kết nối Nitter (Status: {response.status})")
                            continue

                    # Lấy bài đăng mới nhất
                    latest_tweet = feed.entries[0]
                    # Tách ID từ link: https://nitter.net/user/status/123#m -> 123
                    tweet_id = str(latest_tweet.link.split('/')[-1].split('#')[0])

                    # In DEBUG ra console để soi lỗi nếu cần
                    # print(f"🔍 DEBUG @{username} | Web: {tweet_id} | Saved: {last_id}")

                    if tweet_id != str(last_id):
                        # Gửi link fxtwitter để tự hiện Embed đẹp
                        fxtwitter_url = f"https://fxtwitter.com/{username}/status/{tweet_id}"
                        await channel.send(fxtwitter_url)

                        # Cập nhật ID mới vào dữ liệu và lưu file
                        data["twitter"]["accounts"][username] = tweet_id
                        self.save_data(data)
                        print(f"🔔 Đã gửi bài mới của @{username}!")

                    # Nghỉ 2 giây để tránh bị Rate Limit
                    await asyncio.sleep(2)

                except Exception as e:
                    print(f"❗ Lỗi khi quét @{username}: {e}")

    @check_twitter.before_loop
    async def before_check_twitter(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(TwitterTracker(bot))