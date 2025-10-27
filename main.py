import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config_bot import config
from database import db
from handlers.start import register_handlers_start
from handlers.registration import register_handlers_registration
from handlers.login import register_handlers_login
from handlers.profile import register_handlers_profile
from handlers.admin import register_handlers_admin
from handlers.tournaments import register_handlers_tournaments
from handlers.info import register_handlers_info
from handlers.matches import register_handlers_matches
from handlers.bets import register_handlers_bets

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def set_bot_commands(bot: Bot):
    """Установка команд бота"""
    commands = [
        types.BotCommand("start", "Запустить бота"),
        types.BotCommand("help", "Помощь"),
        types.BotCommand("admin", "Админ-панель"),
    ]
    await bot.set_my_commands(commands)

async def main():
    """Основная функция запуска бота"""
    # Проверяем наличие токена
    if not config.BOT_TOKEN:
        logger.error("Не указан BOT_TOKEN в переменных окружения!")
        return
    
    if not config.ADMIN_ID:
        logger.warning("ADMIN_ID не указан, некоторые функции могут быть недоступны")
    
    try:
        # Инициализация бота и диспетчера
        bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
        storage = MemoryStorage()
        dp = Dispatcher(bot, storage=storage)
        
        # Действия при запуске
        logger.info("Бот запускается...")
        
        # Устанавливаем команды бота
        await set_bot_commands(bot)
        
        # Создаем таблицы в базе данных
        await db.create_tables()
        logger.info("База данных инициализирована")
        
        # Создаем администратора
        if config.ADMIN_ID:
            success = await db.create_admin_user(config.ADMIN_ID)
            if success:
                logger.info(f"Администратор с ID {config.ADMIN_ID} создан/проверен")
            else:
                logger.error(f"Ошибка при создании администратора с ID {config.ADMIN_ID}")
        
        # Регистрируем обработчики
        logger.info("Регистрация обработчиков...")
        register_handlers_start(dp)
        register_handlers_registration(dp)
        register_handlers_login(dp)
        register_handlers_profile(dp)
        register_handlers_admin(dp)
        register_handlers_tournaments(dp)
        register_handlers_info(dp)
        register_handlers_matches(dp)
        register_handlers_bets(dp)
        logger.info("Все обработчики зарегистрированы")
        
        # Обработчик неизвестных команд
        @dp.message_handler()
        async def unknown_message(message: types.Message):
            """Обработка неизвестных сообщений"""
            await message.answer(
                "🤔 Я не понимаю эту команду.\n\n"
                "Используйте кнопки меню или команды:\n"
                "/start - начать работу\n"
                "/help - помощь\n"
                "/admin - админ-панель (только для администраторов)\n\n"
                "Если у вас возникли проблемы, обратитесь к администратору: @admin"
            )
        
        # Обработчик неизвестных callback-запросов
        @dp.callback_query_handler()
        async def unknown_callback(callback: types.CallbackQuery):
            """Обработка неизвестных callback-запросов"""
            await callback.answer("❌ Эта кнопка больше не активна", show_alert=True)
            # Пытаемся вернуть пользователя в главное меню
            try:
                await callback.message.answer(
                    "Произошла ошибка при обработке запроса.\n"
                    "Возвращаемся в главное меню...",
                    reply_markup=types.ReplyKeyboardRemove()
                )
                
                from handlers.start import cmd_start
                from aiogram.dispatcher import FSMContext
                state = dp.current_state(user=callback.from_user.id)
                await cmd_start(callback.message, state)
                
            except Exception as e:
                logger.error(f"Ошибка при обработке неизвестного callback: {e}")
                await callback.message.answer(
                    "Произошла ошибка. Попробуйте начать заново: /start"
                )
        
        # Запускаем бота
        logger.info("Бот успешно запущен и готов к работе")
        logger.info("Бот начинает polling...")
        await dp.start_polling()
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
    finally:
        if 'bot' in locals():
            await bot.close()
            logger.info("Бот остановлен")

if __name__ == '__main__':
    try:
        # Запускаем асинхронную функцию main
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")