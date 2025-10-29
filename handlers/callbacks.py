from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
from database.db_handler import DatabaseHandler
from keyboards.menu import (
    get_main_inline_keyboard, 
    get_profile_inline_keyboard, 
    get_back_inline_keyboard,
    get_user_tournaments_keyboard,
    get_user_tournament_matches_keyboard
)
from states.user_states import ProfileStates
from utils.validators import validate_username, validate_full_name

async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка главного меню"""
    # Сбрасываем состояние если оно есть
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=get_main_inline_keyboard()
    )

async def profile_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка кнопки личного кабинета"""
    # Сбрасываем состояние если оно есть
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    await callback.message.edit_text(
        "👤 Личный кабинет. Выберите действие:",
        reply_markup=get_profile_inline_keyboard()
    )

async def my_profile_callback(callback: CallbackQuery, state: FSMContext):
    """Показать профиль пользователя"""
    # Сбрасываем состояние если оно есть
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    db = DatabaseHandler('users.db')
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if user:
        profile_text = f"""
👤 **Ваш профиль:**

📱 **Телефон:** {user.phone_number}
👤 **Логин:** {user.username or 'Не установлен'}
📛 **ФИО:** {user.full_name or 'Не установлено'}
📅 **Дата регистрации:** {user.registration_date}
        """
        await callback.message.edit_text(
            profile_text,
            parse_mode='Markdown',
            reply_markup=get_profile_inline_keyboard()
        )
    else:
        await callback.answer("❌ Профиль не найден.", show_alert=True)

async def change_username_callback(callback: CallbackQuery, state: FSMContext):
    """Начало изменения логина"""
    await callback.message.edit_text(
        "Введите новый логин (только латинские буквы, цифры и нижнее подчеркивание, 3-20 символов):\n\nДля отмены нажмите кнопку 'Назад'",
        reply_markup=get_back_inline_keyboard()
    )
    await ProfileStates.waiting_for_username.set()

async def change_fullname_callback(callback: CallbackQuery, state: FSMContext):
    """Начало изменения ФИО"""
    await callback.message.edit_text(
        "Введите ваше ФИО (только буквы, пробелы и дефисы, 2-100 символов):\n\nДля отмены нажмите кнопку 'Назад'",
        reply_markup=get_back_inline_keyboard()
    )
    await ProfileStates.waiting_for_full_name.set()

async def tournaments_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка кнопки турниров для пользователя"""
    # Сбрасываем состояние если оно есть
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    db = DatabaseHandler('users.db')
    tournaments = db.get_all_tournaments()
    
    if tournaments:
        text = "🏆 Доступные турниры:\n\n"
        for tournament in tournaments:
            matches_count = len(db.get_tournament_matches(tournament[0]))
            text += f"• {tournament[1]}\n"
            if tournament[2]:  # описание
                text += f"  📝 {tournament[2]}\n"
            text += f"  ⚽ Матчей: {matches_count}\n"
            text += f"  📅 Создан: {tournament[4]}\n\n"
    else:
        text = "🏆 На данный момент нет активных турниров.\n\nСледите за обновлениями!"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_user_tournaments_keyboard(tournaments)
    )

async def user_tournament_detail_callback(callback: CallbackQuery, state: FSMContext):
    """Детальная информация о турнире для пользователя"""
    # Сбрасываем состояние если оно есть
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    tournament_id = int(callback.data.split('_')[2])
    
    db = DatabaseHandler('users.db')
    tournament = db.get_tournament(tournament_id)
    matches = db.get_tournament_matches(tournament_id)
    
    if tournament:
        if matches:
            text = f"🏆 Матчи турнира: {tournament[1]}\n\n"
            if tournament[2]:  # описание
                text += f"📝 {tournament[2]}\n\n"
            
            for match in matches:
                text += f"📅 {match[2]} {match[3]} - {match[4]} vs {match[5]}\n\n"
        else:
            text = f"🏆 В турнире '{tournament[1]}' пока нет матчей.\n\n"
            if tournament[2]:  # описание
                text += f"📝 {tournament[2]}\n\n"
            text += "Следите за обновлениями!"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_user_tournament_matches_keyboard(tournament_id, matches)
        )
    else:
        await callback.answer("❌ Турнир не найден.", show_alert=True)

async def user_match_detail_callback(callback: CallbackQuery, state: FSMContext):
    """Детальная информация о матче для пользователя"""
    # Сбрасываем состояние если оно есть
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    match_id = int(callback.data.split('_')[2])
    
    db = DatabaseHandler('users.db')
    match = db.get_match(match_id)
    
    if match:
        tournament = db.get_tournament(match[1])
        text = f"""
