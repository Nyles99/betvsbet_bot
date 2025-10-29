from aiogram import Dispatcher, types
from aiogram.types import Message
from database.db_handler import DatabaseHandler
from keyboards.menu import get_main_inline_keyboard, remove_keyboard
from utils.validators import validate_phone_number, format_phone_number

async def handle_contact(message: Message):
    """Обработка полученного номера телефона через контакт"""
    db = DatabaseHandler('users.db')
    user_id = message.from_user.id
    contact = message.contact
    
    if contact and contact.phone_number:
        phone_number = contact.phone_number
        
        # Форматируем номер телефона
        formatted_phone = format_phone_number(phone_number)
        
        if validate_phone_number(formatted_phone):
            if db.add_user(user_id, formatted_phone):
                await message.answer(
                    "✅ Регистрация успешно завершена! Теперь вы можете использовать бота.",
                    reply_markup=remove_keyboard()
                )
                await message.answer(
                    "Выберите действие:",
                    reply_markup=get_main_inline_keyboard()
                )
            else:
                await message.answer(
                    "❌ Этот номер телефона уже зарегистрирован.",
                    reply_markup=remove_keyboard()
                )
        else:
            await message.answer(
                "❌ Неверный формат номера телефона. Пожалуйста, используйте номер в формате +7.",
                reply_markup=remove_keyboard()
            )
    else:
        await message.answer(
            "❌ Не удалось получить номер телефона.",
            reply_markup=remove_keyboard()
        )

async def handle_phone_text(message: Message):
    """Обработка номера телефона, введенного вручную"""
    db = DatabaseHandler('users.db')
    user_id = message.from_user.id
    
    phone_number = message.text.strip()
    
    # Форматируем номер телефона
    formatted_phone = format_phone_number(phone_number)
    
    if validate_phone_number(formatted_phone):
        if db.add_user(user_id, formatted_phone):
            await message.answer(
                "✅ Регистрация успешно завершена! Теперь вы можете использовать бота.",
                reply_markup=remove_keyboard()
            )
            await message.answer(
                "Выберите действие:",
                reply_markup=get_main_inline_keyboard()
            )
        else:
            await message.answer(
                "❌ Этот номер телефона уже зарегистрирован.",
                reply_markup=remove_keyboard()
            )
    else:
        await message.answer(
            "❌ Неверный формат номера телефона. Пожалуйста, введите номер в формате +7XXXXXXXXXX:",
            reply_markup=remove_keyboard()
        )

def register_auth_handlers(dp: Dispatcher):
    dp.register_message_handler(handle_contact, content_types=types.ContentType.CONTACT)
    dp.register_message_handler(handle_phone_text, lambda message: message.text and any(char.isdigit() for char in message.text))