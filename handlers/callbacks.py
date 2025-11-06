from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.exceptions import MessageNotModified
from database.db_handler import DatabaseHandler
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from keyboards.menu import (
    get_main_inline_keyboard,
    get_profile_inline_keyboard,
    get_tournaments_main_keyboard,
    get_all_tournaments_keyboard,
    get_my_tournaments_keyboard,
    get_user_tournament_matches_keyboard,
    get_tournament_detail_keyboard,
    get_tournament_players_keyboard,
    get_tournament_leaderboard_keyboard,
    get_player_bets_keyboard,
    get_back_keyboard
)
from states.user_states import ProfileStates, UserBetStates
from utils.validators import validate_username, validate_score
from utils.scoring_system import calculate_points, get_scoring_rules_description
import hashlib
import logging

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

def _is_datetime_string(self, text: str) -> bool:
    """Проверяет, является ли строка датой/временем"""
    if not text:
        return False
    # Проверяем паттерны даты/времени
    datetime_patterns = [
        r'\d{4}-\d{2}-\d{2}',
        r'\d{2}:\d{2}:\d{2}',
        r'\d{4}-\d{2}-\d{2}.*\d{2}:\d{2}:\d{2}'
    ]
    import re
    for pattern in datetime_patterns:
        if re.search(pattern, str(text)):
            return True
    return False

async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup=None):
    """Безопасное редактирование сообщения"""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    except MessageNotModified:
        pass

async def handle_navigation(callback: CallbackQuery, state: FSMContext):
    """Универсальный обработчик навигации"""
    await state.finish()
    
    navigation_config = {
        "main_menu": {
            "text": "Выберите действие:",
            "keyboard": get_main_inline_keyboard()
        },
        "profile": {
            "text": "👤 Личный кабинет. Выберите действие:",
            "keyboard": get_profile_inline_keyboard()
        },
        "tournaments_main": {
            "text": "🏆 Раздел турниров\n\nВыберите раздел:",
            "keyboard": get_tournaments_main_keyboard()
        },
        "all_tournaments": {
            "text": "📋 Все доступные турниры:\n\nВыберите турнир для участия:",
            "keyboard": get_all_tournaments_keyboard(DatabaseHandler('users.db').get_all_tournaments())
        },
        "my_tournaments": {
            "text": "🏆 Ваши турниры:\n\nВыберите турнир для просмотра:",
            "keyboard": get_my_tournaments_keyboard(
                DatabaseHandler('users.db').get_user_tournaments_with_bets(callback.from_user.id)
            )
        },
        "help": {
            "text": """🤖 **Помощь по боту:**

📱 **Регистрация:** 
• Уникальный номер телефона и логин
• Номер в формате +7XXXXXXXXXX
• Логин: латинские буквы, цифры (3-20 символов)
• Пароль: минимум 6 символов
• ФИО: имя и фамилия

👤 **Личный кабинет:** Изменение логина и пароля
🏆 **Турниры:** 
• Мои турниры - ваши текущие турниры
• Все турниры - выбор новых турниров

📝 **Как сделать ставку:**
1. Турниры → Все турниры
2. Выберите турнир
3. Выберите матч
4. Введите счет (формат X-Y)

После ставки турнир появится в Мои турниры""",
            "keyboard": get_back_keyboard()
        },
        "about": {
            "text": """📞 **О нас**

Современная платформа для организации турниров.

🎯 **Наша миссия:** Сделать участие в турнирах простым и доступным.

🏆 **Турниры:** Регулярные соревнования и чемпионаты.

⚽ **Ставки:** Прогнозирование результатов матчей.

Следите за обновлениями!""",
            "keyboard": get_back_keyboard()
        }
    }
    
    if callback.data in navigation_config:
        config = navigation_config[callback.data]
        await safe_edit_message(callback, config["text"], config["keyboard"])

