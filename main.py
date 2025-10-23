import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import config
from database import db
from handlers.start import register_handlers_start
from handlers.registration import register_handlers_registration
from handlers.login import register_handlers_login
from handlers.profile import register_handlers_profile

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска бота"""
    # Проверяем наличие токена
    if not config.BOT_TOKEN:
        logger.error("Не указан BOT_TOKEN в переменных окружения!")
        return
    
    # Инициализация бота и диспетчера
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    
    # Создаем таблицы в базе данных
    await db.create_tables()
    logger.info("База данных инициализирована")
    
    # Регистрируем обработчики
    register_handlers_start(dp)
    register_handlers_registration(dp)
    register_handlers_login(dp)
    register_handlers_profile(dp)
    
    # Обработчик неизвестных команд
    @dp.message_handler()
    async def unknown_message(message: types.Message):
        await message.answer(
            "🤔 Я не понимаю эту команду.\n\n"
            "Используйте кнопки меню или команды:\n"
            "/start - начать работу\n"
            "/help - помощь"
        )
    
    # Запускаем бота
    try:
        logger.info("Бот запущен")
        await dp.start_polling()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.close()

if __name__ == '__main__':
    asyncio.run(main())