from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.exceptions import MessageNotModified
from database.db_handler import DatabaseHandler
from keyboards.menu import (
    get_main_inline_keyboard, 
    get_profile_inline_keyboard, 
    get_user_tournaments_keyboard,
    get_user_tournament_matches_keyboard,
    get_available_matches_keyboard,
    get_user_tournaments_list_keyboard,
    get_tournament_detail_keyboard,
    get_tournament_players_keyboard,
    get_player_detail_keyboard,
    get_back_keyboard
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
        pass

async def navigation_handler(callback: CallbackQuery, state: FSMContext, section: str):
    """
    Универсальный обработчик навигации по основным разделам
    """
    if state:
        await state.finish()
    
    navigation_config = {
        'main_menu': {
            'text': "Выберите действие:",
            'keyboard': get_main_inline_keyboard
        },
        'profile': {
            'text': "👤 Личный кабинет. Выберите действие:",
            'keyboard': get_profile_inline_keyboard
        },
        'tournaments': {
            'text': "🏆 Доступные турниры:\n\nЗдесь вы можете:\n• Просмотреть матчи турниров\n• Сделать ставки на матчи\n• Отслеживать свои прогнозы\n\nВыберите турнир:",
            'keyboard': lambda: get_user_tournaments_keyboard(DatabaseHandler('users.db').get_all_tournaments())
        },
        'my_tournaments': {
            'text': "🏆 Ваши турниры:\n\nВыберите турнир для просмотра детальной информации:",
            'keyboard': lambda: get_user_tournaments_list_keyboard(
                DatabaseHandler('users.db').get_user_tournaments_with_bets(callback.from_user.id)
            )
        },
        'help': {
            'text': """
🤖 **Помощь по боту:**

📱 **Регистрация:** Для регистрации требуется номер телефона в формате +7
👤 **Личный кабинет:** Позволяет изменить логин, ФИО и просмотреть ставки
🏆 **Турниры:** Просмотр доступных турниров, матчей и ввод ставок
📋 **Мои турниры:** Просмотр всех ваших турниров и статистики

📝 **Как сделать ставку:**
1. Перейдите в раздел "🏆 Турниры"
2. Выберите интересующий турнир  
3. Выберите матч из списка
4. Введите счет в формате X-Y (например: 2-1)
            """,
            'keyboard': lambda: get_back_keyboard()
        },
        'about': {
            'text': """
📞 **О нас**

Мы - современная платформа для организации и проведения турниров. 

🎯 **Наша миссия:** Сделать участие в турнирах простым и доступным для всех.

🏆 **Турниры:** Регулярно проводим различные соревнования и чемпионаты.

⚽ **Ставки:** Участвуйте в прогнозировании результатов матчей.

Следите за нашими обновлениями!
            """,
            'keyboard': lambda: get_back_keyboard()
        }
    }
    
    if section in navigation_config:
        config = navigation_config[section]
        keyboard = config['keyboard']() if callable(config['keyboard']) else config['keyboard']
        await safe_edit_message(callback, config['text'], keyboard)

# Функции-обертки для навигации
async def main_menu_handler(callback: CallbackQuery, state: FSMContext = None):
    await navigation_handler(callback, state, 'main_menu')

async def profile_handler(callback: CallbackQuery, state: FSMContext = None):
    await navigation_handler(callback, state, 'profile')

async def tournaments_handler(callback: CallbackQuery, state: FSMContext = None):
    await navigation_handler(callback, state, 'tournaments')

async def my_tournaments_handler(callback: CallbackQuery, state: FSMContext = None):
    await navigation_handler(callback, state, 'my_tournaments')

async def help_handler(callback: CallbackQuery, state: FSMContext = None):
    await navigation_handler(callback, state, 'help')

async def about_handler(callback: CallbackQuery, state: FSMContext = None):
    await navigation_handler(callback, state, 'about')

async def my_profile_callback(callback: CallbackQuery, state: FSMContext):
    """Показать профиль пользователя"""
    await state.finish()
    
    db = DatabaseHandler('users.db')
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if user:
        user_bets = db.get_user_bets(user_id)
        user_tournaments = db.get_user_tournaments_with_bets(user_id)
        
        profile_text = f"""
👤 **Ваш профиль:**

📱 **Телефон:** {user.phone_number}
👤 **Логин:** {user.username or 'Не установлен'}
📛 **ФИО:** {user.full_name or 'Не установлено'}
📅 **Дата регистрации:** {user.registration_date}
⚽ **Количество ставок:** {len(user_bets)}
🏆 **Участвуете в турнирах:** {len(user_tournaments)}
        """
        await safe_edit_message(callback, profile_text, get_profile_inline_keyboard())
    else:
        await callback.answer("❌ Профиль не найден.", show_alert=True)

async def my_tournaments_callback(callback: CallbackQuery, state: FSMContext):
    """Список турниров пользователя"""
    await state.finish()
    
    db = DatabaseHandler('users.db')
    user_id = callback.from_user.id
    
    # Получаем турниры, в которых пользователь делал ставки
    tournaments = db.get_user_tournaments_with_bets(user_id)
    
    if tournaments:
        text = "🏆 Ваши турниры:\n\nВыберите турнир для просмотра детальной информации:"
        await safe_edit_message(
            callback,
            text,
            get_user_tournaments_list_keyboard(tournaments)
        )
    else:
        text = "🏆 У вас пока нет турниров.\n\nПримите участие в турнирах, сделав ставки на матчи!"
        await safe_edit_message(
            callback,
            text,
            get_back_keyboard("profile", "🔙 Назад в профиль")
        )

async def user_tournament_detail_callback(callback: CallbackQuery, state: FSMContext):
    """Детальная информация о турнире для пользователя"""
    await state.finish()
    
    tournament_id = int(callback.data.split('_')[3])
    
    db = DatabaseHandler('users.db')
    tournament = db.get_tournament(tournament_id)
    user_bets_count = len(db.get_tournament_bets_by_user(callback.from_user.id, tournament_id))
    
    if tournament:
        text = f"""
🏆 Детали турнира:

📌 Название: {tournament[1]}
📝 Описание: {tournament[2] or 'Нет описания'}
🔰 Статус: {'✅ Активный' if tournament[3] == 'active' else '❌ Неактивный'}
📊 Ваших ставок: {user_bets_count}

Выберите раздел для просмотра:
        """
        await safe_edit_message(
            callback,
            text,
            get_tournament_detail_keyboard(tournament_id)
        )
    else:
        await callback.answer("❌ Турнир не найден.", show_alert=True)

async def tournament_my_bets_callback(callback: CallbackQuery, state: FSMContext):
    """Мои ставки в турнире"""
    await state.finish()
    
    tournament_id = int(callback.data.split('_')[3])
    
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
            get_tournament_detail_keyboard(tournament_id)
        )
    else:
        text = f"📋 В турнире '{tournament[1]}' у вас пока нет ставок.\n\nСделайте ставки на матчи турнира!"
        await safe_edit_message(
            callback,
            text,
            get_tournament_detail_keyboard(tournament_id)
        )