async def my_profile_callback(callback: CallbackQuery, state: FSMContext):
    """Показать профиль пользователя"""
    await state.finish()
    
    db = DatabaseHandler('users.db')
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if user:
        # Используем новый метод для получения ставок с информацией о матчах
        user_bets = db.get_user_bets_with_match_info(user_id)
        user_tournaments = db.get_user_tournaments_with_bets(user_id)
        
        profile_text = f"""👤 **Ваш профиль:**

📱 **Телефон:** {user.phone_number}
👤 **Логин:** {user.username or 'Не установлен'}
📛 **ФИО:** {user.full_name or 'Не установлено'}
📅 **Регистрация:** {user.registration_date}
⚽ **Ставок:** {len(user_bets)}
🏆 **Турниров:** {len(user_tournaments)}"""
        
        await safe_edit_message(callback, profile_text, get_profile_inline_keyboard())
    else:
        await callback.answer("❌ Профиль не найден.", show_alert=True)

async def all_tournament_detail_callback(callback: CallbackQuery, state: FSMContext):
    """Детальная информация о турнире из раздела 'Все турниры'"""
    await state.finish()
    
    tournament_id = int(callback.data.split('_')[2])
    user_id = callback.from_user.id
    
    db = DatabaseHandler('users.db')
    tournament = db.get_tournament(tournament_id)
    
    if not tournament:
        await callback.answer("❌ Турнир не найден.", show_alert=True)
        return
    
    # Используем новый метод для получения доступных матчей
    available_matches = db.get_available_tournament_matches(tournament_id, user_id)
    all_matches = db.get_tournament_matches(tournament_id)
    
    text = f"🏆 Турнир: {tournament[1]}\n"
    if tournament[2]:
        text += f"📝 {tournament[2]}\n\n"
    
    if available_matches:
        text += "Выберите матч для ввода счета:\n\n"
        for match in available_matches:
            text += f"📅 {match[2]} {match[3]} - {match[4]} vs {match[5]}\n\n"
    else:
        if all_matches:
            # Проверяем, есть ли истекшие матчи без ставок
            expired_without_bets = False
            for match in all_matches:
                if db.is_match_expired(match[2], match[3]):
                    user_bet = db.get_user_bet(user_id, match[0])
                    if not user_bet:
                        expired_without_bets = True
                        break
            
            if expired_without_bets:
                text += "⏰ Время для ставок на некоторые матчи истекло.\n\n"
            text += "✅ Вы уже сделали ставки на все доступные матчи!\n\n"
            text += "Теперь этот турнир доступен в разделе '🏆 Мои турниры'"
        else:
            text += "В этом турнире пока нет матчей.\n\nСледите за обновлениями!"
    
    await safe_edit_message(
        callback,
        text,
        get_user_tournament_matches_keyboard(tournament_id, available_matches, "all_tournaments")
    )

async def my_tournament_detail_callback(callback: CallbackQuery, state: FSMContext):
    """Детальная информация о турнире из раздела 'Мои турниры'"""
    await state.finish()
    
    tournament_id = int(callback.data.split('_')[3])
    
    db = DatabaseHandler('users.db')
    tournament = db.get_tournament(tournament_id)
    
    if not tournament:
        await callback.answer("❌ Турнир не найден.", show_alert=True)
        return
    
    user_bets_count = len(db.get_tournament_bets_by_user(callback.from_user.id, tournament_id))
    
    text = f"""🏆 Детали турнира:

📌 Название: {tournament[1]}
📝 Описание: {tournament[2] or 'Нет описания'}
🔰 Статус: {'✅ Активный' if tournament[3] == 'active' else '❌ Неактивный'}
📊 Ваших ставок: {user_bets_count}

Выберите раздел для просмотра:"""
    
    await safe_edit_message(
        callback,
        text,
        get_tournament_detail_keyboard(tournament_id)
    )

