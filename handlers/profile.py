from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
from database.db_handler import DatabaseHandler
from keyboards.menu import get_profile_inline_keyboard
from utils.validators import validate_username, validate_full_name
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

async def process_full_name(message: Message, state: FSMContext):
    """Обработка нового ФИО"""
    new_full_name = message.text.strip()
    
    if validate_full_name(new_full_name):
        db = DatabaseHandler('users.db')
        user_id = message.from_user.id
        
        if db.update_profile(user_id, full_name=new_full_name):
            await message.answer(
                "✅ ФИО успешно обновлено!",
                reply_markup=types.ReplyKeyboardRemove()
            )
            await message.answer(
                "👤 Личный кабинет. Выберите действие:",
                reply_markup=get_profile_inline_keyboard()
            )
        else:
            await message.answer(
                "❌ Ошибка при обновлении ФИО.",
                reply_markup=types.ReplyKeyboardRemove()
            )
    else:
        await message.answer(
            "❌ Неверный формат ФИО. Используйте только буквы, пробелы и дефисы (2-100 символов)."
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

async def cancel_full_name(callback: CallbackQuery, state: FSMContext):
    """Отмена изменения ФИО"""
    await state.finish()
    await callback.message.edit_text(
        "❌ Изменение ФИО отменено.",
        reply_markup=get_profile_inline_keyboard()
    )

def register_profile_handlers(dp: Dispatcher):
    """Регистрация обработчиков профиля"""
    # Обработчики текстовых сообщений для FSM
    dp.register_message_handler(process_username, state=ProfileStates.waiting_for_username)
    dp.register_message_handler(process_full_name, state=ProfileStates.waiting_for_full_name)
    
    # Обработчики отмены через callback (кнопка Назад)
    dp.register_callback_query_handler(cancel_username, lambda c: c.data == "main_menu", state=ProfileStates.waiting_for_username)
    dp.register_callback_query_handler(cancel_full_name, lambda c: c.data == "main_menu", state=ProfileStates.waiting_for_full_name)