⚽ Информация о матче:

🏆 Турнир: {tournament[1]}
📅 Дата: {match[2]}
⏰ Время: {match[3]}
🏆 Команда 1: {match[4]}
🏆 Команда 2: {match[5]}
🔰 Статус: Запланирован

Для участия в ставках обратитесь к администратору.
        """
        await callback.message.edit_text(
            text,
            reply_markup=get_back_inline_keyboard()
        )
    else:
        await callback.answer("❌ Матч не найден.", show_alert=True)

async def help_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка кнопки помощи"""
    # Сбрасываем состояние если оно есть
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    help_text = """
🤖 **Помощь по боту:**

📱 **Регистрация:** Для регистрации требуется номер телефона в формате +7
👤 **Личный кабинет:** Позволяет изменить логин и ФИО
🏆 **Турниры:** Просмотр доступных турниров и матчей
⚽ **Матчи:** Информация о предстоящих матчах
📞 **О нас:** Информация о нашей компании

Если у вас возникли проблемы, обратитесь в поддержку.
    """
    await callback.message.edit_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=get_back_inline_keyboard()
    )

async def about_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка кнопки 'О нас'"""
    # Сбрасываем состояние если оно есть
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    about_text = """
📞 **О нас**

Мы - современная платформа для организации и проведения турниров. 

🎯 **Наша миссия:** Сделать участие в турнирах простым и доступным для всех.

🏆 **Турниры:** Регулярно проводим различные соревнования и чемпионаты.

⚽ **Матчи:** Актуальная информация о всех предстоящих матчах.

📧 **Контакты:**
Email: info@example.com
Телефон: +7 (XXX) XXX-XX-XX

Следите за нашими обновлениями!
    """
    await callback.message.edit_text(
        about_text,
        parse_mode='Markdown',
        reply_markup=get_back_inline_keyboard()
    )

def register_callback_handlers(dp: Dispatcher):
    """Регистрация обработчиков колбэков"""
    # Главное меню
    dp.register_callback_query_handler(main_menu_callback, lambda c: c.data == "main_menu", state="*")
    
    # Профиль
    dp.register_callback_query_handler(profile_callback, lambda c: c.data == "profile", state="*")
    dp.register_callback_query_handler(my_profile_callback, lambda c: c.data == "my_profile", state="*")
    dp.register_callback_query_handler(change_username_callback, lambda c: c.data == "change_username", state="*")
    dp.register_callback_query_handler(change_fullname_callback, lambda c: c.data == "change_fullname", state="*")
    
    # Турниры для пользователей
    dp.register_callback_query_handler(tournaments_callback, lambda c: c.data == "tournaments", state="*")
    dp.register_callback_query_handler(user_tournament_detail_callback, lambda c: c.data.startswith("user_tournament_"), state="*")
    dp.register_callback_query_handler(user_match_detail_callback, lambda c: c.data.startswith("user_match_"), state="*")
    
    # Другие разделы
    dp.register_callback_query_handler(help_callback, lambda c: c.data == "help", state="*")
    dp.register_callback_query_handler(about_callback, lambda c: c.data == "about", state="*")