async def tournament_my_bets_callback(callback: CallbackQuery, state: FSMContext):
    """Мои ставки в турнире"""
    await state.finish()
    
    try:
        parts = callback.data.split('_')
        if len(parts) < 2:
            await callback.answer("❌ Ошибка: неверный формат данных", show_alert=True)
            return
        
        tournament_id = int(parts[1])  # bets_123
        
        db = DatabaseHandler('users.db')
        user_id = callback.from_user.id
        tournament = db.get_tournament(tournament_id)
        bets = db.get_tournament_bets_by_user(user_id, tournament_id)
        
        if tournament and bets:
            text = f"📋 Ваши ставки в турнире: {tournament[1]}\n\n"
            
            for bet in bets:
                # bet[9] - это match_result из запроса (поле №9 в результате)
                match_result = bet[9] if len(bet) > 9 else None
                
                # Формируем базовую строку
                bet_text = f"📅 {bet[5]} | {bet[6]} | {bet[7]} vs {bet[8]} | Счет: {bet[3]}"
                
                # Проверяем есть ли результат и он не пустой и является счетом
                if (match_result and 
                    match_result != 'None' and 
                    '-' in str(match_result) and
                    all(c.isdigit() or c == '-' for c in str(match_result).strip())):
                    bet_text += f" | 🎯 Итог: `{match_result}`"
                    
                    # Рассчитываем и добавляем очки
                    points = calculate_points(bet[3], match_result)
                    bet_text += f" | Очки: {points}"
                else:
                    bet_text += " | 🎯 Итог: `Неизвестно`"
                
                text += bet_text + "\n\n"
            
            await safe_edit_message(
                callback,
                text,
                get_tournament_detail_keyboard(tournament_id)
            )
        else:
            text = f"📋 В турнире '{tournament[1]}' у вас пока нет ставок."
            await safe_edit_message(
                callback,
                text,
                get_tournament_detail_keyboard(tournament_id)
            )
    except (ValueError, IndexError) as e:
        logging.error(f"Error in tournament_my_bets_callback: {e}, data: {callback.data}")
        await callback.answer("❌ Ошибка при загрузке ставок", show_alert=True)

async def tournament_players_callback(callback: CallbackQuery, state: FSMContext):
    """Список игроков турнира с пагинацией"""
    await state.finish()
    
    try:
        parts = callback.data.split('_')
        if len(parts) < 2:
            await callback.answer("❌ Ошибка: неверный формат данных", show_alert=True)
            return
        
        tournament_id = int(parts[1])  # players_123_0
        
        # Получаем номер страницы
        page = 0
        if len(parts) > 2:
            try:
                page = int(parts[2])
            except (ValueError, IndexError):
                page = 0
        
        db = DatabaseHandler('users.db')
        tournament = db.get_tournament(tournament_id)
        
        if not tournament:
            await callback.answer("❌ Турнир не найден.", show_alert=True)
            return
        
        users = db.get_tournament_participants(tournament_id)
        
        if users:
            # Пагинация
            users_per_page = 8  # Уменьшил для кнопок
            total_pages = (len(users) + users_per_page - 1) // users_per_page
            start_index = page * users_per_page
            end_index = start_index + users_per_page
            current_users = users[start_index:end_index]
            
            text = f"👥 Игроки турнира: {tournament[1]}\n\n"
            text += f"📊 Всего участников: {len(users)}\n\n"
            text += "Нажмите '📊 Посмотреть ставки' чтобы увидеть завершенные ставки игрока:\n\n"
            
            # Создаем клавиатуру с кнопками
            keyboard = InlineKeyboardMarkup(row_width=1)
            
            for i, user in enumerate(current_users, start_index + 1):
                user_info = f"{i}. ID: {user.user_id}"
                if user.username:
                    user_info += f", 👤: @{user.username}"
                if user.full_name:
                    user_info += f", 📛: {user.full_name}"
                
                # Добавляем кнопку для просмотра ставок
                keyboard.add(InlineKeyboardButton(
                    f"📊 {user_info}",
                    callback_data=f"view_bets_{tournament_id}_{user.user_id}_{page}"
                ))
            
            # Кнопки пагинации
            if total_pages > 1:
                pagination_buttons = []
                if page > 0:
                    pagination_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"players_{tournament_id}_{page-1}"))
                
                pagination_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="no_action"))
                
                if page < total_pages - 1:
                    pagination_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"players_{tournament_id}_{page+1}"))
                
                if pagination_buttons:
                    keyboard.row(*pagination_buttons)
            
            # Кнопка назад
            keyboard.row(InlineKeyboardButton("🔙 Назад к турниру", callback_data=f"my_tournament_detail_{tournament_id}"))
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard
            )
        else:
            text = f"👥 В турнире '{tournament[1]}' пока нет участников."
            await safe_edit_message(
                callback,
                text,
                get_tournament_detail_keyboard(tournament_id)
            )
    except (ValueError, IndexError) as e:
        logging.error(f"Error in tournament_players_callback: {e}, data: {callback.data}")
        await callback.answer("❌ Ошибка при загрузке игроков", show_alert=True)

