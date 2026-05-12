import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load dữ liệu từ file .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


class MyBot(commands.Bot):
    def __init__(self):
        # Thiết lập quyền hạn (Intents)
        intents = discord.Intents.default()
        intents.members = True  # Quyền quản lý thành viên (Welcome/Boost)
        intents.message_content = True  # Quyền đọc nội dung tin nhắn

        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        """Hàm chạy một lần khi bot khởi động để cài đặt các thành phần"""

        # 1. Tự động load tất cả file trong thư mục cogs
        print("--- Đang nạp các Cogs ---")
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"✅ Đã nạp: {filename}")
                except Exception as e:
                    print(f"❌ Lỗi nạp {filename}: {e}")

        # 2. Đồng bộ lệnh Slash (Slash Commands)
        # Thay đổi ID này thành ID server test của bạn để lệnh hiện ngay lập tức
        MY_GUILD = discord.Object(id=1502283307214180462)

        # Chép lệnh từ global vào riêng server này để tránh chờ 1 tiếng
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

        print("--- 🚀 Hệ thống đã sẵn sàng ---")

    async def on_ready(self):
        print(f'>>> Bot {self.user.name} (ID: {self.user.id}) đã trực tuyến!')


# Khởi tạo và chạy bot
if __name__ == "__main__":
    bot = MyBot()
    bot.run(TOKEN)