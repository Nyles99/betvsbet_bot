from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message
from database.db_handler import DatabaseHandler
from keyboards.menu import (
    get_main_inline_keyboard,
    get_match_bet_keyboard, 
    get_profile_inline_keyboard, 
    get_back_inline_keyboard,
    get_user_tournaments_keyboard,
    get_user_tournament_matches_keyboard,
    get_available_matches_keyboard,
    get_bet_score_keyboard,
    get_user_bets_tournaments_keyboard,
    get_user_tournament_bets_keyboard
)
from states.user_states import ProfileStates, UserBetStates
from utils.validators import validate_username, validate_full_name, validate_score

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
        # Получаем количество ставок пользователя
        user_bets = db.get_user_bets(user_id)
        
        profile_text = f"""
👤 **Ваш профиль:**

📱 **Телефон:** {user.phone_number}
👤 **Логин:** {user.username or 'Не установлен'}
📛 **ФИО:** {user.full_name or 'Не установлено'}
📅 **Дата регистрации:** {user.registration_date}
⚽ **Количество ставок:** {len(user_bets)}
        """
        await callback.message.edit_text(
            profile_text,
            parse_mode='Markdown',
            reply_markup=get_profile_inline_keyboard()
        )
    else:
        await callback.answer("❌ Профиль не найден.", show_alert=True)

async def my_bets_callback(callback: CallbackQuery, state: FSMContext):
    """Мои ставки - список турниров"""
    # Сбрасываем состояние если оно есть
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    db = DatabaseHandler('users.db')
    user_id = callback.from_user.id
    tournaments = db.get_user_tournaments_with_bets(user_id)
    
    if tournaments:
        text = "🏆 Ваши турниры:\n\nВыберите турнир для просмотра ставок:"
        await callback.message.edit_text(
            text,
            reply_markup=get_user_bets_tournaments_keyboard(tournaments)
        )
    else:
        text = "📋 У вас пока нет ставок.\n\nСделайте свою первую ставку в разделе '⚽ Сделать ставку'!"
        await callback.message.edit_text(
            text,
            reply_markup=get_back_inline_keyboard()
        )

async def bets_tournament_detail_callback(callback: CallbackQuery, state: FSMContext):
    """Детали ставок в турнире"""
    # Сбрасываем состояние если оно есть
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    tournament_id = int(callback.data.split('_')[2])
    
    db = DatabaseHandler('users.db')
    user_id = callback.from_user.id
    tournament = db.get_tournament(tournament_id)
    bets = db.get_tournament_bets_by_user(user_id, tournament_id)
    
    if tournament and bets:
        text = f"📋 Ваши ставки в турнире: {tournament[1]}\n\n"
        
        for bet in bets:
            text += f"📅 {bet[5]} | {bet[6]} | {bet[7]} vs {bet[8]} | Счет: {bet[3]}\n\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_user_tournament_bets_keyboard(tournament_id, bets)
        )
    else:
        await callback.answer("❌ Ставки не найдены.", show_alert=True)

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

async def make_bet_callback(callback: CallbackQuery, state: FSMContext):
    """Раздел для создания ставок"""
    # Сбрасываем состояние если оно есть
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    db = DatabaseHandler('users.db')
    user_id = callback.from_user.id
    available_matches = db.get_available_matches_for_user(user_id)
    
    if available_matches:
        text = "⚽ Доступные матчи для ставок:\n\nВыберите матч для ввода счета:"
        await callback.message.edit_text(
            text,
            reply_markup=get_available_matches_keyboard(available_matches)
        )
    else:
        text = "⚽ На данный момент нет доступных матчей для ставок.\n\nВсе матчи уже имеют ваши ставки или турниры еще не начались."
        await callback.message.edit_text(
            text,
            reply_markup=get_back_inline_keyboard()
        )

async def bet_match_callback(callback: CallbackQuery, state: FSMContext):
    """Выбор матча для ставки"""
    match_id = int(callback.data.split('_')[2])
    
    db = DatabaseHandler('users.db')
    match = db.get_match(match_id)
    
    if match:
        tournament = db.get_tournament(match[1])
        text = f"""
⚽ Ввод счета для матча:

🏆 Турнир: {tournament[1]}
📅 Дата: {match[2]}
⏰ Время: {match[3]}
🏆 Команда 1: {match[4]}
🏆 Команда 2: {match[5]}

Введите счет матча, обязательно через дефис, например 3-2:
        """
        
        async with state.proxy() as data:
            data['match_id'] = match_id
            data['match_info'] = f"{match[4]} vs {match[5]}"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_bet_score_keyboard(match_id)
        )
        await UserBetStates.waiting_for_score.set()
    else:
        await callback.answer("❌ Матч не найден.", show_alert=True)

async def process_score_input(callback: CallbackQuery, state: FSMContext):
    """Обработка ввода счета через кнопку"""
    await callback.answer()