async def tournament_leaderboard_callback(callback: CallbackQuery, state: FSMContext):
    """Общая таблица турнира с рейтингом игроков"""
    await state.finish()
    
    try:
        parts = callback.data.split('_')
        if len(parts) < 2:
            await callback.answer("❌ Ошибка: неверный формат данных", show_alert=True)
            return
        
        tournament_id = int(parts[1])  # leaderboard_123 или leaderboard_123_0
        
        # Получаем номер страницы
        page = 0
        if len(parts) > 2:
            try:
                page = int(parts[2])
            except (ValueError, IndexError):
                page = 0
        
        db = DatabaseHandler('users.db')
        tournament = db.get_tournament(tournament_id)
        
        if not tournament:
            await callback.answer("❌ Турнир не найден.", show_alert=True)
            return
        
        # Получаем рейтинг игроков с пагинацией
        players_per_page = 10
        all_players = db.get_tournament_leaderboard(tournament_id)
        total_players = len(all_players)
        
        # Применяем пагинацию
        start_index = page * players_per_page
        end_index = start_index + players_per_page
        current_players = all_players[start_index:end_index]
        
        if current_players:
            text = f"🏆 **Рейтинг игроков: {tournament[1]}**\n\n"
            text += "```\n"
            text += "Место| Логин        | Матчи | ТС |Очки\n"
            text += "-----|--------------|-------|----|----\n"
            
            for i, player in enumerate(current_players, start_index + 1):
                # Определяем медаль для первых трех мест
                medal = ""
                if i == 1:
                    medal = "🥇"
                elif i == 2:
                    medal = "🥈"
                elif i == 3:
                    medal = "🥉"
                else:
                    medal = f"{i}"
                
                # Форматируем логин (обрезаем если длинный)
                username = player['username']
                if len(username) > 12:
                    username = username[:12] + "..."
                else:
                    username = username.ljust(12)
                
                # Форматируем количество матчей
                matches_text = f"{player['matches_played']}"
                if player['matches_played'] == 1:
                    matches_text += " матч"
                elif 2 <= player['matches_played'] <= 4:
                    matches_text += " матча"
                else:
                    matches_text += " матчей"
                
                text += f"{medal:3} | {username} | {matches_text:3}|{player['exact_scores']:3} |{player['total_points']:3}\n"
            
            text += "```\n\n"
            text += f"📊 Всего игроков: {total_players}\n"
            text += f"📄 Страница {page + 1}/{(total_players + players_per_page - 1) // players_per_page}"
            
            await safe_edit_message(
                callback,
                text,
                get_tournament_leaderboard_keyboard(tournament_id, page, total_players, players_per_page)
            )
        else:
            text = f"🏆 **Рейтинг игроков: {tournament[1]}**\n\n"
            text += "📊 В этом турнире пока нет результатов для составления рейтинга.\n\n"
            text += "Рейтинг появится после того как администратор введет результаты матчей."
            
            await safe_edit_message(
                callback,
                text,
                get_tournament_detail_keyboard(tournament_id)
            )
    except (ValueError, IndexError) as e:
        logging.error(f"Error in tournament_leaderboard_callback: {e}, data: {callback.data}")
        await callback.answer("❌ Ошибка при загрузке рейтинга", show_alert=True)

