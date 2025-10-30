from aiogram import Dispatcher, types
from aiogram.types import Message
from database.db_handler import DatabaseHandler
from keyboards.menu import get_start_keyboard, get_phone_keyboard, get_main_inline_keyboard

async def start_command(message: Message):
    """Обработчик команды /start"""
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

def register_start_handlers(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=['start'])
    dp.register_callback_query_handler(back_to_start, lambda c: c.data == "start")