async def process_score_message(message: Message, state: FSMContext):
    """Обработка сообщения с счетом"""
    score = message.text.strip()
    
    if not validate_score(score):
        await message.answer(
            "❌ Неверный формат счета. Используйте формат X-Y (например: 2-1).\n\nПопробуйте еще раз:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return
    
    async with state.proxy() as data:
        match_id = data['match_id']
        match_info = data['match_info']
    
    db = DatabaseHandler('users.db')
    user_id = message.from_user.id
    
    if db.add_user_bet(user_id, match_id, score):
        await message.answer(
            f"✅ Счет {score} для матча {match_info} успешно сохранен!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        # Показываем обновленную информацию о матче
        match = db.get_match(match_id)
        tournament = db.get_tournament(match[1])
        user_bet = db.get_user_bet(user_id, match_id)
        
        text = f"""
⚽ Информация о матче:

🏆 Турнир: {tournament[1]}
📅 Дата: {match[2]}
⏰ Время: {match[3]}
⚔️ Матч: {match[4]} vs {match[5]}
🔰 Статус: Запланирован

✅ Ваш счет: {user_bet[3]}
📅 Дата ставки: {user_bet[4]}
        """
        await message.answer(
            text,
            reply_markup=get_back_inline_keyboard()
        )
    else:
        await message.answer(
            "❌ Ошибка при сохранении ставки. Попробуйте еще раз.",
            reply_markup=types.ReplyKeyboardRemove()
        )
    
    await state.finish()

async def submit_score_callback(callback: CallbackQuery, state: FSMContext):
    """Подтверждение отправки счета"""
    # Эта функция просто подтверждает что нужно ввести счет
    await callback.answer("Введите счет в сообщении выше 👆")

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
    """Детальная информация о матче для пользователя с возможностью ввода счета"""
    # Сбрасываем состояние если оно есть
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    match_id = int(callback.data.split('_')[2])
    
    db = DatabaseHandler('users.db')
    match = db.get_match(match_id)
    
    if match:
        tournament = db.get_tournament(match[1])
        user_bet = db.get_user_bet(callback.from_user.id, match_id)
        
        if user_bet:
            # Если ставка уже сделана, показываем информацию о ставке
            text = f"""
⚽ Информация о матче:

🏆 Турнир: {tournament[1]}
📅 Дата: {match[2]}
⏰ Время: {match[3]}
⚔️ Матч: {match[4]} vs {match[5]}
🔰 Статус: Запланирован

✅ Ваш счет: {user_bet[3]}
📅 Дата ставки: {user_bet[4]}
            """
            await callback.message.edit_text(
                text,
                reply_markup=get_back_inline_keyboard()
            )
        else:
            # Если ставки нет, предлагаем ввести счет
            text = f"""
⚽ Ввод счета для матча:

🏆 Турнир: {tournament[1]}
📅 Дата: {match[2]}
⏰ Время: {match[3]}
⚔️ Матч: {match[4]} vs {match[5]}

Введите счет матча в формате X-Y (например: 2-1):
            """
            
            async with state.proxy() as data:
                data['match_id'] = match_id
                data['match_info'] = f"{match[4]} vs {match[5]}"
            
            await callback.message.edit_text(
                text,
                reply_markup=get_match_bet_keyboard(match_id)
            )
            await UserBetStates.waiting_for_score.set()
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
👤 **Личный кабинет:** Позволяет изменить логин, ФИО и просмотреть ставки
🏆 **Турниры:** Просмотр доступных турниров и матчей
⚽ **Сделать ставку:** Ввод счета на предстоящие матчи
📋 **Мои ставки:** Просмотр всех ваших ставок по турнирам
📞 **О нас:** Информация о нашей компании

📝 **Формат счета:** Используйте формат X-Y (например: 2-1)
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

⚽ **Ставки:** Участвуйте в прогнозировании результатов матчей.

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

async def submit_match_score_callback(callback: CallbackQuery, state: FSMContext):
    """Подтверждение отправки счета из деталей матча"""
    # Эта функция просто подтверждает что нужно ввести счет
    await callback.answer("Введите счет в сообщении выше 👆")

def register_callback_handlers(dp: Dispatcher):
    """Регистрация обработчиков колбэков"""
    # Главное меню
    dp.register_callback_query_handler(main_menu_callback, lambda c: c.data == "main_menu", state="*")
    
    # Профиль
    dp.register_callback_query_handler(profile_callback, lambda c: c.data == "profile", state="*")
    dp.register_callback_query_handler(my_profile_callback, lambda c: c.data == "my_profile", state="*")
    dp.register_callback_query_handler(my_bets_callback, lambda c: c.data == "my_bets", state="*")
    dp.register_callback_query_handler(bets_tournament_detail_callback, lambda c: c.data.startswith("bets_tournament_"), state="*")
    dp.register_callback_query_handler(change_username_callback, lambda c: c.data == "change_username", state="*")
    dp.register_callback_query_handler(change_fullname_callback, lambda c: c.data == "change_fullname", state="*")
    
    # Турниры и ставки
    dp.register_callback_query_handler(tournaments_callback, lambda c: c.data == "tournaments", state="*")
    dp.register_callback_query_handler(make_bet_callback, lambda c: c.data == "make_bet", state="*")
    dp.register_callback_query_handler(bet_match_callback, lambda c: c.data.startswith("bet_match_"), state="*")
    dp.register_callback_query_handler(submit_score_callback, lambda c: c.data.startswith("submit_score_"), state="*")
    dp.register_callback_query_handler(submit_match_score_callback, lambda c: c.data.startswith("submit_match_score_"), state="*")  # Добавьте эту строку
    dp.register_callback_query_handler(user_tournament_detail_callback, lambda c: c.data.startswith("user_tournament_"), state="*")
    dp.register_callback_query_handler(user_match_detail_callback, lambda c: c.data.startswith("user_match_"), state="*")
    
    # Другие разделы
    dp.register_callback_query_handler(help_callback, lambda c: c.data == "help", state="*")
    dp.register_callback_query_handler(about_callback, lambda c: c.data == "about", state="*")
    
    # FSM для ставок
    dp.register_message_handler(process_score_message, state=UserBetStates.waiting_for_score)