async def tournament_players_callback(callback: CallbackQuery, state: FSMContext):
    """Список игроков турнира с пагинацией"""
    await state.finish()
    
    parts = callback.data.split('_')
    tournament_id = int(parts[2])
    
    # Получаем номер страницы, если он есть, иначе ставим 0
    page = 0
    if len(parts) > 3:
        try:
            page = int(parts[3])
        except (ValueError, IndexError):
            page = 0
    
    db = DatabaseHandler('users.db')
    tournament = db.get_tournament(tournament_id)
    
    if tournament:
        # Получаем всех пользователей, которые делали ставки в этом турнире
        users = db.get_tournament_participants(tournament_id)
        
        if users:
            # Пагинация - по 10 пользователей на страницу
            users_per_page = 10
            total_pages = (len(users) + users_per_page - 1) // users_per_page
            start_index = page * users_per_page
            end_index = start_index + users_per_page
            current_users = users[start_index:end_index]
            
            text = f"👥 Игроки турнира: {tournament[1]}\n\n"
            text += f"📊 Всего участников: {len(users)}\n\n"
            
            for i, user in enumerate(current_users, start_index + 1):
                # Новый формат: "1. ID: 831040832, 👤: @Nyles44"
                user_info = f"{i}. ID: {user.user_id}"
                if user.username:
                    user_info += f", 👤: @{user.username}"
                user_info += "\n"
                
                text += user_info
            
            await safe_edit_message(
                callback,
                text,
                get_tournament_players_keyboard(tournament_id, page, total_pages, len(users))
            )
        else:
            text = f"👥 В турнире '{tournament[1]}' пока нет участников."
            await safe_edit_message(
                callback,
                text,
                get_tournament_detail_keyboard(tournament_id)
            )
    else:
        await callback.answer("❌ Турнир не найден.", show_alert=True)