async def tournament_rules_callback(callback: CallbackQuery, state: FSMContext):
    """Правила турнира"""
    await state.finish()
    
    try:
        parts = callback.data.split('_')
        if len(parts) < 2:
            await callback.answer("❌ Ошибка: неверный формат данных", show_alert=True)
            return
        
        tournament_id = int(parts[1])  # rules_123
        
        # Получаем описание системы подсчета очков
        scoring_rules = get_scoring_rules_description()
        
        text = f"""📖 **Правила турнира**

🏆 **Основные правила:**
• Ставки принимаются до начала матча
• Одна ставка на матч
• Результаты определяются администратором

{scoring_rules}

📞 **По вопросам обращайтесь к администратору**"""
        
        await safe_edit_message(
            callback,
            text,
            get_tournament_detail_keyboard(tournament_id)
        )
    except (ValueError, IndexError) as e:
        logging.error(f"Error in tournament_rules_callback: {e}, data: {callback.data}")
        await callback.answer("❌ Ошибка при загрузке правил", show_alert=True)

async def user_match_detail_callback(callback: CallbackQuery, state: FSMContext):
    """Детальная информация о матче для пользователя"""
    await state.finish()
    
    match_id = int(callback.data.split('_')[2])
    user_id = callback.from_user.id
    
    db = DatabaseHandler('users.db')
    match = db.get_match(match_id)
    
    if not match:
        await callback.answer("❌ Матч не найден.", show_alert=True)
        return
    
    # Проверяем, не истекло ли время матча
    if db.is_match_expired(match[2], match[3]):
        await callback.answer("⏰ Время для ставок на этот матч истекло.", show_alert=True)
        
        # Возвращаем к списку матчей
        tournament = db.get_tournament(match[1])
        available_matches = db.get_available_tournament_matches(match[1], user_id)
        
        text = f"🏆 Турнир: {tournament[1]}\n\n"
        text += "⏰ Время для ставок на выбранный матч истекло.\n\n"
        
        if available_matches:
            text += "Выберите другой матч:\n\n"
            for available_match in available_matches:
                text += f"📅 {available_match[2]} {available_match[3]} - {available_match[4]} vs {available_match[5]}\n\n"
        
        await safe_edit_message(
            callback,
            text,
            get_user_tournament_matches_keyboard(match[1], available_matches, "all_tournaments")
        )
        return
    
    tournament = db.get_tournament(match[1])
    user_bet = db.get_user_bet(user_id, match_id)
    
    if user_bet:
        text = f"""⚽ Информация о матче:

🏆 Турнир: {tournament[1]}
📅 Дата: {match[2]}
⏰ Время: {match[3]}
⚔️ Матч: {match[4]} vs {match[5]}

✅ Ваш счет: {user_bet[3]}
📅 Дата ставки: {user_bet[4]}"""
        
        await safe_edit_message(
            callback,
            text,
            get_back_keyboard(f"all_tournament_{match[1]}", "🔙 Назад к турниру")
        )
    else:
        text = f"""⚽ Ввод счета для матча:

🏆 Турнир: {tournament[1]}
📅 Дата: {match[2]}
⏰ Время: {match[3]}
⚔️ Матч: {match[4]} vs {match[5]}

📝 Введите счет матча в формате X-Y (например: 2-1):"""
        
        async with state.proxy() as data:
            data['match_id'] = match_id
            data['match_info'] = f"{match[4]} vs {match[5]}"
            data['tournament_id'] = match[1]
        
        await safe_edit_message(
            callback,
            text,
            get_back_keyboard(f"all_tournament_{match[1]}", "🔙 Назад к турниру")
        )
        await UserBetStates.waiting_for_score.set()

