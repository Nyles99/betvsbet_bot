from aiogram import Dispatcher, types
from aiogram.types import Message
from database.db_handler import DatabaseHandler
from keyboards.menu import get_start_keyboard, get_phone_keyboard, get_main_inline_keyboard

async def start_command(message: Message):
    """Обработчик команды /start"""
    db = DatabaseHandler('users.db')
    user_id = message.from_user.id
    
    if db.user_exists(user_id):
        # Пользователь уже зарегистрирован
        await message.answer(
            "Добро пожаловать назад! Выберите действие:",
            reply_markup=get_main_inline_keyboard()
        )
    else:
        # Новый пользователь - показываем стартовое меню
        await message.answer(
            "👋 Добро пожаловать в BetVsBet Bot!\n\n"
            "Для использования бота необходимо войти или зарегистрироваться.",
            reply_markup=get_start_keyboard()
        )

async def back_to_start(callback: types.CallbackQuery):
    """Возврат к стартовому меню"""
    await callback.message.edit_text(
        "👋 Добро пожаловать в BetVsBet Bot!\n\n"
        "Для использования бота необходимо войти или зарегистрироваться.",
        reply_markup=get_start_keyboard()
    )

async def back_to_main(message: Message):
    """Возврат в главное меню"""
    db = DatabaseHandler('users.db')
    user_id = message.from_user.id
    
    if db.user_exists(user_id):
        await message.answer(
            "Главное меню:",
            reply_markup=get_main_inline_keyboard()
        )
    else:
        await message.answer(
            "Для начала работы войдите или зарегистрируйтесь:",
            reply_markup=get_start_keyboard()
        )

def register_start_handlers(dp: Dispatcher):
    """Регистрация обработчиков стартовых команд"""
    dp.register_message_handler(start_command, commands=['start'])
    dp.register_message_handler(back_to_main, lambda message: message.text == '🔙 Назад')
    dp.register_callback_query_handler(back_to_start, lambda c: c.data == "start")