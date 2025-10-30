from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
from database.db_handler import DatabaseHandler
from keyboards.menu import get_cancel_login_keyboard, get_main_inline_keyboard, get_start_keyboard
from states.user_states import LoginStates
from utils.validators import validate_username
import hashlib

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

async def start_login(callback: CallbackQuery, state: FSMContext):
    """Начало процесса входа"""
    await callback.message.edit_text(
        "🚪 Вход в систему\n\n"
        "Пожалуйста, введите ваш логин:",
        reply_markup=get_cancel_login_keyboard()
    )
    await LoginStates.waiting_for_username.set()

async def process_username_login(message: Message, state: FSMContext):
    """Обработка логина при входе"""
    username = message.text.strip()
    
    db = DatabaseHandler('users.db')
    
    # Проверяем существование пользователя
    user = db.get_user_by_username(username)
    if not user:
        await message.answer(
            "❌ Пользователь с таким логином не найден. Попробуйте еще раз:",
            reply_markup=get_cancel_login_keyboard()
        )
        return
    
    async with state.proxy() as data:
        data['username'] = username
        data['user_id'] = user.user_id
    
    await message.answer(
        "✅ Логин принят!\n\n"
        "Теперь введите ваш пароль:",
        reply_markup=get_cancel_login_keyboard()
    )
    await LoginStates.waiting_for_password.set()

async def process_password_login(message: Message, state: FSMContext):
    """Обработка пароля при входе"""
    password = message.text.strip()
    hashed_password = hash_password(password)
    
    async with state.proxy() as data:
        username = data['username']
        user_id = data['user_id']
    
    db = DatabaseHandler('users.db')
    
    # Проверяем пароль
    if db.verify_password(user_id, hashed_password):
        # Обновляем последний вход
        db.update_last_login(user_id)
        
        await message.answer(
            "✅ Вход выполнен успешно!\n\n"
            "Добро пожаловать обратно!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await message.answer(
            "Выберите действие:",
            reply_markup=get_main_inline_keyboard()
        )
    else:
        await message.answer(
            "❌ Неверный пароль. Попробуйте еще раз:",
            reply_markup=get_cancel_login_keyboard()
        )
    
    await state.finish()

async def cancel_login(callback: CallbackQuery, state: FSMContext):
    """Отмена входа"""
    await state.finish()
    await callback.message.edit_text(
        "❌ Вход отменен.",
        reply_markup=get_start_keyboard()
    )

def register_login_handlers(dp: Dispatcher):
    """Регистрация обработчиков входа"""
    # Начало входа
    dp.register_callback_query_handler(start_login, lambda c: c.data == "login", state="*")
    
    # Обработка логина и пароля
    dp.register_message_handler(process_username_login, state=LoginStates.waiting_for_username)
    dp.register_message_handler(process_password_login, state=LoginStates.waiting_for_password)
    
    # Отмена входа
    dp.register_callback_query_handler(cancel_login, lambda c: c.data == "start", state=LoginStates.all_states)