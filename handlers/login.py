from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove

from database import db
from states import LoginStates
from keyboards import get_back_keyboard, get_main_menu, get_start_keyboard
from utils import is_login_identifier

async def start_login(message: types.Message):
    """Начало процесса входа"""
    user_id = message.from_user.id
    
    # Проверяем, не зарегистрирован ли пользователь уже
    if await db.user_exists_by_tg_id(user_id):
        await message.answer(
            "✅ Вы уже вошли в систему!\n"
            "Используйте личный кабинет для просмотра данных.",
            reply_markup=get_main_menu()
        )
        return
    
    await message.answer(
        "🔐 *Вход в систему*\n\n"
        "Введите ваш *логин, email или номер телефона*:\n\n"
        "✅ *Можно использовать:*\n"
        "• Логин (пример: `ivanov2024`)\n"
        "• Email (пример: `ivan@mail.ru`)\n"
        "• Телефон (пример: `+79123456789`)\n\n"
        "Или нажмите 'Назад' для возврата:",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    
    await LoginStates.waiting_for_login.set()

async def process_login_identifier(message: types.Message, state: FSMContext):
    """Обработка ввода логина/email/телефона"""
    login_identifier = message.text.strip()
    
    # Проверяем, не нажата ли кнопка "Назад"
    if message.text == "🔙 Назад":
        await state.finish()
        await message.answer(
            "Вход отменен.",
            reply_markup=get_start_keyboard()
        )
        return
    
    # Определяем тип идентификатора
    identifier_type = is_login_identifier(login_identifier)
    
    if identifier_type == "invalid":
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Введите один из вариантов:\n"
            "• Логин (только буквы, цифры, подчеркивание)\n"
            "• Email (пример: user@mail.ru)\n"
            "• Телефон (пример: +79123456789)\n\n"
            "Попробуйте еще раз:"
        )
        return
    
    # Проверяем существование пользователя
    user = await db.get_user_by_login(login_identifier)
    if not user:
        await message.answer(
            "❌ Пользователь не найден!\n\n"
            "Проверьте правильность введенных данных или "
            "зарегистрируйтесь, если у вас нет аккаунта.\n\n"
            "Введите логин/email/телефон еще раз:"
        )
        return
    
    # Сохраняем данные в состоянии
    await state.update_data(
        login_identifier=login_identifier,
        user_id=user['user_id']
    )
    
    await message.answer(
        "✅ Пользователь найден!\n\n"
        "Теперь введите ваш *пароль*:\n\n"
        "Или нажмите 'Назад' для ввода другого логина:",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )
    
    await LoginStates.waiting_for_password.set()

async def process_password(message: types.Message, state: FSMContext):
    """Обработка ввода пароля"""
    password = message.text.strip()
    
    # Проверяем, не нажата ли кнопка "Назад"
    if message.text == "🔙 Назад":
        await message.answer(
            "Введите ваш логин, email или телефон:",
            reply_markup=get_back_keyboard()
        )
        await LoginStates.waiting_for_login.set()
        return
    
    # Получаем данные из состояния
    user_data = await state.get_data()
    login_identifier = user_data.get('login_identifier')
    stored_user_id = user_data.get('user_id')
    
    # Проверяем пароль
    if await db.verify_password(login_identifier, password):
        # Обновляем Telegram данные пользователя
        current_user = message.from_user
        await db.update_user_field(stored_user_id, 'tg_username', current_user.username or '')
        await db.update_user_field(stored_user_id, 'tg_first_name', current_user.first_name or '')
        await db.update_user_field(stored_user_id, 'tg_last_name', current_user.last_name or '')
        await db.update_last_login(stored_user_id)
        
        # Получаем актуальные данные пользователя
        user_info = await db.get_user_by_id(stored_user_id)
        
        await message.answer(
            "🎉 *Вход выполнен успешно!*\n\n"
            f"👋 Добро пожаловать, {user_info['full_name']}!\n\n"
            f"🔑 Вошли как: `{login_identifier}`\n"
            f"🕒 Время входа: {user_info['last_login'][:16]}\n\n"
            "Теперь вам доступен полный функционал бота!",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            "❌ Неверный пароль!\n\n"
            "Попробуйте ввести пароль еще раз:\n\n"
            "Если забыли пароль, обратитесь к администратору.",
            reply_markup=get_back_keyboard()
        )
        return
    
    # Завершаем состояние
    await state.finish()

def register_handlers_login(dp: Dispatcher):
    """Регистрация обработчиков входа"""
    # Обработчик кнопки "Войти"
    dp.register_message_handler(
        start_login, 
        lambda message: message.text == "🔐 Войти",
        state="*"
    )
    
    # Обработчики состояний входа
    dp.register_message_handler(
        process_login_identifier, 
        state=LoginStates.waiting_for_login
    )
    dp.register_message_handler(
        process_password, 
        state=LoginStates.waiting_for_password
    )