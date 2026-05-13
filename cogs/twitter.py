import discord
from discord.ext import commands, tasks
from discord import app_commands
import feedparser
import asyncio
import aiohttp


class TwitterTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Bắt đầu vòng lặp quét bài
        self.check_twitter.start()

    def cog_unload(self):
        self.check_twitter.cancel()

    # --- CÁC LỆNH SLASH COMMAND ---

    @app_commands.command(name="twitter_setup", description="[Admin] Đặt kênh nhận thông báo Twitter")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def twitter_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)

        if guild_id not in self.bot.server_configs["guilds"]:
            self.bot.server_configs["guilds"][guild_id] = {}

        self.bot.server_configs["guilds"][guild_id]["twitter_channel"] = channel.id
        self.bot.save_configs()
        await interaction.response.send_message(f"✅ Đã đặt kênh thông báo Twitter là {channel.mention}", ephemeral=True)

    @app_commands.command(name="twitter_add", description="[Admin] Thêm tài khoản Twitter vào danh sách theo dõi")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def twitter_add(self, interaction: discord.Interaction, username: str):
        username = username.replace("@", "").lower()
        guild_id = str(interaction.guild.id)

        if guild_id not in self.bot.server_configs["guilds"]:
            self.bot.server_configs["guilds"][guild_id] = {}

        if "twitter_accounts" not in self.bot.server_configs["guilds"][guild_id]:
            self.bot.server_configs["guilds"][guild_id]["twitter_accounts"] = {}

        accounts = self.bot.server_configs["guilds"][guild_id]["twitter_accounts"]

        if username in accounts:
            await interaction.response.send_message(f"❌ `@{username}` đã có trong danh sách.", ephemeral=True)
        else:
            accounts[username] = "0"
            self.bot.save_configs()
            await interaction.response.send_message(f"✅ Đã thêm `@{username}` vào danh sách theo dõi.")

    @app_commands.command(name="twitter_remove", description="[Admin] Xóa tài khoản khỏi danh sách theo dõi")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def twitter_remove(self, interaction: discord.Interaction, username: str):
        username = username.replace("@", "").lower()
        guild_id = str(interaction.guild.id)

        accounts = self.bot.server_configs["guilds"].get(guild_id, {}).get("twitter_accounts", {})

        if username in accounts:
            del accounts[username]
            self.bot.save_configs()
            await interaction.response.send_message(f"🗑️ Đã ngừng theo dõi `@{username}`.")
        else:
            await interaction.response.send_message(f"❌ Không tìm thấy `@{username}`.", ephemeral=True)

    @app_commands.command(name="twitter_list", description="Xem danh sách tài khoản Twitter đang theo dõi")
    async def twitter_list(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        accounts = self.bot.server_configs["guilds"].get(guild_id, {}).get("twitter_accounts", {})

        if not accounts:
            return await interaction.response.send_message("Danh sách đang trống.")

        list_str = "\n".join([f"• @{user}" for user in accounts.keys()])
        embed = discord.Embed(title="📋 Twitter Follow List", description=list_str, color=0x1DA1F2)
        await interaction.response.send_message(embed=embed)

    # --- HỆ THỐNG QUÉT TỰ ĐỘNG ---

    @tasks.loop(minutes=5.0)  # Tăng lên 5 phút để tránh bị Nitter chặn IP (Rate Limit)
    async def check_twitter(self):
        async with aiohttp.ClientSession() as session:
            # Duyệt qua từng server trong cấu hình
            for guild_id, config in self.bot.server_configs["guilds"].items():
                channel_id = config.get("twitter_channel")
                accounts = config.get("twitter_accounts", {})

                if not channel_id or not accounts:
                    continue

                channel = self.bot.get_channel(channel_id)
                if not channel:
                    continue

                for username, last_id in accounts.items():
                    try:
                        # Thử các instance Nitter khác nhau nếu nitter.net bị lỗi
                        rss_url = f"https://nitter.privacydev.net/{username}/rss"

                        async with session.get(rss_url, timeout=15) as response:
                            if response.status == 200:
                                xml_data = await response.text()
                                feed = feedparser.parse(xml_data)
                                if not feed.entries: continue
                            else:
                                continue

                        latest_tweet = feed.entries[0]
                        tweet_id = str(latest_tweet.link.split('/')[-1].split('#')[0])

                        if tweet_id != str(last_id):
                            fxtwitter_url = f"https://fxtwitter.com/{username}/status/{tweet_id}"
                            await channel.send(fxtwitter_url)

                            # Cập nhật ID mới trực tiếp vào cache RAM của bot
                            self.bot.server_configs["guilds"][guild_id]["twitter_accounts"][username] = tweet_id
                            self.bot.save_configs()

                        await asyncio.sleep(1)  # Nghỉ ngắn giữa các tài khoản

                    except Exception as e:
                        print(f"❗ Lỗi quét @{username} tại Guild {guild_id}: {e}")

    @check_twitter.before_loop
    async def before_check_twitter(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(TwitterTracker(bot))