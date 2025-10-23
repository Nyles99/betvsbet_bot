from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove

from database import db
from states import ProfileStates
from keyboards import get_profile_keyboard, get_back_keyboard, get_main_menu, get_cancel_keyboard
from utils import validate_username, validate_email, validate_phone, validate_full_name

async def process_profile_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка инлайн кнопок личного кабинета"""
    user_id = callback.from_user.id
    action = callback.data
    
    # Получаем текущие данные пользователя
    user_data = await db.get_user_by_id(user_id)
    if not user_data:
        await callback.answer("❌ Ошибка: пользователь не найден")
        return
    
    if action == 'edit_username':
        await callback.message.answer(
            "✏️ *Изменение логина*\n\n"
            f"Текущий логин: `{user_data['username']}`\n\n"
            "Введите новый логин:\n\n"
            "✅ *Требования:*\n"
            "• 3-50 символов\n"
            "• Только буквы, цифры, подчеркивание\n"
            "• Без пробелов и спецсимволов\n\n"
            "Или нажмите 'Отмена' для возврата:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        await ProfileStates.editing_username.set()
        
    elif action == 'edit_email':
        await callback.message.answer(
            "✏️ *Изменение email*\n\n"
            f"Текущий email: `{user_data['email']}`\n\n"
            "Введите новый email:\n\n"
            "Пример: *example@mail.ru*\n\n"
            "Или нажмите 'Отмена' для возврата:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        await ProfileStates.editing_email.set()
        
    elif action == 'edit_phone':
        await callback.message.answer(
            "✏️ *Изменение телефона*\n\n"
            f"Текущий телефон: `{user_data['phone'] or 'Не указан'}`\n\n"
            "Введите новый номер телефона:\n\n"
            "📱 *Формат:* +7XXXXXXXXXX или 8XXXXXXXXXX\n"
            "Пример: *+79123456789*\n\n"
            "Или нажмите 'Отмена' для возврата:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        await ProfileStates.editing_phone.set()
        
    elif action == 'edit_name':
        await callback.message.answer(
            "✏️ *Изменение ФИО*\n\n"
            f"Текущее ФИО: {user_data['full_name']}\n\n"
            "Введите новое ФИО:\n\n"
            "Пример: *Иванов Иван Иванович*\n\n"
            "Или нажмите 'Отмена' для возврата:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        await ProfileStates.editing_full_name.set()
        
    elif action == 'change_password':
        await callback.message.answer(
            "🔑 *Изменение пароля*\n\n"
            "Функция смены пароля временно недоступна.\n"
            "Обратитесь к администратору для сброса пароля.\n\n"
            "📞 Контакты: @admin",
            reply_markup=get_profile_keyboard()
        )
        
    elif action == 'back_to_main':
        await callback.message.answer(
            "Возвращаемся в главное меню...",
            reply_markup=get_main_menu()
        )
    
    await callback.answer()

async def process_edit_username(message: types.Message, state: FSMContext):
    """Обработка изменения логина"""
    if message.text == "❌ Отмена":
        await state.finish()
        await message.answer(
            "Изменение логина отменено.",
            reply_markup=ReplyKeyboardRemove()
        )
        await message.answer("Выберите действие:", reply_markup=get_profile_keyboard())
        return
    
    new_username = message.text.strip()
    user_id = message.from_user.id
    
    # Валидируем логин
    is_valid, error_msg = validate_username(new_username)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\n\nВведите новый логин еще раз:")
        return
    
    # Проверяем уникальность логина (исключая текущего пользователя)
    if not await db.check_field_unique('username', new_username, user_id):
        await message.answer(
            "❌ Этот логин уже занят!\n"
            "Придумайте другой логин:"
        )
        return
    
    # Обновляем логин
    success = await db.update_user_field(user_id, 'username', new_username)
    if success:
        await message.answer(
            f"✅ Логин успешно изменен на: `{new_username}`",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        # Показываем обновленный профиль
        await show_updated_profile(message)
    else:
        await message.answer(
            "❌ Ошибка при изменении логина!\n"
            "Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )
    
    await state.finish()

async def process_edit_email(message: types.Message, state: FSMContext):
    """Обработка изменения email"""
    if message.text == "❌ Отмена":
        await state.finish()
        await message.answer(
            "Изменение email отменено.",
            reply_markup=ReplyKeyboardRemove()
        )
        await message.answer("Выберите действие:", reply_markup=get_profile_keyboard())
        return
    
    new_email = message.text.strip().lower()
    user_id = message.from_user.id
    
    # Валидируем email
    is_valid, error_msg = validate_email(new_email)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\n\nВведите новый email еще раз:")
        return
    
    # Проверяем уникальность email (исключая текущего пользователя)
    if not await db.check_field_unique('email', new_email, user_id):
        await message.answer(
            "❌ Этот email уже зарегистрирован!\n"
            "Введите другой email:"
        )
        return
    
    # Обновляем email
    success = await db.update_user_field(user_id, 'email', new_email)
    if success:
        await message.answer(
            f"✅ Email успешно изменен на: `{new_email}`",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        await show_updated_profile(message)
    else:
        await message.answer(
            "❌ Ошибка при изменении email!\n"
            "Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )
    
    await state.finish()

async def process_edit_phone(message: types.Message, state: FSMContext):
    """Обработка изменения телефона"""
    if message.text == "❌ Отмена":
        await state.finish()
        await message.answer(
            "Изменение телефона отменено.",
            reply_markup=ReplyKeyboardRemove()
        )
        await message.answer("Выберите действие:", reply_markup=get_profile_keyboard())
        return
    
    new_phone = message.text.strip()
    user_id = message.from_user.id
    
    # Валидируем телефон
    is_valid, formatted_phone = validate_phone(new_phone)
    if not is_valid:
        await message.answer(
            "❌ Неверный формат номера телефона!\n"
            "Введите номер в формате: +7XXXXXXXXXX или 8XXXXXXXXXX\n\n"
            "Попробуйте еще раз:"
        )
        return
    
    # Проверяем уникальность телефона (исключая текущего пользователя)
    if not await db.check_field_unique('phone', formatted_phone, user_id):
        await message.answer(
            "❌ Этот номер телефона уже зарегистрирован!\n"
            "Введите другой номер:"
        )
        return
    
    # Обновляем телефон
    success = await db.update_user_field(user_id, 'phone', formatted_phone)
    if success:
        await message.answer(
            f"✅ Телефон успешно изменен на: `{formatted_phone}`",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        await show_updated_profile(message)
    else:
        await message.answer(
            "❌ Ошибка при изменении телефона!\n"
            "Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )
    
    await state.finish()

async def process_edit_full_name(message: types.Message, state: FSMContext):
    """Обработка изменения ФИО"""
    if message.text == "❌ Отмена":
        await state.finish()
        await message.answer(
            "Изменение ФИО отменено.",
            reply_markup=ReplyKeyboardRemove()
        )
        await message.answer("Выберите действие:", reply_markup=get_profile_keyboard())
        return
    
    new_full_name = message.text.strip()
    user_id = message.from_user.id
    
    # Валидируем ФИО
    is_valid, error_msg = validate_full_name(new_full_name)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\n\nВведите новое ФИО еще раз:")
        return
    
    # Обновляем ФИО
    success = await db.update_user_field(user_id, 'full_name', new_full_name)
    if success:
        await message.answer(
            f"✅ ФИО успешно изменено на: {new_full_name}",
            reply_markup=ReplyKeyboardRemove()
        )
        await show_updated_profile(message)
    else:
        await message.answer(
            "❌ Ошибка при изменении ФИО!\n"
            "Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )
    
    await state.finish()

async def show_updated_profile(message: types.Message):
    """Показать обновленный профиль"""
    user_id = message.from_user.id
    user_data = await db.get_user_by_id(user_id)
    
    if user_data:
        profile_text = (
            "👤 *Обновленный профиль:*\n\n"
            f"🔑 *Логин:* `{user_data['username']}`\n"
            f"📧 *Email:* `{user_data['email']}`\n"
            f"📞 *Телефон:* `{user_data['phone'] or 'Не указан'}`\n"
            f"👨‍💼 *ФИО:* {user_data['full_name']}\n"
            f"📅 *Дата регистрации:* {user_data['registration_date'][:10]}\n"
            f"🕒 *Последнее обновление:* {user_data['last_login'][:16]}\n\n"
            "Выберите что хотите изменить:"
        )
        
        await message.answer(profile_text, parse_mode="Markdown", reply_markup=get_profile_keyboard())
    else:
        await message.answer(
            "❌ Ошибка при загрузке профиля!",
            reply_markup=get_main_menu()
        )

def register_handlers_profile(dp: Dispatcher):
    """Регистрация обработчиков профиля"""
    # Обработчик инлайн кнопок профиля
    dp.register_callback_query_handler(
        process_profile_callback,
        lambda c: c.data in [
            'edit_username', 'edit_email', 'edit_phone', 'edit_name',
            'change_password', 'back_to_main'
        ]
    )
    
    # Обработчики состояний редактирования профиля
    dp.register_message_handler(
        process_edit_username,
        state=ProfileStates.editing_username
    )
    dp.register_message_handler(
        process_edit_email,
        state=ProfileStates.editing_email
    )
    dp.register_message_handler(
        process_edit_phone,
        state=ProfileStates.editing_phone
    )
    dp.register_message_handler(
        process_edit_full_name,
        state=ProfileStates.editing_full_name
    )