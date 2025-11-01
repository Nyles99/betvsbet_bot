from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
from database.db_handler import DatabaseHandler
from keyboards.menu import (
    get_main_inline_keyboard, 
    get_phone_keyboard, 
    get_cancel_login_keyboard,
    remove_keyboard
)
from states.user_states import AuthStates
import hashlib
import logging

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

async def login_start(callback: CallbackQuery, state: FSMContext):
    """Начало процесса входа"""
    await state.finish()
    
    await callback.message.edit_text(
        "🚪 Вход в систему\n\n"
        "Для входа введите ваш логин:",
        reply_markup=get_cancel_login_keyboard()
    )
    await AuthStates.waiting_for_username.set()

async def process_login_username(message: Message, state: FSMContext):
    """Обработка логина при входе"""
    username = message.text.strip()
    
    db = DatabaseHandler('users.db')
    user = db.get_user_by_username(username)
    
    if not user:
        await message.answer(
            "❌ Пользователь с таким логином не найден.\n"
            "Проверьте логин или зарегистрируйтесь:\n\n"
            "Введите логин еще раз:",
            reply_markup=get_cancel_login_keyboard()
        )
        return
    
    async with state.proxy() as data:
        data['username'] = username
        data['user_id'] = user.user_id
    
    await message.answer(
        "🔐 Введите ваш пароль:",
        reply_markup=get_cancel_login_keyboard()
    )
    await AuthStates.waiting_for_password.set()

async def process_login_password(message: Message, state: FSMContext):
    """Обработка пароля при входе"""
    password = message.text.strip()
    
    async with state.proxy() as data:
        username = data['username']
        user_id = data['user_id']
    
    db = DatabaseHandler('users.db')
    hashed_password = hash_password(password)
    
    if db.verify_password(user_id, hashed_password):
        # Обновляем время последнего входа
        db.update_last_login(user_id)
        
        # Получаем актуальные данные пользователя
        user = db.get_user(user_id)
        
        await message.answer(
            f"✅ Вход выполнен успешно!\n\n"
            f"👤 Добро пожаловать, {user.full_name or user.username}!\n"
            f"📱 Ваш номер: {user.phone_number}",
            reply_markup=remove_keyboard()
        )
        
        await message.answer(
            "📍 Главное меню. Выберите действие:",
            reply_markup=get_main_inline_keyboard()
        )
        
        # Логируем успешный вход
        logging.info(f"User {user_id} ({username}) successfully logged in")
        
    else:
        await message.answer(
            "❌ Неверный пароль.\n\n"
            "Попробуйте еще раз:\n"
            "Введите пароль:",
            reply_markup=get_cancel_login_keyboard()
        )
        return
    
    await state.finish()

async def cancel_login(callback: CallbackQuery, state: FSMContext):
    """Отмена процесса входа"""
    await state.finish()
    await callback.message.edit_text(
        "❌ Вход отменен.",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        )
    )

async def login_retry(callback: CallbackQuery, state: FSMContext):
    """Повторная попытка входа"""
    await state.finish()
    await callback.message.edit_text(
        "🚪 Вход в систему\n\n"
        "Для входа введите ваш логин:",
        reply_markup=get_cancel_login_keyboard()
    )
    await AuthStates.waiting_for_username.set()

async def handle_login_phone(message: Message, state: FSMContext):
    """Обработка номера телефона для входа (альтернативный метод)"""
    if message.contact:
        phone_number = message.contact.phone_number
        # Нормализуем номер телефона
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        
        db = DatabaseHandler('users.db')
        user = None
        
        # Ищем пользователя по номеру телефона
        with db.conn:
            cursor = db.conn.cursor()
            cursor.execute('SELECT * FROM users WHERE phone_number = ?', (phone_number,))
            row = cursor.fetchone()
            if row:
                user = type('User', (), {
                    'user_id': row[0],
                    'phone_number': row[1],
                    'username': row[2],
                    'full_name': row[3]
                })()
        
        if user:
            await message.answer(
                f"✅ Найден пользователь: {user.full_name or user.username}\n\n"
                f"🔐 Введите ваш пароль для входа:",
                reply_markup=get_cancel_login_keyboard()
            )
            async with state.proxy() as data:
                data['username'] = user.username
                data['user_id'] = user.user_id
            await AuthStates.waiting_for_password.set()
        else:
            await message.answer(
                "❌ Пользователь с таким номером телефона не найден.\n\n"
                "Возможно, вам нужно зарегистрироваться:",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("📝 Регистрация", callback_data="register"),
                    types.InlineKeyboardButton("🔄 Попробовать другой номер", callback_data="login")
                )
            )
    else:
        await message.answer(
            "📱 Пожалуйста, используйте кнопку для отправки номера телефона:",
            reply_markup=get_phone_keyboard()
        )

def register_login_handlers(dp: Dispatcher):
    """Регистрация обработчиков входа"""
    
    # Обработчики колбэков
    dp.register_callback_query_handler(login_start, lambda c: c.data == "login", state="*")
    dp.register_callback_query_handler(login_retry, lambda c: c.data == "login_retry", state="*")
    dp.register_callback_query_handler(cancel_login, lambda c: c.data == "start", state=AuthStates.all_states)
    
    # Обработчики сообщений для FSM
    dp.register_message_handler(process_login_username, state=AuthStates.waiting_for_username)
    dp.register_message_handler(process_login_password, state=AuthStates.waiting_for_password)
    
    # Обработчик номера телефона (альтернативный метод входа)
    dp.register_message_handler(handle_login_phone, content_types=['contact', 'text'], state=AuthStates.waiting_for_phone)