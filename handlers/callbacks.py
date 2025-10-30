from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.exceptions import MessageNotModified
from database.db_handler import DatabaseHandler
from keyboards.menu import (
    get_main_inline_keyboard, 
    get_profile_inline_keyboard, 
    get_back_inline_keyboard,
    get_user_tournaments_keyboard,
    get_user_tournament_matches_keyboard,
    get_available_matches_keyboard,
    get_user_bets_tournaments_keyboard,
    get_user_tournament_bets_keyboard,
    get_back_to_matches_keyboard,
    get_back_to_tournament_keyboard
)
from states.user_states import ProfileStates, UserBetStates
from utils.validators import validate_username, validate_full_name, validate_score

async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup=None):
    """
    Безопасное редактирование сообщения с обработкой ошибки MessageNotModified
    """
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    except MessageNotModified:
        # Игнорируем ошибку, если сообщение не изменилось
        pass

async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка главного меню"""
    # Сбрасываем состояние если оно есть
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    await safe_edit_message(
        callback,
        "Выберите действие:",
        get_main_inline_keyboard()
    )

async def profile_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка кнопки личного кабинета"""
    # Сбрасываем состояние если оно есть
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    await safe_edit_message(
        callback,
        "👤 Личный кабинет. Выберите действие:",
        get_profile_inline_keyboard()
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
        await safe_edit_message(
            callback,
            profile_text,
            get_profile_inline_keyboard()
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
        await safe_edit_message(
            callback,
            text,
            get_user_bets_tournaments_keyboard(tournaments)
        )
    else:
        text = "📋 У вас пока нет ставок.\n\nСделайте свою первую ставку в разделе '🏆 Турниры'!"
        await safe_edit_message(
            callback,
            text,
            get_back_inline_keyboard()
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
        
        await safe_edit_message(
            callback,
            text,
            get_user_tournament_bets_keyboard(tournament_id, bets)
        )
    else:
        await callback.answer("❌ Ставки не найден.", show_alert=True)

async def change_username_callback(callback: CallbackQuery, state: FSMContext):
    """Начало изменения логина"""
    await safe_edit_message(
        callback,
        "Введите новый логин (только латинские буквы, цифры и нижнее подчеркивание, 3-20 символов):\n\nДля отмены нажмите кнопку 'Назад'",
        get_back_inline_keyboard()
    )
    await ProfileStates.waiting_for_username.set()

async def change_fullname_callback(callback: CallbackQuery, state: FSMContext):
    """Начало изменения ФИО"""
    await safe_edit_message(
        callback,
        "Введите ваше ФИО (только буквы, пробелы и дефисы, 2-100 символов):\n\nДля отмены нажмите кнопку 'Назад'",
        get_back_inline_keyboard()
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
        text = "🏆 Доступные турниры:\n\nЗдесь вы можете:\n• Просмотреть матчи турниров\n• Сделать ставки на матчи\n• Отслеживать свои прогнозы\n\nВыберите турнир:"
        for tournament in tournaments:
            matches_count = len(db.get_tournament_matches(tournament[0]))
            text += f"\n\n• {tournament[1]}"
            if tournament[2]:  # описание
                text += f"\n  📝 {tournament[2]}"
            text += f"\n  ⚽ Матчей: {matches_count}"
            text += f"\n  📅 Создан: {tournament[4]}"
    else:
        text = "🏆 На данный момент нет активных турниров.\n\nСледите за обновлениями!"
    
    await safe_edit_message(
        callback,
        text,
        get_user_tournaments_keyboard(tournaments)
    )

async def user_tournament_detail_callback(callback: CallbackQuery, state: FSMContext):
    """Детальная информация о турнире для пользователя"""
    # Сбрасываем состояние если оно есть
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    tournament_id = int(callback.data.split('_')[2])
    user_id = callback.from_user.id
    
    db = DatabaseHandler('users.db')
    tournament = db.get_tournament(tournament_id)
    all_matches = db.get_tournament_matches(tournament_id)
    
    # Фильтруем матчи - оставляем только те, на которые пользователь еще не делал ставку
    available_matches = []
    for match in all_matches:
        user_bet = db.get_user_bet(user_id, match[0])
        if not user_bet:  # Если ставки нет - добавляем в список
            available_matches.append(match)
    
    if tournament:
        if available_matches:
            text = f"🏆 Матчи турнира: {tournament[1]}\n\n"
            if tournament[2]:  # описание
                text += f"📝 {tournament[2]}\n\n"
            text += "Выберите матч для ввода счета:\n\n"
            
            for match in available_matches:
                text += f"📅 {match[2]} {match[3]} - {match[4]} vs {match[5]}\n\n"
        else:
            text = f"🏆 Турнир: {tournament[1]}\n\n"
            if tournament[2]:  # описание
                text += f"📝 {tournament[2]}\n\n"
            
            if all_matches:
                text += "✅ Вы уже сделали ставки на все матчи этого турнира!\n\n"
                text += "Просмотреть свои ставки можно в разделе '📋 Мои ставки' личного кабинета."
            else:
                text += "В этом турнире пока нет матчей.\n\nСледите за обновлениями!"
        
        await safe_edit_message(
            callback,
            text,
            get_user_tournament_matches_keyboard(tournament_id, available_matches)
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
    user_id = callback.from_user.id
    
    db = DatabaseHandler('users.db')
    match = db.get_match(match_id)
    
    if match:
        tournament = db.get_tournament(match[1])
        user_bet = db.get_user_bet(user_id, match_id)
        
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
            await safe_edit_message(
                callback,
                text,
                get_back_to_tournament_keyboard(match[1])
            )
        else:
            # Если ставки нет, предлагаем ввести счет
            text = f"""
⚽ Ввод счета для матча:

🏆 Турнир: {tournament[1]}
📅 Дата: {match[2]}
⏰ Время: {match[3]}
⚔️ Матч: {match[4]} vs {match[5]}

📝 Введите счет матча в формате X-Y (например: 2-1) и нажмите отправить:
            """
            
            async with state.proxy() as data:
                data['match_id'] = match_id
                data['match_info'] = f"{match[4]} vs {match[5]}"
                data['tournament_id'] = match[1]  # Сохраняем tournament_id для возврата
            
            await safe_edit_message(
                callback,
                text,
                get_back_to_tournament_keyboard(match[1])
            )
            await UserBetStates.waiting_for_score.set()
    else:
        await callback.answer("❌ Матч не найден.", show_alert=True)

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
        await safe_edit_message(
            callback,
            text,
            get_available_matches_keyboard(available_matches)
        )
    else:
        text = "⚽ На данный момент нет доступных матчей для ставок.\n\nВсе матчи уже имеют ваши ставки или турниры еще не начались."
        await safe_edit_message(
            callback,
            text,
            get_back_inline_keyboard()
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
⚔️ Матч: {match[4]} vs {match[5]}

📝 Введите счет матча в формате X-Y (например: 2-1) и нажмите отправить:
        """
        
        async with state.proxy() as data:
            data['match_id'] = match_id
            data['match_info'] = f"{match[4]} vs {match[5]}"
            data['tournament_id'] = match[1]  # Сохраняем tournament_id для возврата
        
        await safe_edit_message(
            callback,
            text,
            get_back_to_matches_keyboard()
        )
        await UserBetStates.waiting_for_score.set()
    else:
        await callback.answer("❌ Матч не найден.", show_alert=True)

async def process_score_message(message: Message, state: FSMContext):
    """Обработка сообщения с счетом из чата"""
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
        tournament_id = data.get('tournament_id')
    
    db = DatabaseHandler('users.db')
    user_id = message.from_user.id
    
    if db.add_user_bet(user_id, match_id, score):
        # Успешное сохранение ставки
        await message.answer(
            f"✅ Счет {score} для матча {match_info} успешно сохранен!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        # Возвращаем пользователя в список матчей турнира
        tournament = db.get_tournament(tournament_id)
        all_matches = db.get_tournament_matches(tournament_id)
        
        # Фильтруем матчи - оставляем только доступные для ставок
        available_matches = []
        for match in all_matches:
            user_bet = db.get_user_bet(user_id, match[0])
            if not user_bet:
                available_matches.append(match)
        
        if available_matches:
            text = f"🏆 Матчи турнира: {tournament[1]}\n\n"
            text += "✅ Ваша ставка сохранена!\n\n"
            text += "Выберите следующий матч для ввода счета:\n\n"
            
            for match in available_matches:
                text += f"📅 {match[2]} {match[3]} - {match[4]} vs {match[5]}\n\n"
        else:
            text = f"🏆 Турнир: {tournament[1]}\n\n"
            text += "✅ Поздравляем! Вы сделали ставки на все матчи этого турнира!\n\n"
            text += "Просмотреть все свои ставки можно в разделе '📋 Мои ставки' личного кабинета."
        
        await message.answer(
            text,
            reply_markup=get_user_tournament_matches_keyboard(tournament_id, available_matches)
        )
    else:
        await message.answer(
            "❌ Ошибка при сохранении ставки. Попробуйте еще раз.",
            reply_markup=get_back_to_tournament_keyboard(tournament_id)
        )
    
    await state.finish()

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
🏆 **Турниры:** Просмотр доступных турниров, матчей и ввод ставок
📋 **Мои ставки:** Просмотр всех ваших ставок по турнирам
📞 **О нас:** Информация о нашей компании

📝 **Как сделать ставку:**
1. Перейдите в раздел "🏆 Турниры"
2. Выберите интересующий турнир
3. Выберите матч из списка
4. Введите счет в формате X-Y (например: 2-1)

📝 **Формат счета:** Используйте формат X-Y (например: 2-1)
    """
    await safe_edit_message(
        callback,
        help_text,
        get_back_inline_keyboard()
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
    await safe_edit_message(
        callback,
        about_text,
        get_back_inline_keyboard()
    )

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
    dp.register_callback_query_handler(user_tournament_detail_callback, lambda c: c.data.startswith("user_tournament_"), state="*")
    dp.register_callback_query_handler(user_match_detail_callback, lambda c: c.data.startswith("user_match_"), state="*")
    
    # Другие разделы
    dp.register_callback_query_handler(help_callback, lambda c: c.data == "help", state="*")
    dp.register_callback_query_handler(about_callback, lambda c: c.data == "about", state="*")
    
    # FSM для ставок
    dp.register_message_handler(process_score_message, state=UserBetStates.waiting_for_score)