async def change_username_callback(callback: CallbackQuery, state: FSMContext):
    """Начало изменения логина"""
    await safe_edit_message(
        callback,
        "Введите новый логин (только латинские буквы, цифры и нижнее подчеркивание, 3-20 символов):\n\nДля отмены нажмите кнопку 'Назад'",
        get_back_keyboard()
    )
    await ProfileStates.waiting_for_username.set()

async def change_password_callback(callback: CallbackQuery, state: FSMContext):
    """Начало изменения пароля"""
    await safe_edit_message(
        callback,
        "🔐 Изменение пароля\n\nВведите ваш текущий пароль для подтверждения:\n\nДля отмены нажмите кнопку 'Назад'",
        get_back_keyboard()
    )
    async with state.proxy() as data:
        data['step'] = 'waiting_current_password'
    await ProfileStates.waiting_for_password.set()

async def process_username(message: Message, state: FSMContext):
    """Обработка нового логина"""
    new_username = message.text.strip()
    
    if not validate_username(new_username):
        await message.answer("❌ Неверный формат логина. Используйте латинские буквы, цифры и нижнее подчеркивание (3-20 символов).")
        return
    
    db = DatabaseHandler('users.db')
    user_id = message.from_user.id
    
    # Проверка занятости логина
    if db.is_username_taken(new_username):
        current_user = db.get_user(user_id)
        if current_user and current_user.username == new_username:
            await message.answer("ℹ️ Это ваш текущий логин. Введите другой логин для изменения:")
        else:
            await message.answer("❌ Этот логин уже занят. Выберите другой логин:")
        return
    
    if db.update_profile(user_id, username=new_username):
        await message.answer(
            "✅ Логин успешно обновлен!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await message.answer(
            "👤 Личный кабинет. Выберите действие:",
            reply_markup=get_profile_inline_keyboard()
        )
    else:
        await message.answer("❌ Ошибка при обновлении логина.")
    
    await state.finish()

async def process_password_change(message: Message, state: FSMContext):
    """Обработка смены пароля"""
    password = message.text.strip()
    
    async with state.proxy() as data:
        current_step = data.get('step', 'waiting_current_password')
    
    db = DatabaseHandler('users.db')
    user_id = message.from_user.id
    
    if current_step == 'waiting_current_password':
        # Проверяем текущий пароль
        hashed_current_password = hash_password(password)
        if not db.verify_password(user_id, hashed_current_password):
            await message.answer("❌ Неверный текущий пароль. Попробуйте еще раз:")
            return
        
        # Переходим к следующему шагу
        async with state.proxy() as data:
            data['step'] = 'waiting_new_password'
        
        await message.answer("✅ Текущий пароль подтвержден!\n\nТеперь введите новый пароль (минимум 6 символов):")
    
    elif current_step == 'waiting_new_password':
        # Проверяем новый пароль
        if len(password) < 6:
            await message.answer("❌ Пароль слишком короткий. Минимальная длина - 6 символов. Попробуйте еще раз:")
            return
        
        # Хешируем и обновляем пароль
        hashed_new_password = hash_password(password)
        
        if db.update_user_password(user_id, hashed_new_password):
            await message.answer(
                "✅ Пароль успешно изменен!",
                reply_markup=types.ReplyKeyboardRemove()
            )
            await message.answer(
                "👤 Личный кабинет. Выберите действие:",
                reply_markup=get_profile_inline_keyboard()
            )
        else:
            await message.answer("❌ Ошибка при изменении пароля. Попробуйте позже.")
        
        await state.finish()

