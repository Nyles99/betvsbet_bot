import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from handlers.start import register_start_handlers
from handlers.registration import register_registration_handlers
from handlers.login import register_login_handlers
from handlers.profile import register_profile_handlers
from handlers.callbacks import register_callback_handlers
from handlers.admin import register_admin_handlers
from utils.match_checker import start_match_checker

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def main():
    """Основная функция запуска бота"""
    # Получаем токен из переменных окружения
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN environment variable is not set")
        logging.info("Пожалуйста, создайте файл .env с BOT_TOKEN=your_bot_token")
        return
    
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    
    # Регистрация обработчиков
    register_start_handlers(dp)
    register_registration_handlers(dp)
    register_login_handlers(dp)
    register_profile_handlers(dp)
    register_callback_handlers(dp)
    register_admin_handlers(dp)
    
    # Запуск бота
    try:
        logging.info("Бот запущен...")
        
        # Запускаем фоновую задачу проверки матчей
        asyncio.create_task(start_match_checker())
        
        await dp.start_polling()
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())