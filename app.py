import discord
from discord.ext import commands
import aiosqlite
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

class YuriBot(commands.Bot):
    def __init__(self):
        # Prefix vẫn phải khai báo cho lớp cha nhưng chúng ta sẽ không dùng đến
        intents = discord.Intents.all()
        super().__init__(command_prefix="!#none_used", intents=intents)
        self.db = None

    # Trong file app.py, sửa lại hàm on_ready
    async def on_ready(self):
        print(f'--- 🛠️ Bot {self.user.name} đã trực tuyến! ---')

        # Đếm tổng số lệnh đã nạp trong tree
        total_commands = len(self.tree.get_commands())
        print(f"📡 Tổng số lệnh tìm thấy trong code: {total_commands}")

        # Vòng lặp duyệt qua tất cả các server bot đang tham gia
        for guild in self.guilds:
            try:
                # BƯỚC QUAN TRỌNG:
                # Copy toàn bộ lệnh Global vào bộ nhớ đệm của Server này
                self.tree.copy_global_to(guild=guild)

                # Ép Discord đồng bộ ngay lập tức cho Server này
                synced = await self.tree.sync(guild=guild)

                print(f"✅ Đã sync {len(synced)} lệnh cho server: {guild.name} ({guild.id})")
            except discord.errors.Forbidden:
                print(f"❌ Thiếu quyền 'applications.commands' tại server: {guild.name}")
            except Exception as e:
                print(f"❌ Lỗi khi sync tại server {guild.name}: {e}")

        print("🚀 Tất cả các server đã được cập nhật lệnh mới nhất!")

    async def setup_hook(self):
        self.db = await aiosqlite.connect('yuri_bot.db')
        # ... (Các câu lệnh CREATE TABLE giữ nguyên như bản cũ Huy đã có)
        await self.db.commit()
        print("✅ SQLite Database Ready!")

        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')

    async def close(self):
        if self.db: await self.db.close()
        await super().close()

bot = YuriBot()
bot.run(TOKEN)