async def process_score_message(message: Message, state: FSMContext):
    """Обработка сообщения с счетом"""
    score = message.text.strip()
    
    if not validate_score(score):
        await message.answer("❌ Неверный формат счета. Используйте формат X-Y (например: 2-1). Попробуйте еще раз:")
        return
    
    async with state.proxy() as data:
        match_id = data['match_id']
        match_info = data['match_info']
        tournament_id = data['tournament_id']
    
    db = DatabaseHandler('users.db')
    user_id = message.from_user.id
    
    # Проверяем, не истекло ли время матча перед сохранением ставки
    match = db.get_match(match_id)
    if match and db.is_match_expired(match[2], match[3]):
        await message.answer(
            "⏰ Время для ставок на этот матч истекло. Ставка не принята.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        # Возвращаем к списку доступных матчей
        tournament = db.get_tournament(tournament_id)
        available_matches = db.get_available_tournament_matches(tournament_id, user_id)
        
        text = f"🏆 Турнир: {tournament[1]}\n\n"
        
        if available_matches:
            text += "Выберите доступный матч:\n\n"
            for available_match in available_matches:
                text += f"📅 {available_match[2]} {available_match[3]} - {available_match[4]} vs {available_match[5]}\n\n"
        
        await message.answer(
            text,
            reply_markup=get_user_tournament_matches_keyboard(tournament_id, available_matches, "all_tournaments")
        )
        await state.finish()
        return
    
    if db.add_user_bet(user_id, match_id, score):
        await message.answer(
            f"✅ Счет {score} для матча {match_info} успешно сохранен!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        # Проверяем остались ли доступные матчи
        tournament = db.get_tournament(tournament_id)
        available_matches = db.get_available_tournament_matches(tournament_id, user_id)
        
        if available_matches:
            text = f"🏆 Турнир: {tournament[1]}\n\n✅ Ваша ставка сохранена!\n\nВыберите следующий матч:\n\n"
            for match in available_matches:
                text += f"📅 {match[2]} {match[3]} - {match[4]} vs {match[5]}\n\n"
            
            await message.answer(
                text,
                reply_markup=get_user_tournament_matches_keyboard(tournament_id, available_matches, "all_tournaments")
            )
        else:
            text = f"🏆 Турнир: {tournament[1]}\n\n🎉 Поздравляем! Вы сделали ставки на все доступные матчи!\n\nТеперь турнир доступен в разделе '🏆 Мои турниры'"
            
            await message.answer(
                text,
                reply_markup=get_back_keyboard("tournaments_main", "🔙 В раздел турниров")
            )
    else:
        await message.answer("❌ Ошибка при сохранении ставки. Попробуйте еще раз.")
    
    await state.finish()

async def cancel_operation(callback: CallbackQuery, state: FSMContext):
    """Отмена операции"""
    await state.finish()
    await callback.message.edit_text(
        "❌ Операция отменена.",
        reply_markup=get_profile_inline_keyboard()
    )

async def no_action_callback(callback: CallbackQuery):
    """Обработчик для кнопок без действия"""
    await callback.answer("⏳ Эта функция находится в разработке", show_alert=True)

async def view_player_bets_callback(callback: CallbackQuery, state: FSMContext):
    """Просмотр завершенных ставок другого игрока"""
    await state.finish()
    
    try:
        parts = callback.data.split('_')
        if len(parts) < 4:
            await callback.answer("❌ Ошибка: неверный формат данных", show_alert=True)
            return
        
        tournament_id = int(parts[2])  # view_bets_123_456_0
        target_user_id = int(parts[3])
        
        # Получаем номер страницы (для возврата)
        page = 0
        if len(parts) > 4:
            try:
                page = int(parts[4])
            except (ValueError, IndexError):
                page = 0
        
        db = DatabaseHandler('users.db')
        tournament = db.get_tournament(tournament_id)
        target_user = db.get_user(target_user_id)
        
        if not tournament or not target_user:
            await callback.answer("❌ Турнир или игрок не найден.", show_alert=True)
            return
        
        # Получаем завершенные ставки игрока
        completed_bets = db.get_user_completed_bets(target_user_id, tournament_id)
        
        if completed_bets:
            username = target_user.username or f"ID{target_user_id}"
            text = f"📊 **Завершенные ставки игрока: {username}**\n"
            text += f"🏆 Турнир: {tournament[1]}\n\n"
            
            for bet in completed_bets:
                match_result = bet[8] if len(bet) > 8 else None
                
                bet_text = f"📅 {bet[4]} | {bet[5]} | {bet[6]} vs {bet[7]} | Счет: {bet[2]}"
                
                if (match_result and 
                    match_result != 'None' and 
                    '-' in str(match_result) and
                    all(c.isdigit() or c == '-' for c in str(match_result).strip())):
                    bet_text += f" | 🎯 Итог: `{match_result}`"
                    
                    # Рассчитываем и добавляем очки
                    points = calculate_points(bet[2], match_result)
                    bet_text += f" | Очки: {points}"
                else:
                    # Матч истек, но результата нет
                    bet_text += " | 🎯 Итог: `Ожидается`"
                
                text += bet_text + "\n\n"
            
        else:
            username = target_user.username or f"ID{target_user_id}"
            text = f"📊 **Завершенные ставки игрока: {username}**\n"
            text += f"🏆 Турнир: {tournament[1]}\n\n"
            text += "📭 У этого игрока пока нет завершенных ставок для просмотра.\n\n"
            text += "Ставки появятся здесь после начала матчей."
        
        await safe_edit_message(
            callback,
            text,
            get_player_bets_keyboard(tournament_id, target_user_id, page)
        )
        
    except (ValueError, IndexError) as e:
        logging.error(f"Error in view_player_bets_callback: {e}, data: {callback.data}")
        await callback.answer("❌ Ошибка при загрузке ставок игрока", show_alert=True)

def register_callback_handlers(dp: Dispatcher):
    """Регистрация обработчиков колбэков"""
    
    # Основная навигация
    navigation_handlers = [
        "main_menu", "profile", "tournaments_main", 
        "all_tournaments", "my_tournaments", "help", "about"
    ]
    
    for handler in navigation_handlers:
        dp.register_callback_query_handler(
            handle_navigation, 
            lambda c, h=handler: c.data == h, 
            state="*"
        )
    
    # Профиль пользователя
    dp.register_callback_query_handler(my_profile_callback, lambda c: c.data == "my_profile", state="*")
    dp.register_callback_query_handler(change_username_callback, lambda c: c.data == "change_username", state="*")
    dp.register_callback_query_handler(change_password_callback, lambda c: c.data == "change_password", state="*")
    
    # Турниры - общие
    dp.register_callback_query_handler(all_tournament_detail_callback, lambda c: c.data.startswith("all_tournament_"), state="*")
    dp.register_callback_query_handler(my_tournament_detail_callback, lambda c: c.data.startswith("my_tournament_detail_"), state="*")
    
    # Детали турнира - новые префиксы
    dp.register_callback_query_handler(tournament_my_bets_callback, lambda c: c.data.startswith("bets_"), state="*")
    dp.register_callback_query_handler(tournament_leaderboard_callback, lambda c: c.data.startswith("leaderboard_"), state="*")
    dp.register_callback_query_handler(tournament_rules_callback, lambda c: c.data.startswith("rules_"), state="*")
    dp.register_callback_query_handler(tournament_players_callback, lambda c: c.data.startswith("players_"), state="*")
    
    # Просмотр ставок других игроков
    dp.register_callback_query_handler(view_player_bets_callback, lambda c: c.data.startswith("view_bets_"), state="*")
    
    # Матчи и ставки
    dp.register_callback_query_handler(user_match_detail_callback, lambda c: c.data.startswith("user_match_"), state="*")
    
    # FSM обработчики
    dp.register_message_handler(process_username, state=ProfileStates.waiting_for_username)
    dp.register_message_handler(process_password_change, state=ProfileStates.waiting_for_password)
    dp.register_message_handler(process_score_message, state=UserBetStates.waiting_for_score)
    
    # Отмена операций
    dp.register_callback_query_handler(cancel_operation, lambda c: c.data == "main_menu", state=[ProfileStates.waiting_for_username, ProfileStates.waiting_for_password])
    
    # Кнопки без действия
    dp.register_callback_query_handler(no_action_callback, lambda c: c.data == "no_action")
