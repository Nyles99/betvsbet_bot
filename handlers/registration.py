from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove

from database import db
from states import RegistrationStates
from keyboards import get_back_keyboard, get_phone_keyboard, get_main_menu, get_start_keyboard
from utils import validate_username, validate_email, validate_phone, validate_full_name

async def start_registration(message: types.Message):
    """Начало процесса регистрации"""
    user_id = message.from_user.id
    
    # Проверяем, не зарегистрирован ли пользователь уже
    if await db.user_exists_by_tg_id(user_id):
        await message.answer(
            "❌ Вы уже зарегистрированы!\n"
            "Используйте личный кабинет для просмотра данных.",
            reply_markup=get_main_menu()
        )
        return
    
    await message.answer(
        "📝 *Начинаем регистрацию!*\n\n"
        "Шаг 1 из 5:\n"
        "Придумайте и введите *логин* для входа:\n\n"
        "✅ *Можно:* буквы, цифры, подчеркивание\n"
        "❌ *Нельзя:* пробелы, спецсимволы\n"
        "📏 *Длина:* 3-50 символов\n\n"
        "Пример: `ivanov2024`",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    
    await RegistrationStates.waiting_for_username.set()

async def process_username(message: types.Message, state: FSMContext):
    """Обработка ввода логина - Шаг 1"""
    username = message.text.strip()
    
    # Проверяем, не нажата ли кнопка "Назад"
    if message.text == "🔙 Назад":
        await state.finish()
        await message.answer(
            "Регистрация отменена.",
            reply_markup=get_start_keyboard()
        )
        return
    
    # Валидируем логин
    is_valid, error_msg = validate_username(username)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\n\nВведите логин еще раз:")
        return
    
    # Проверяем уникальность логина
    if not await db.check_field_unique('username', username):
        await message.answer(
            "❌ Этот логин уже занят!\n"
            "Придумайте другой логин:"
        )
        return
    
    # Сохраняем логин в состоянии
    await state.update_data(username=username)
    
    await message.answer(
        "✅ Логин принят!\n\n"
        "Шаг 2 из 5:\n"
        "Введите ваш *пароль*:\n\n"
        "⚠️ *Рекомендации:*\n"
        "• Минимум 6 символов\n"
        "• Буквы и цифры\n"
        "• Пароль будет надежно защищен",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    
    await RegistrationStates.waiting_for_password.set()

async def process_password(message: types.Message, state: FSMContext):
    """Обработка ввода пароля - Шаг 2"""
    password = message.text.strip()
    
    # Проверяем, не нажата ли кнопка "Назад"
    if message.text == "🔙 Назад":
        await message.answer(
            "Введите логин:",
            reply_markup=get_back_keyboard()
        )
        await RegistrationStates.waiting_for_username.set()
        return
    
    # Проверяем длину пароля
    if len(password) < 6:
        await message.answer(
            "❌ Пароль слишком короткий!\n"
            "Минимальная длина - 6 символов.\n\n"
            "Введите пароль еще раз:"
        )
        return
    
    # Сохраняем пароль в состоянии
    await state.update_data(password=password)
    
    await message.answer(
        "✅ Пароль принят!\n\n"
        "Шаг 3 из 5:\n"
        "Введите ваше *ФИО* (Фамилия Имя Отчество):\n\n"
        "Пример: *Иванов Иван Иванович*",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    
    await RegistrationStates.waiting_for_full_name.set()

async def process_full_name(message: types.Message, state: FSMContext):
    """Обработка ввода ФИО - Шаг 3"""
    full_name = message.text.strip()
    
    # Проверяем, не нажата ли кнопка "Назад"
    if message.text == "🔙 Назад":
        await message.answer("Введите пароль:")
        await RegistrationStates.waiting_for_password.set()
        return
    
    # Валидируем ФИО
    is_valid, error_msg = validate_full_name(full_name)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\n\nВведите ФИО еще раз:")
        return
    
    # Сохраняем ФИО в состоянии
    await state.update_data(full_name=full_name)
    
    await message.answer(
        "✅ ФИО принято!\n\n"
        "Шаг 4 из 5:\n"
        "Введите ваш *email*:\n\n"
        "Пример: *example@mail.ru*",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    
    await RegistrationStates.waiting_for_email.set()

async def process_email(message: types.Message, state: FSMContext):
    """Обработка ввода email - Шаг 4"""
    email = message.text.strip().lower()
    
    # Проверяем, не нажата ли кнопка "Назад"
    if message.text == "🔙 Назад":
        await message.answer("Введите ФИО:")
        await RegistrationStates.waiting_for_full_name.set()
        return
    
    # Валидируем email
    is_valid, error_msg = validate_email(email)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\n\nВведите email еще раз:")
        return
    
    # Проверяем уникальность email
    if not await db.check_field_unique('email', email):
        await message.answer(
            "❌ Этот email уже зарегистрирован!\n"
            "Введите другой email:"
        )
        return
    
    # Сохраняем email в состоянии
    await state.update_data(email=email)
    
    await message.answer(
        "✅ Email принят!\n\n"
        "Шаг 5 из 5:\n"
        "Введите ваш *номер телефона*:\n\n"
        "📱 *Формат:* +7XXXXXXXXXX или 8XXXXXXXXXX\n"
        "Пример: *+79123456789* или *89123456789*\n\n"
        "Или нажмите кнопку ниже для автоматической отправки:",
        parse_mode="Markdown",
        reply_markup=get_phone_keyboard()
    )
    
    await RegistrationStates.waiting_for_phone.set()

async def process_phone_message(message: types.Message, state: FSMContext):
    """Обработка ввода телефона текстом - Шаг 5"""
    phone = message.text.strip()
    
    # Проверяем, не нажата ли кнопка "Назад"
    if message.text == "🔙 Назад":
        await message.answer("Введите email:")
        await RegistrationStates.waiting_for_email.set()
        return
    
    # Валидируем телефон
    is_valid, formatted_phone = validate_phone(phone)
    if not is_valid:
        await message.answer(
            "❌ Неверный формат номера телефона!\n"
            "Введите номер в формате: +7XXXXXXXXXX или 8XXXXXXXXXX\n\n"
            "Пример: *+79123456789*",
            parse_mode="Markdown"
        )
        return
    
    # Проверяем уникальность телефона
    if not await db.check_field_unique('phone', formatted_phone):
        await message.answer(
            "❌ Этот номер телефона уже зарегистрирован!\n"
            "Введите другой номер:"
        )
        return
    
    # Сохраняем телефон в состоянии
    await state.update_data(phone=formatted_phone)
    
    # Завершаем регистрацию
    await complete_registration(message, state)

async def process_phone_contact(message: types.Message, state: FSMContext):
    """Обработка отправки контакта - Шаг 5"""
    if message.contact:
        phone = message.contact.phone_number
        
        # Валидируем телефон
        is_valid, formatted_phone = validate_phone(phone)
        if not is_valid:
            await message.answer(
                "❌ Неверный формат номера телефона!\n"
                "Пожалуйста, введите номер вручную:",
                reply_markup=get_back_keyboard()
            )
            return
        
        # Проверяем уникальность телефона
        if not await db.check_field_unique('phone', formatted_phone):
            await message.answer(
                "❌ Этот номер телефона уже зарегистрирован!\n"
                "Введите другой номер:",
                reply_markup=get_back_keyboard()
            )
            return
        
        # Сохраняем телефон в состоянии
        await state.update_data(phone=formatted_phone)
        
        # Завершаем регистрацию
        await complete_registration(message, state)
    else:
        await message.answer("Пожалуйста, отправьте ваш номер телефона")

async def complete_registration(message: types.Message, state: FSMContext):
    """Завершение регистрации"""
    # Получаем все данные из состояния
    user_data = await state.get_data()
    
    username = user_data.get('username')
    password = user_data.get('password')
    email = user_data.get('email')
    phone = user_data.get('phone')
    full_name = user_data.get('full_name')
    
    # Получаем информацию о пользователе Telegram
    user = message.from_user
    
    # Сохраняем пользователя в базу данных
    result = await db.add_user(
        user_id=user.id,
        username=username,
        password=password,
        email=email,
        phone=phone,
        full_name=full_name,
        tg_username=user.username or '',
        tg_first_name=user.first_name or '',
        tg_last_name=user.last_name or ''
    )
    
    if result is True:
        await message.answer(
            "🎉 *Регистрация успешно завершена!*\n\n"
            f"📋 *Ваши данные для входа:*\n"
            f"🔑 *Логин:* `{username}`\n"
            f"📧 *Email:* `{email}`\n"
            f"📞 *Телефон:* `{phone}`\n"
            f"👤 *ФИО:* {full_name}\n\n"
            "✅ Теперь вы можете входить используя:\n"
            "• Логин\n• Email\n• Номер телефона\n\n"
            "Используйте личный кабинет для управления данными!",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    else:
        error_messages = {
            "username_exists": "❌ Этот логин уже занят!",
            "email_exists": "❌ Этот email уже зарегистрирован!",
            "phone_exists": "❌ Этот номер телефона уже зарегистрирован!",
            "error": "❌ Произошла ошибка при регистрации."
        }
        
        await message.answer(
            error_messages.get(result, "❌ Произошла ошибка при регистрации.") +
            "\n\nПопробуйте начать регистрацию заново: /start",
            reply_markup=get_start_keyboard()
        )
    
    # Завершаем состояние
    await state.finish()

def register_handlers_registration(dp: Dispatcher):
    """Регистрация обработчиков регистрации"""
    # Обработчик кнопки "Регистрация"
    dp.register_message_handler(
        start_registration, 
        lambda message: message.text == "📝 Регистрация",
        state="*"
    )
    
    # Обработчики состояний регистрации
    dp.register_message_handler(
        process_username, 
        state=RegistrationStates.waiting_for_username
    )
    dp.register_message_handler(
        process_password, 
        state=RegistrationStates.waiting_for_password
    )
    dp.register_message_handler(
        process_full_name, 
        state=RegistrationStates.waiting_for_full_name
    )
    dp.register_message_handler(
        process_email, 
        state=RegistrationStates.waiting_for_email
    )
    dp.register_message_handler(
        process_phone_message, 
        state=RegistrationStates.waiting_for_phone,
        content_types=types.ContentType.TEXT
    )
    dp.register_message_handler(
        process_phone_contact, 
        state=RegistrationStates.waiting_for_phone,
        content_types=types.ContentType.CONTACT
    )