async def tournament_player_detail_callback(callback: CallbackQuery, state: FSMContext):
    """Детальная информация об игроке (заглушка)"""
    await state.finish()
    
    parts = callback.data.split('_')
    tournament_id = int(parts[3])
    user_id = int(parts[4])
    page = int(parts[5])
    
    db = DatabaseHandler('users.db')
    tournament = db.get_tournament(tournament_id)
    user = db.get_user(user_id)
    
    if tournament and user:
        text = f"""
👤 Информация об игроке:

🏆 Турнир: {tournament[1]}
📱 Телефон: {user.phone_number}
👤 Логин: {user.username or 'Не установлен'}
📛 ФИО: {user.full_name or 'Не установлено'}

⏳ Детальная статистика игрока находится в разработке.
Следите за обновлениями!
        """
        await safe_edit_message(
            callback,
            text,
            get_player_detail_keyboard(tournament_id, page)
        )
    else:
        await callback.answer("❌ Данные не найдены.", show_alert=True)

async def tournament_leaderboard_callback(callback: CallbackQuery, state: FSMContext):
    """Общая таблица турнира (заглушка)"""
    await state.finish()
    
    tournament_id = int(callback.data.split('_')[3])
    
    text = """
📊 Общая таблица турнира

⏳ Функция находится в разработке.
В будущем здесь будет отображаться рейтинг участников турнира.

Следите за обновлениями!
    """
    await safe_edit_message(
        callback,
        text,
        get_tournament_detail_keyboard(tournament_id)
    )

async def tournament_rules_callback(callback: CallbackQuery, state: FSMContext):
    """Правила турнира (заглушка)"""
    await state.finish()
    
    tournament_id = int(callback.data.split('_')[3])
    
    text = """
📖 Правила турнира

⏳ Функция находится в разработке.
В будущем здесь будут отображаться правила и условия турнира.

Следите за обновлениями!
    """
    await safe_edit_message(
        callback,
        text,
        get_tournament_detail_keyboard(tournament_id)
    )

async def user_tournament_matches_callback(callback: CallbackQuery, state: FSMContext):
    """Детальная информация о турнире для пользователя с матчами"""
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
        if not user_bet:
            available_matches.append(match)
    
    if tournament:
        if available_matches:
            text = f"🏆 Матчи турнира: {tournament[1]}\n\n"
            if tournament[2]:
                text += f"📝 {tournament[2]}\n\n"
            text += "Выберите матч для ввода счета:\n\n"
            
            for match in available_matches:
                text += f"📅 {match[2]} {match[3]} - {match[4]} vs {match[5]}\n\n"
        else:
            text = f"🏆 Турнир: {tournament[1]}\n\n"
            if tournament[2]:
                text += f"📝 {tournament[2]}\n\n"
            
            if all_matches:
                text += "✅ Вы уже сделали ставки на все матчи этого турнира!\n\n"
                text += "Просмотреть свои ставки можно в разделе '📋 Мои ставки' деталей турнира."
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
    await state.finish()
    
    match_id = int(callback.data.split('_')[2])
    user_id = callback.from_user.id
    
    db = DatabaseHandler('users.db')
    match = db.get_match(match_id)
    
    if match:
        tournament = db.get_tournament(match[1])
        user_bet = db.get_user_bet(user_id, match_id)
        
        if user_bet:
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
                get_back_keyboard(f"user_tournament_{match[1]}", "🔙 Назад к турниру")
            )
        else:
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
                data['tournament_id'] = match[1]
            
            await safe_edit_message(
                callback,
                text,
                get_back_keyboard(f"user_tournament_{match[1]}", "🔙 Назад к турниру")
            )
            await UserBetStates.waiting_for_score.set()
    else:
        await callback.answer("❌ Матч не найден.", show_alert=True)

async def change_username_callback(callback: CallbackQuery, state: FSMContext):
    """Начало изменения логина"""
    await safe_edit_message(
        callback,
        "Введите новый логин (только латинские буквы, цифры и нижнее подчеркивание, 3-20 символов):\n\nДля отмены нажмите кнопку 'Назад'",
        get_back_keyboard()
    )
    await ProfileStates.waiting_for_username.set()

