from bot_manager import BotManager
from config import BOT_TOKEN
import asyncio

async def main():
    bot_manager = BotManager(BOT_TOKEN)
    await bot_manager.start()

if __name__ == "__main__":
    asyncio.run(main())