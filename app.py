import discord
from discord.ext import commands
import os
import json
from dotenv import load_dotenv

# Load dữ liệu từ file .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

CONFIG_FILE = 'server_config.json'


class MyBot(commands.Bot):
    def __init__(self):
        # 1. Thiết lập quyền hạn (Intents)
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(command_prefix='!', intents=intents)

        # 2. Kho lưu trữ cấu hình trên RAM (Cache)
        self.server_configs = {}
        self.load_all_configs()

    def load_all_configs(self):
        """Đọc file JSON vào RAM khi khởi động"""
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({"guilds": {}}, f)

        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            self.server_configs = json.load(f)
        print("📂 Đã nạp cấu hình các server vào RAM.")

    def save_configs(self):
        """Ghi dữ liệu từ RAM xuống file JSON (gọi khi có thay đổi)"""
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.server_configs, f, ensure_ascii=False, indent=4)

    async def setup_hook(self):
        """Hàm chạy một lần khi bot khởi động"""

        print("--- 🛠️ Đang nạp các Cogs ---")
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"✅ Đã nạp: {filename}")
                except Exception as e:
                    print(f"❌ Lỗi nạp {filename}: {e}")

        # Đồng bộ lệnh Slash
        MY_GUILD = discord.Object(id=1502283307214180462)
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

        print("--- 🚀 Hệ thống đã sẵn sàng ---")

    async def on_ready(self):
        print(f'>>> Bot {self.user.name} (ID: {self.user.id}) đã trực tuyến!')


# Khởi tạo và chạy bot
if __name__ == "__main__":
    bot = MyBot()
    bot.run(TOKEN)