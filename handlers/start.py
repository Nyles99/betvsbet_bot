from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from database import db
from config_bot import config
from keyboards import get_main_menu, get_start_keyboard
import keyboards

async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    # Сбрасываем состояние пользователя
    await state.finish()
    
    user_id = message.from_user.id
    
    # Проверяем, зарегистрирован ли пользователь
    if await db.user_exists_by_tg_id(user_id):
        # Проверяем, не забанен ли пользователь
        if await db.is_user_banned(user_id):
            await message.answer(
                "🚫 Ваш аккаунт заблокирован!\n\n"
                "По всем вопросам обращайтесь к администратору: @admin",
                reply_markup=types.ReplyKeyboardRemove()
            )
            return
        
        # Пользователь зарегистрирован - показываем главное меню
        await message.answer(
            "🎉 Добро пожаловать назад!\n"
            "Выберите действие:",
            reply_markup=get_main_menu()
        )
    else:
        # Пользователь не зарегистрирован - предлагаем регистрацию или вход
        await message.answer(
            "👋 Привет! Я бот для регистрации.\n\n"
            "У вас уже есть аккаунт? Выберите действие:",
            reply_markup=get_start_keyboard()
        )

async def cmd_help(message: types.Message):
    """Обработчик команды помощи"""
    help_text = (
        "ℹ️ *Помощь по боту:*\n\n"
        "🔐 *Войти* - вход в существующий аккаунт\n"
        "📝 *Регистрация* - создание нового аккаунта\n"
        "👤 *Личный кабинет* - просмотр и редактирование данных\n"
        "⚽ *Турниры* - просмотр футбольных турниров (только для авторизованных)\n"
        "ℹ️ *О нас* - информация о боте\n"
        "❓ *Помощь* - это сообщение\n\n"
        "👑 *Администраторам:*\n"
        "/admin - админ-панель\n\n"
        "📞 *Поддержка:* @admin"
    )
    
    await message.answer(help_text, parse_mode="Markdown")

async def show_profile(message: types.Message):
    """Показать личный кабинет"""
    user_id = message.from_user.id
    user_data = await db.get_user_by_id(user_id)
    
    if not user_data:
        await message.answer(
            "❌ Вы не зарегистрированы!\n"
            "Пройдите регистрацию для доступа к личному кабинету.",
            reply_markup=get_start_keyboard()
        )
        return
    
    profile_text = (
        "👤 *Ваш профиль:*\n\n"
        f"🔑 *Логин:* `{user_data['username']}`\n"
        f"📧 *Email:* `{user_data['email']}`\n"
        f"📞 *Телефон:* `{user_data['phone'] or 'Не указан'}`\n"
        f"👨‍💼 *ФИО:* {user_data['full_name']}\n"
        f"📅 *Дата регистрации:* {user_data['registration_date'][:10]}\n"
        f"🕒 *Последний вход:* {user_data['last_login'][:16]}\n\n"
        "Используйте кнопки ниже для редактирования данных:"
    )
    
    await message.answer(profile_text, parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())
    await message.answer("Выберите что хотите изменить:", reply_markup=keyboards.get_profile_keyboard())

def register_handlers_start(dp: Dispatcher):
    """Регистрация обработчиков команд"""
    dp.register_message_handler(cmd_start, Command("start"), state="*")
    dp.register_message_handler(cmd_help, Command("help"))
    dp.register_message_handler(cmd_help, lambda message: message.text == "❓ Помощь")
    dp.register_message_handler(show_profile, lambda message: message.text == "👤 Личный кабинет")