from aiogram import Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def show_about(message: types.Message):
    """Показать информацию 'О нас'"""
    about_text = (
        "ℹ️ *О нас*\n\n"
        "Здесь должна быть надпись\n\n"
        "Этот бот создан для управления футбольными турнирами "
        "и предоставляет удобный интерфейс для регистрации участников, "
        "просмотра турнирной таблицы и управления соревнованиями.\n\n"
        "⚽ *Возможности бота:*\n"
        "• Регистрация и личный кабинет\n"
        "• Просмотр футбольных турниров\n"
        "• Управление турнирами (для администраторов)\n"
        "• Система банов и модерации\n\n"
        "📞 *Контакты:*\n"
        "По всем вопросам обращайтесь к администратору: @admin"
    )
    
    keyboard = InlineKeyboardMarkup()
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data='about_back')
    keyboard.add(back_btn)
    
    await message.answer(about_text, parse_mode="Markdown", reply_markup=keyboard)

async def about_back(callback: types.CallbackQuery):
    """Возврат из информации 'О нас'"""
    from database import db
    from keyboards import get_main_menu, get_start_keyboard
    
    user_id = callback.from_user.id
    
    if await db.user_exists_by_tg_id(user_id):
        await callback.message.edit_text(
            "Возвращаемся в главное меню...",
            reply_markup=None
        )
        await callback.message.answer(
            "Главное меню:",
            reply_markup=get_main_menu()
        )
    else:
        await callback.message.edit_text(
            "Возвращаемся в начало...",
            reply_markup=None
        )
        await callback.message.answer(
            "👋 Добро пожаловать! Выберите действие:",
            reply_markup=get_start_keyboard()
        )
    
    await callback.answer()

def register_handlers_info(dp: Dispatcher):
    """Регистрация обработчиков информации"""
    # Обработчик кнопки "О нас"
    dp.register_message_handler(
        show_about, 
        lambda message: message.text == "ℹ️ О нас",
        state="*"
    )
    
    # Обработчик возврата
    dp.register_callback_query_handler(about_back, lambda c: c.data == 'about_back')