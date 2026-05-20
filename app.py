import discord
from discord.ext import commands
import aiosqlite
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


class YuriBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!#none_used", intents=intents)
        self.db = None

    async def on_ready(self):
        print(f'--- 🛠️ Bot {self.user.name} đã trực tuyến! ---')
        print("🚀 Hệ thống đang hoạt động ổn định!")

    async def setup_hook(self):
        self.db = await aiosqlite.connect('Bot.db')

        # 1. Bảng cấu hình server (Cập nhật thêm cột facebook_channel_id)
        await self.db.execute('''
                              CREATE TABLE IF NOT EXISTS server_configs
                              (
                                  guild_id
                                  INTEGER
                                  PRIMARY
                                  KEY,
                                  welcome_channel_id
                                  INTEGER,
                                  confession_channel_id
                                  INTEGER,
                                  twitter_channel_id
                                  INTEGER,
                                  facebook_channel_id
                                  INTEGER -- Thêm cột này
                              )
                              ''')

        # 2. Tạo bảng theo dõi Facebook mới
        await self.db.execute('''
                              CREATE TABLE IF NOT EXISTS facebook_feeds
                              (
                                  id
                                  INTEGER
                                  PRIMARY
                                  KEY
                                  AUTOINCREMENT,
                                  guild_id
                                  INTEGER,
                                  rss_url
                                  TEXT, -- ĐỔI TÊN CỘT NÀY: Lưu thẳng link của rss.app
                                  role_ids
                                  TEXT,
                                  last_post_id
                                  TEXT
                              )
                              ''')
        await self.db.execute('''
                              CREATE TABLE IF NOT EXISTS twitter_feeds
                              (
                                  id
                                  INTEGER
                                  PRIMARY
                                  KEY
                                  AUTOINCREMENT,
                                  guild_id
                                  INTEGER,
                                  twitter_user
                                  TEXT,
                                  last_tweet_id
                                  TEXT
                              )
                              ''')
        await self.db.execute('''
                              CREATE TABLE IF NOT EXISTS member_stats
                              (
                                  guild_id
                                  INTEGER,
                                  user_id
                                  INTEGER,
                                  join_order
                                  INTEGER,
                                  PRIMARY
                                  KEY
                              (
                                  guild_id,
                                  user_id
                              )
                                  )
                              ''')
        await self.db.commit()
        print("✅ SQLite Database đã cập nhật cấu trúc Facebook!")
        await self.db.commit()
        print("✅ SQLite Database Ready!")

        # 1. Nạp toàn bộ lệnh từ Cogs vào bộ nhớ (Não bot)
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')

        total_cmds = len(self.tree.get_commands())
        print(f"📡 Đã nạp thành công {total_cmds} lệnh vào bộ nhớ.")

        # 2. Quét dọn: Ép Discord xóa hết các lệnh bị lặp ở từng Server
        for guild in self.guilds:
            self.tree.clear_commands(guild=guild)
            try:
                await self.tree.sync(guild=guild)
            except Exception:
                pass
        print("🧹 Đã dọn dẹp sạch sẽ các lệnh rác/lệnh lặp ở cấp Server.")

        # 3. Đồng bộ duy nhất 1 bản Toàn cầu (Global)
        try:
            synced = await self.tree.sync()
            print(f"🔄 Đã đồng bộ Toàn cầu {len(synced)} lệnh Slash Command!")
        except Exception as e:
            print(f"❌ Lỗi đồng bộ toàn cầu: {e}")

    async def close(self):
        if self.db: await self.db.close()
        await super().close()


bot = YuriBot()
bot.run(TOKEN)