import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from database import init_db
from handlers import start, catalog, payment, admin, promo

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    logger.info("Инициализация базы данных...")
    await init_db()
    logger.info("База данных инициализирована")
    
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    
    dp = Dispatcher()
    
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(promo.router)
    dp.include_router(payment.router)
    
    bot_info = await bot.get_me()
    logger.info(f"Бот запущен: @{bot_info.username}")
    logger.info(f"ID бота: {bot_info.id}")
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        logger.info("=" * 50)
        logger.info("LUNOST SHOP BOT - Запуск")
        logger.info("=" * 50)
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
