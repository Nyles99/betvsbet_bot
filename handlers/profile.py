from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
from database.db_handler import DatabaseHandler
from keyboards.menu import get_profile_inline_keyboard
from utils.validators import validate_username
from states.user_states import ProfileStates

async def process_username(message: Message, state: FSMContext):
    """Обработка нового логина"""
    new_username = message.text.strip()
    
    if validate_username(new_username):
        db = DatabaseHandler('users.db')
        user_id = message.from_user.id
        
        if db.update_profile(user_id, username=new_username):
            await message.answer(
                "✅ Логин успешно обновлен!",
                reply_markup=types.ReplyKeyboardRemove()
            )
            await message.answer(
                "👤 Личный кабинет. Выберите действие:",
                reply_markup=get_profile_inline_keyboard()
            )
        else:
            await message.answer(
                "❌ Ошибка при обновлении логина.",
                reply_markup=types.ReplyKeyboardRemove()
            )
    else:
        await message.answer(
            "❌ Неверный формат логина. Используйте только латинские буквы, цифры и нижнее подчеркивание (3-20 символов)."
        )
        return
    
    await state.finish()

async def cancel_username(callback: CallbackQuery, state: FSMContext):
    """Отмена изменения логина"""
    await state.finish()
    await callback.message.edit_text(
        "❌ Изменение логина отменено.",
        reply_markup=get_profile_inline_keyboard()
    )

def register_profile_handlers(dp: Dispatcher):
    """Регистрация обработчиков профиля"""
    # Обработчики текстовых сообщений для FSM
    dp.register_message_handler(process_username, state=ProfileStates.waiting_for_username)
    
    # Обработчики отмены через callback (кнопка Назад)
    dp.register_callback_query_handler(cancel_username, lambda c: c.data == "main_menu", state=ProfileStates.waiting_for_username)