async def change_fullname_callback(callback: CallbackQuery, state: FSMContext):
    """Начало изменения ФИО"""
    await safe_edit_message(
        callback,
        "Введите ваше ФИО (только буквы, пробелы и дефисы, 2-100 символов):\n\nДля отмены нажмите кнопку 'Назад'",
        get_back_keyboard()
    )
    await ProfileStates.waiting_for_full_name.set()

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
        await message.answer(
            f"✅ Счет {score} для матча {match_info} успешно сохранен!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        # Возвращаем пользователя в список матчей турнира
        tournament = db.get_tournament(tournament_id)
        all_matches = db.get_tournament_matches(tournament_id)
        
        available_matches = []
        for match in all_matches:
            user_bet = db.get_user_bet(user_id, match[0])
            if not user_bet:
                available_matches.append(match)
        
        if available_matches:
            text = f"🏆 Матчи турнира: {tournament[1]}\n\n✅ Ваша ставка сохранена!\n\nВыберите следующий матч для ввода счета:\n\n"
            for match in available_matches:
                text += f"📅 {match[2]} {match[3]} - {match[4]} vs {match[5]}\n\n"
        else:
            text = f"🏆 Турнир: {tournament[1]}\n\n✅ Поздравляем! Вы сделали ставки на все матчи этого турнира!\n\nПросмотреть все свои ставки можно в разделе '📋 Мои ставки' деталей турнира."
        
        await message.answer(
            text,
            reply_markup=get_user_tournament_matches_keyboard(tournament_id, available_matches)
        )
    else:
        await message.answer(
            "❌ Ошибка при сохранении ставки. Попробуйте еще раз.",
            reply_markup=get_back_keyboard(f"user_tournament_{tournament_id}", "🔙 Назад к турниру")
        )
    
    await state.finish()

async def no_action_callback(callback: CallbackQuery):
    """Обработчик для кнопок без действия"""
    await callback.answer("⏳ Эта функция находится в разработке", show_alert=True)

def register_callback_handlers(dp: Dispatcher):
    """Регистрация обработчиков колбэков"""
    # Основная навигация
    dp.register_callback_query_handler(main_menu_handler, lambda c: c.data == "main_menu", state="*")
    dp.register_callback_query_handler(profile_handler, lambda c: c.data == "profile", state="*")
    dp.register_callback_query_handler(tournaments_handler, lambda c: c.data == "tournaments", state="*")
    dp.register_callback_query_handler(my_tournaments_handler, lambda c: c.data == "my_tournaments", state="*")
    dp.register_callback_query_handler(help_handler, lambda c: c.data == "help", state="*")
    dp.register_callback_query_handler(about_handler, lambda c: c.data == "about", state="*")
    
    # Профиль пользователя
    dp.register_callback_query_handler(my_profile_callback, lambda c: c.data == "my_profile", state="*")
    dp.register_callback_query_handler(change_username_callback, lambda c: c.data == "change_username", state="*")
    dp.register_callback_query_handler(change_fullname_callback, lambda c: c.data == "change_fullname", state="*")
    
    # Турниры пользователя
    dp.register_callback_query_handler(my_tournaments_callback, lambda c: c.data == "my_tournaments", state="*")
    dp.register_callback_query_handler(user_tournament_detail_callback, lambda c: c.data.startswith("user_tournament_detail_"), state="*")
    dp.register_callback_query_handler(tournament_my_bets_callback, lambda c: c.data.startswith("tournament_my_bets_"), state="*")
    dp.register_callback_query_handler(tournament_players_callback, lambda c: c.data.startswith("tournament_players_"), state="*")  # Этот обработчик
    dp.register_callback_query_handler(tournament_leaderboard_callback, lambda c: c.data.startswith("tournament_leaderboard_"), state="*")
    dp.register_callback_query_handler(tournament_rules_callback, lambda c: c.data.startswith("tournament_rules_"), state="*")
    
    # Турниры и матчи для ставок
    dp.register_callback_query_handler(user_tournament_matches_callback, lambda c: c.data.startswith("user_tournament_") and not c.data.startswith("user_tournament_detail_"), state="*")
    dp.register_callback_query_handler(user_match_detail_callback, lambda c: c.data.startswith("user_match_"), state="*")
    
    # Кнопки без действия
    dp.register_callback_query_handler(no_action_callback, lambda c: c.data == "no_action")
    
    # FSM для ставок
    dp.register_message_handler(process_score_message, state=UserBetStates.waiting_for_score)
