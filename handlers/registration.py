from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
from database.db_handler import DatabaseHandler
from keyboards.menu import get_cancel_registration_keyboard, get_main_inline_keyboard
from states.user_states import AuthStates
from utils.validators import validate_phone_number, format_phone_number, validate_username
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

async def start_registration(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 Регистрация\n\nДля регистрации потребуется:\n• Номер телефона\n• Логин\n• Пароль\n• ФИО\n\nПоделитесь номером телефона:",
        reply_markup=get_cancel_registration_keyboard()
    )
    await AuthStates.waiting_for_phone.set()

async def process_phone(message: Message, state: FSMContext):
    """Обработка номера телефона"""
    if message.contact and message.contact.phone_number:
        phone_number = message.contact.phone_number
    else:
        phone_number = message.text.strip()
    
    formatted_phone = format_phone_number(phone_number)
    
    if not validate_phone_number(formatted_phone):
        await message.answer(
            "❌ Неверный формат номера.\n"
            "✅ Правильный формат: +7XXXXXXXXXX\n"
            "📱 Пример: +79123456789\n\n"
            "Попробуйте еще раз:",
            reply_markup=get_cancel_registration_keyboard()
        )
        return
    
    # Проверяем, не занят ли номер телефона
    db = DatabaseHandler('users.db')
    if db.is_phone_taken(formatted_phone):
        await message.answer(
            "❌ Этот номер телефона уже зарегистрирован.\n"
            "🔐 Если это ваш номер, войдите в систему\n"
            "📱 Или используйте другой номер:\n\n"
            "Попробуйте еще раз:",
            reply_markup=get_cancel_registration_keyboard()
        )
        return
    
    async with state.proxy() as data:
        data['phone'] = formatted_phone
    
    await message.answer(
        "✅ Номер принят!\n\n"
        "Теперь придумайте уникальный логин:\n"
        "• Только латинские буквы a-z, A-Z\n"
        "• Цифры 0-9\n"
        "• Нижнее подчеркивание _\n"
        "• Длина: 3-20 символов\n\n"
        "Введите логин:",
        reply_markup=get_cancel_registration_keyboard()
    )
    await AuthStates.waiting_for_username.set()

async def process_username_registration(message: Message, state: FSMContext):
    username = message.text.strip()
    
    if not validate_username(username):
        await message.answer(
            "❌ Неверный формат логина.\n"
            "✅ Разрешенные символы:\n"
            "• Латинские буквы: a-z, A-Z\n"
            "• Цифры: 0-9\n"
            "• Нижнее подчеркивание: _\n"
            "• Длина: 3-20 символов\n\n"
            "Попробуйте еще раз:",
            reply_markup=get_cancel_registration_keyboard()
        )
        return
    
    db = DatabaseHandler('users.db')
    
    # Проверяем, не занят ли логин
    if db.is_username_taken(username):
        await message.answer(
            "❌ Этот логин уже занят.\n"
            "💡 Попробуйте добавить цифры или изменить логин\n"
            "📝 Примеры: ivan_2024, alex_winner, max007\n\n"
            "Введите другой логин:",
            reply_markup=get_cancel_registration_keyboard()
        )
        return
    
    async with state.proxy() as data:
        data['username'] = username
    
    await message.answer(
        "✅ Логин принят!\n\n"
        "Теперь придумайте надежный пароль:\n"
        "• Минимум 6 символов\n"
        "• Рекомендуется использовать буквы и цифры\n"
        "• Не используйте простые пароли\n\n"
        "Введите пароль:",
        reply_markup=get_cancel_registration_keyboard()
    )
    await AuthStates.waiting_for_password.set()

async def process_password_registration(message: Message, state: FSMContext):
    password = message.text.strip()
    
    if len(password) < 6:
        await message.answer("❌ Пароль слишком короткий. Минимум 6 символов:", reply_markup=get_cancel_registration_keyboard())
        return
    
    async with state.proxy() as data:
        data['password'] = password
    
    await message.answer("✅ Пароль принят!\n\nВведите ФИО:", reply_markup=get_cancel_registration_keyboard())
    await AuthStates.waiting_for_full_name.set()

async def process_full_name_registration(message: Message, state: FSMContext):
    full_name = message.text.strip()
    
    if len(full_name) < 2:
        await message.answer("❌ ФИО слишком короткое. Минимум 2 символа:", reply_markup=get_cancel_registration_keyboard())
        return
    
    async with state.proxy() as data:
        phone = data['phone']
        username = data['username']
        password = data['password']
    
    db = DatabaseHandler('users.db')
    
    # Финальная проверка перед регистрацией (на случай параллельных запросов)
    if db.is_phone_taken(phone):
        await message.answer("❌ Этот номер телефона уже зарегистрирован. Начните регистрацию заново.", reply_markup=get_cancel_registration_keyboard())
        await state.finish()
        return
    
    if db.is_username_taken(username):
        await message.answer("❌ Этот логин уже занят. Начните регистрацию заново.", reply_markup=get_cancel_registration_keyboard())
        await state.finish()
        return
    
    # Регистрируем пользователя
    if db.register_user(message.from_user.id, phone, username, hash_password(password), full_name):
        await message.answer("🎉 Регистрация завершена!", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("Выберите действие:", reply_markup=get_main_inline_keyboard())
    else:
        await message.answer("❌ Ошибка регистрации. Попробуйте позже.", reply_markup=get_cancel_registration_keyboard())
    
    await state.finish()

async def cancel_registration(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.edit_text("❌ Регистрация отменена.", reply_markup=types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("🔙 Назад", callback_data="start")
    ))

def register_registration_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(start_registration, lambda c: c.data == "register", state="*")
    dp.register_message_handler(process_phone, content_types=[types.ContentType.CONTACT, types.ContentType.TEXT], state=AuthStates.waiting_for_phone)
    dp.register_message_handler(process_username_registration, state=AuthStates.waiting_for_username)
    dp.register_message_handler(process_password_registration, state=AuthStates.waiting_for_password)
    dp.register_message_handler(process_full_name_registration, state=AuthStates.waiting_for_full_name)
    dp.register_callback_query_handler(cancel_registration, lambda c: c.data == "start", state=AuthStates.all_states)