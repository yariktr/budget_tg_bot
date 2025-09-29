import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile  # Правильный импорт
from database import Database
import matplotlib.pyplot as plt
import io
from datetime import datetime


class BotManager:
    def __init__(self, token):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.router = Router()
        self.db = Database()
        self.setup_handlers()
        self.dp.include_router(self.router)

    def setup_handlers(self):
        @self.router.message(Command("start"))
        async def cmd_start(message: Message):
            user_id = message.from_user.id
            username = message.from_user.username or "unknown"
            self.db.register_user(user_id, username)
            await message.answer("Добро пожаловать! Бот для учёта расходов готов. Используйте команды:\n"
                                "/add_expense <сумма> <категория> — добавить расход\n"
                                "/report <month|year> — отчёт по расходам\n"
                                "/top_category — категория с наибольшими тратами\n"
                                "/stats <month|year> [категория] — статистика расходов")

        @self.router.message(Command("add_expense"))
        async def cmd_add_expense(message: Message):
            try:
                _, amount, category = message.text.split(maxsplit=2)
                amount = float(amount)
                self.db.add_expense(message.from_user.id, amount, category.upper())
                await message.answer(f"Расход {amount} в категории {category.upper()} добавлен")
            except ValueError:
                await message.answer("Используйте: /add_expense <сумма> <категория>")

        @self.router.message(Command("report"))
        async def cmd_report(message: Message):
            try:
                _, period = message.text.split(maxsplit=1)
                if period not in ["month", "year"]:
                    raise ValueError
                report = self.db.get_report(message.from_user.id, period)
                if not report:
                    await message.answer(f"Нет расходов за {period}")
                    return
                response = f"Отчёт за {period}:\n"
                for category, total in report:
                    response += f"{category}: {total:.2f}\n"
                await message.answer(response)
            except ValueError:
                await message.answer("Используйте: /report <month|year>")

        @self.router.message(Command("top_category"))
        async def cmd_top_category(message: Message):
            top = self.db.get_top_category(message.from_user.id)
            if top:
                category, total = top
                await message.answer(f"Топовая категория: {category} ({total:.2f})")
            else:
                await message.answer("Нет расходов")

        @self.router.message(Command("stats"))
        async def cmd_stats(message: Message):
            try:
                parts = message.text.split(maxsplit=2)
                period = parts[1] if len(parts) > 1 else None
                category = parts[2].upper() if len(parts) > 2 else None
                
                if period not in ["month", "year"]:
                    raise ValueError
                stats = self.db.get_stats(message.from_user.id, period, category)
                if not stats:
                    await message.answer(f"Нет данных за {period}")
                    return

                print(stats)
                
                plt.figure(figsize=(8, 6))
                categories, amounts = zip(*stats)
                plt.bar(categories, amounts, color='#1f77b4')
                plt.xlabel("Категории")
                plt.ylabel("Сумма")
                plt.title(f"Статистика за {period}")
                plt.tight_layout()

                buf = io.BytesIO()
                plt.savefig(buf, format="png")
                buf.seek(0)
                
                # ИСПРАВЛЕНО: используем BufferedInputFile правильно
                input_file = BufferedInputFile(buf.getvalue(), filename="stats.png")
                await message.answer_photo(input_file, caption=f"Статистика за {period}")
                
                plt.close()
                buf.close()
                
            except ValueError:
                await message.answer("Используйте: /stats <month|year> [категория]")

    async def start(self):
        await self.dp.start_polling(self.bot)

    async def stop(self):
        self.db.close()
        await self.bot.session.close()