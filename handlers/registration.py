from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
from database.db_handler import DatabaseHandler
from keyboards.menu import (
    get_main_inline_keyboard, 
    get_phone_keyboard, 
    get_cancel_registration_keyboard,
    get_start_keyboard,
    remove_keyboard
)
from states.user_states import AuthStates
from utils.validators import validate_phone_number, validate_username, format_phone_number
import hashlib
import logging

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

async def register_start(callback: CallbackQuery, state: FSMContext):
    """Начало процесса регистрации"""
    logging.info(f"Начало регистрации для пользователя {callback.from_user.id}")
    
    await state.finish()
    
    try:
        # Вместо редактирования сообщения, отправляем новое с правильной клавиатурой
        await callback.message.answer(
            "📝 Регистрация\n\n"
            "Для регистрации отправьте ваш номер телефона:",
            reply_markup=get_phone_keyboard()
        )
        await AuthStates.waiting_for_phone.set()
        logging.info(f"Состояние установлено для пользователя {callback.from_user.id}")
    except Exception as e:
        logging.error(f"Ошибка в register_start: {e}")
        await callback.answer("❌ Ошибка при начале регистрации", show_alert=True)

async def process_phone_registration(message: Message, state: FSMContext):
    """Обработка номера телефона при регистрации"""
    logging.info(f"Обработка телефона для пользователя {message.from_user.id}")
    
    if message.contact:
        phone_number = message.contact.phone_number
    else:
        phone_number = message.text
    
    # Форматируем номер телефона
    formatted_phone = format_phone_number(phone_number)
    
    if not validate_phone_number(formatted_phone):
        await message.answer(
            "❌ Неверный формат номера телефона. Пожалуйста, используйте номер в формате +7XXXXXXXXXX:",
            reply_markup=get_cancel_registration_keyboard()
        )
        return
    
    # Проверяем, не занят ли номер
    db = DatabaseHandler('users.db')
    if db.is_phone_taken(formatted_phone):
        await message.answer(
            "❌ Этот номер телефона уже зарегистрирован. Пожалуйста, используйте другой номер:",
            reply_markup=get_cancel_registration_keyboard()
        )
        return
    
    # Сохраняем номер телефона в state
    async with state.proxy() as data:
        data['phone'] = formatted_phone
    
    await message.answer(
        "👤 Введите ваш логин (только латинские буквы, цифры и нижнее подчеркивание, 3-20 символов):",
        reply_markup=get_cancel_registration_keyboard()
    )
    await AuthStates.waiting_for_username.set()

async def process_username_registration(message: Message, state: FSMContext):
    """Обработка логина при регистрации"""
    username = message.text.strip()
    
    if not validate_username(username):
        await message.answer(
            "❌ Неверный формат логина. Используйте только латинские буквы, цифры и нижнее подчеркивание (3-20 символов):",
            reply_markup=get_cancel_registration_keyboard()
        )
        return
    
    # Проверяем, не занят ли логин
    db = DatabaseHandler('users.db')
    if db.is_username_taken(username):
        await message.answer(
            "❌ Этот логин уже занят. Пожалуйста, выберите другой логин:",
            reply_markup=get_cancel_registration_keyboard()
        )
        return
    
    # Сохраняем логин в state
    async with state.proxy() as data:
        data['username'] = username
    
    await message.answer(
        "🔐 Введите ваш пароль (минимум 6 символов):",
        reply_markup=get_cancel_registration_keyboard()
    )
    await AuthStates.waiting_for_password.set()

async def process_password_registration(message: Message, state: FSMContext):
    """Обработка пароля при регистрации"""
    password = message.text.strip()
    
    if len(password) < 6:
        await message.answer(
            "❌ Пароль слишком короткий. Минимальная длина - 6 символов. Попробуйте еще раз:",
            reply_markup=get_cancel_registration_keyboard()
        )
        return
    
    # Хешируем пароль и сохраняем в state
    hashed_password = hash_password(password)
    async with state.proxy() as data:
        data['password'] = hashed_password
    
    await message.answer(
        "📛 Введите ваше ФИО (имя и фамилия):",
        reply_markup=get_cancel_registration_keyboard()
    )
    await AuthStates.waiting_for_full_name.set()

async def process_full_name_registration(message: Message, state: FSMContext):
    """Обработка ФИО и завершение регистрации"""
    full_name = message.text.strip()
    
    # Получаем все данные из state
    async with state.proxy() as data:
        phone = data.get('phone')
        username = data.get('username')
        password = data.get('password')
    
    # Проверяем, что все данные есть
    if not all([phone, username, password]):
        logging.error(f"Данные не найдены для пользователя {message.from_user.id}: phone={phone}, username={username}, password={'*' if password else 'None'}")
        await message.answer(
            "❌ Ошибка при регистрации. Данные не найдены. Пожалуйста, начните регистрацию заново.",
            reply_markup=get_start_keyboard()
        )
        await state.finish()
        return
    
    db = DatabaseHandler('users.db')
    user_id = message.from_user.id
    
    # Регистрируем пользователя
    if db.register_user(user_id, phone, username, password, full_name):
        await message.answer(
            f"✅ Регистрация успешно завершена!\n\n"
            f"👤 Добро пожаловать, {full_name}!\n"
            f"📱 Ваш номер: {phone}\n"
            f"🔐 Логин: {username}",
            reply_markup=remove_keyboard()
        )
        
        await message.answer(
            "📍 Главное меню. Выберите действие:",
            reply_markup=get_main_inline_keyboard()
        )
        
        # Логируем успешную регистрацию
        logging.info(f"New user registered: {user_id} ({username})")
        
    else:
        await message.answer(
            "❌ Ошибка при регистрации. Возможно, такой логин или номер телефона уже заняты.",
            reply_markup=get_start_keyboard()
        )
    
    await state.finish()

async def cancel_registration(callback: CallbackQuery, state: FSMContext):
    """Отмена регистрации"""
    await state.finish()
    # Используем answer вместо edit_text для отмены
    await callback.message.answer(
        "❌ Регистрация отменена.",
        reply_markup=get_start_keyboard()
    )

def register_registration_handlers(dp: Dispatcher):
    """Регистрация обработчиков регистрации"""
    
    # Обработчики колбэков
    dp.register_callback_query_handler(register_start, lambda c: c.data == "register", state="*")
    dp.register_callback_query_handler(cancel_registration, lambda c: c.data == "start", state=AuthStates.all_states)
    
    # Обработчики сообщений для FSM
    dp.register_message_handler(process_phone_registration, content_types=['contact', 'text'], state=AuthStates.waiting_for_phone)
    dp.register_message_handler(process_username_registration, state=AuthStates.waiting_for_username)
    dp.register_message_handler(process_password_registration, state=AuthStates.waiting_for_password)
    dp.register_message_handler(process_full_name_registration, state=AuthStates.waiting_for_full_name)
    
    logging.info("Registration handlers registered successfully")