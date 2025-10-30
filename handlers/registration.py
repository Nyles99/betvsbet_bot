from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
from database.db_handler import DatabaseHandler
from keyboards.menu import (
    get_phone_keyboard, 
    get_cancel_registration_keyboard,
    get_main_inline_keyboard,
    get_start_keyboard
)
from states.user_states import RegistrationStates
from utils.validators import validate_phone_number, format_phone_number, validate_username
import hashlib

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

async def start_registration(callback: CallbackQuery, state: FSMContext):
    """Начало процесса регистрации"""
    await callback.message.edit_text(
        "📝 Регистрация\n\n"
        "Для регистрации нам потребуется:\n"
        "1. Ваш номер телефона\n" 
        "2. Логин\n"
        "3. Пароль\n\n"
        "Давайте начнем! Пожалуйста, поделитесь вашим номером телефона:",
        reply_markup=get_cancel_registration_keyboard()
    )
    await RegistrationStates.waiting_for_phone.set()

async def process_phone_contact(message: Message, state: FSMContext):
    """Обработка номера телефона через контакт"""
    if message.contact and message.contact.phone_number:
        phone_number = message.contact.phone_number
        formatted_phone = format_phone_number(phone_number)
        
        if validate_phone_number(formatted_phone):
            async with state.proxy() as data:
                data['phone'] = formatted_phone
            
            await message.answer(
                "✅ Номер телефона получен!\n\n"
                "Теперь придумайте и введите логин (только латинские буквы, цифры и нижнее подчеркивание, 3-20 символов):",
                reply_markup=get_cancel_registration_keyboard()
            )
            await RegistrationStates.waiting_for_username.set()
        else:
            await message.answer(
                "❌ Неверный формат номера телефона. Пожалуйста, используйте номер в формате +7.",
                reply_markup=get_cancel_registration_keyboard()
            )
    else:
        await message.answer(
            "❌ Не удалось получить номер телефона. Пожалуйста, поделитесь номером через кнопку.",
            reply_markup=get_phone_keyboard()
        )

async def process_phone_text(message: Message, state: FSMContext):
    """Обработка номера телефона, введенного вручную"""
    phone_number = message.text.strip()
    formatted_phone = format_phone_number(phone_number)
    
    if validate_phone_number(formatted_phone):
        async with state.proxy() as data:
            data['phone'] = formatted_phone
        
        await message.answer(
            "✅ Номер телефона принят!\n\n"
            "Теперь придумайте и введите логин (только латинские буквы, цифры и нижнее подчеркивание, 3-20 символов):",
            reply_markup=get_cancel_registration_keyboard()
        )
        await RegistrationStates.waiting_for_username.set()
    else:
        await message.answer(
            "❌ Неверный формат номера телефона. Пожалуйста, введите номер в формате +7XXXXXXXXXX:",
            reply_markup=get_cancel_registration_keyboard()
        )

async def process_username_registration(message: Message, state: FSMContext):
    """Обработка логина при регистрации"""
    username = message.text.strip()
    
    if validate_username(username):
        db = DatabaseHandler('users.db')
        
        # Проверяем, не занят ли логин
        if db.is_username_taken(username):
            await message.answer(
                "❌ Этот логин уже занят. Пожалуйста, выберите другой логин:",
                reply_markup=get_cancel_registration_keyboard()
            )
            return
        
        async with state.proxy() as data:
            data['username'] = username
        
        await message.answer(
            "✅ Логин принят!\n\n"
            "Теперь придумайте и введите пароль (минимум 6 символов):",
            reply_markup=get_cancel_registration_keyboard()
        )
        await RegistrationStates.waiting_for_password.set()
    else:
        await message.answer(
            "❌ Неверный формат логина. Используйте только латинские буквы, цифры и нижнее подчеркивание (3-20 символов):",
            reply_markup=get_cancel_registration_keyboard()
        )

async def process_password_registration(message: Message, state: FSMContext):
    """Обработка пароля при регистрации"""
    password = message.text.strip()
    
    if len(password) < 6:
        await message.answer(
            "❌ Пароль слишком короткий. Минимальная длина - 6 символов. Попробуйте еще раз:",
            reply_markup=get_cancel_registration_keyboard()
        )
        return
    
    async with state.proxy() as data:
        phone = data['phone']
        username = data['username']
        hashed_password = hash_password(password)
    
    db = DatabaseHandler('users.db')
    user_id = message.from_user.id
    
    # Регистрируем пользователя
    if db.register_user(user_id, phone, username, hashed_password):
        await message.answer(
            "🎉 Регистрация успешно завершена!\n\n"
            "Теперь вы можете использовать все возможности бота.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await message.answer(
            "Выберите действие:",
            reply_markup=get_main_inline_keyboard()
        )
    else:
        await message.answer(
            "❌ Ошибка при регистрации. Возможно, этот номер телефона уже зарегистрирован.",
            reply_markup=get_cancel_registration_keyboard()
        )
    
    await state.finish()

async def cancel_registration(callback: CallbackQuery, state: FSMContext):
    """Отмена регистрации"""
    await state.finish()
    await callback.message.edit_text(
        "❌ Регистрация отменена.",
        reply_markup=get_start_keyboard()
    )

def register_registration_handlers(dp: Dispatcher):
    """Регистрация обработчиков регистрации"""
    # Начало регистрации
    dp.register_callback_query_handler(start_registration, lambda c: c.data == "register", state="*")
    
    # Обработка телефона
    dp.register_message_handler(process_phone_contact, content_types=types.ContentType.CONTACT, state=RegistrationStates.waiting_for_phone)
    dp.register_message_handler(process_phone_text, state=RegistrationStates.waiting_for_phone)
    
    # Обработка логина и пароля
    dp.register_message_handler(process_username_registration, state=RegistrationStates.waiting_for_username)
    dp.register_message_handler(process_password_registration, state=RegistrationStates.waiting_for_password)
    
    # Отмена регистрации
    dp.register_callback_query_handler(cancel_registration, lambda c: c.data == "start", state=RegistrationStates.all_states)