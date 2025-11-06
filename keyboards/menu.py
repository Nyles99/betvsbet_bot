from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

def get_start_keyboard():
    """Стартовая клавиатура с входом и регистрацией"""
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🚪 Вход", callback_data="login"),
        InlineKeyboardButton("📝 Регистрация", callback_data="register"),
        InlineKeyboardButton("ℹ️ Помощь", callback_data="help"),
        InlineKeyboardButton("📞 О нас", callback_data="about")
    )

def get_main_menu():
    """Главное меню"""
    return ReplyKeyboardMarkup([
        ['📱 Отправить номер телефона']
    ], resize_keyboard=True)

def get_phone_keyboard():
    """Клавиатура для запроса номера телефона"""
    return ReplyKeyboardMarkup([
        [KeyboardButton("📱 Отправить номер телефона", request_contact=True)],
        ['🔙 Назад']
    ], resize_keyboard=True, one_time_keyboard=True)

def get_main_inline_keyboard():
    """Основная инлайн клавиатура после регистрации"""
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("👤 Личный кабинет", callback_data="profile"),
        InlineKeyboardButton("🏆 Турниры", callback_data="tournaments_main"),
        InlineKeyboardButton("ℹ️ Помощь", callback_data="help"),
        InlineKeyboardButton("📞 О нас", callback_data="about")
    )

def get_profile_inline_keyboard():
    """Инлайн клавиатура для личного кабинета"""
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("✏️ Изменить логин", callback_data="change_username"),
        InlineKeyboardButton("🔐 Изменить пароль", callback_data="change_password"),
        InlineKeyboardButton("📊 Мой профиль", callback_data="my_profile"),
        InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
    )

def get_tournaments_main_keyboard():
    """Главное меню турниров"""
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🏆 Мои турниры", callback_data="my_tournaments"),
        InlineKeyboardButton("📋 Все турниры", callback_data="all_tournaments"),
        InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
    )

def get_admin_match_detail_keyboard(match_id, tournament_id):
    """Клавиатура для конкретного матча в админке"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton("📝 Внести счет", callback_data=f"enter_result_{match_id}"),
        InlineKeyboardButton("🗑️ Удалить матч", callback_data=f"delete_match_{match_id}"),
        InlineKeyboardButton("🔙 Назад к матчам", callback_data=f"tournament_matches_{tournament_id}")
    )
    
    return keyboard

def get_all_tournaments_keyboard(tournaments):
    """Клавиатура всех доступных турниров"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопки для каждого турнира
    for tournament in tournaments:
        keyboard.add(InlineKeyboardButton(
            f"🏆 {tournament[1]}", 
            callback_data=f"all_tournament_{tournament[0]}"
        ))
    
    # Кнопка обновления и назад
    keyboard.row(
        InlineKeyboardButton("🔄 Обновить", callback_data="all_tournaments"),
        InlineKeyboardButton("🔙 Назад", callback_data="tournaments_main")
    )
    
    return keyboard

def get_my_tournaments_keyboard(tournaments):
    """Клавиатура турниров пользователя"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопки для каждого турнира
    for tournament in tournaments:
        keyboard.add(InlineKeyboardButton(
            f"🏆 {tournament[1]}", 
            callback_data=f"my_tournament_detail_{tournament[0]}"
        ))
    
    # Кнопка назад
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="tournaments_main"))
    
    return keyboard

def get_tournament_detail_keyboard(tournament_id, page=0):
    """Клавиатура детальной информации о турнире"""
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("📋 Мои ставки", callback_data=f"bets_{tournament_id}"),
        InlineKeyboardButton("📊 Общая таблица", callback_data=f"leaderboard_{tournament_id}"),
        InlineKeyboardButton("📖 Правила", callback_data=f"rules_{tournament_id}"),
        InlineKeyboardButton("👥 Игроки турнира", callback_data=f"players_{tournament_id}_0"),
        InlineKeyboardButton("🔙 Назад", callback_data="my_tournaments")
    )

def get_tournament_players_keyboard(tournament_id, page, total_pages, players_count):
    """Клавиатура списка игроков турнира с пагинацией и кнопками просмотра ставок"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Кнопки пагинации (только если есть больше одной страницы)
    if total_pages > 1:
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"players_{tournament_id}_{page-1}"))
        
        pagination_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="no_action"))
        
        if page < total_pages - 1:
            pagination_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"players_{tournament_id}_{page+1}"))
        
        if pagination_buttons:
            keyboard.row(*pagination_buttons)
    
    # Кнопка назад к деталям турнира
    keyboard.row(InlineKeyboardButton("🔙 Назад к турниру", callback_data=f"my_tournament_detail_{tournament_id}"))
    
    return keyboard

def get_player_bets_keyboard(tournament_id, user_id, page=0):
    """Клавиатура для просмотра ставок конкретного игрока"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    keyboard.add(
        InlineKeyboardButton("🔙 Назад к игрокам", callback_data=f"players_{tournament_id}_{page}")
    )
    
    return keyboard

def get_player_detail_keyboard(tournament_id, page):
    """Клавиатура детальной информации об игроке"""
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔙 Назад к игрокам", callback_data=f"tournament_players_{tournament_id}_{page}")
    )

def get_user_tournament_matches_keyboard(tournament_id, matches, back_to="tournaments_main"):
    """Клавиатура матчей турнира для пользователя"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопки для каждого матча
    for match in matches:
        match_text = f"📅 {match[2]} {match[3]} - {match[4]} vs {match[5]}"
        # Обрезаем текст если слишком длинный
        if len(match_text) > 60:
            match_text = match_text[:57] + "..."
        keyboard.add(InlineKeyboardButton(
            match_text, 
            callback_data=f"user_match_{match[0]}"
        ))
    
    # Кнопка назад в зависимости от раздела
    if back_to == "all_tournaments":
        keyboard.add(InlineKeyboardButton("🔙 Назад к турнирам", callback_data="all_tournaments"))
    else:
        keyboard.add(InlineKeyboardButton("🔙 Назад к турнирам", callback_data="tournaments_main"))
    
    return keyboard

def get_available_matches_keyboard(matches):
    """Клавиатура доступных матчей для ставок"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопки для каждого матча
    for match in matches:
        match_text = f"📅 {match[2]} {match[3]} - {match[4]} vs {match[5]}"
        # Обрезаем текст если слишком длинный
        if len(match_text) > 60:
            match_text = match_text[:57] + "..."
        keyboard.add(InlineKeyboardButton(
            match_text, 
            callback_data=f"user_match_{match[0]}"
        ))
    
    # Кнопка назад
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
    
    return keyboard

def get_user_bets_tournaments_keyboard(tournaments):
    """Клавиатура турниров со ставками пользователя"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопки для каждого турнира
    for tournament in tournaments:
        keyboard.add(InlineKeyboardButton(
            f"🏆 {tournament[1]}", 
            callback_data=f"bets_tournament_{tournament[0]}"
        ))
    
    # Кнопка назад
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="profile"))
    
    return keyboard

def get_user_tournament_bets_keyboard(tournament_id, bets):
    """Клавиатура ставок пользователя в турнире"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Кнопка назад
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data=f"my_tournament_detail_{tournament_id}"))
    
    return keyboard

def get_tournament_leaderboard_keyboard(tournament_id, page, total_players, players_per_page=10):
    """Клавиатура для рейтинга игроков с пагинацией"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    total_pages = (total_players + players_per_page - 1) // players_per_page
    
    # Кнопки пагинации
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"leaderboard_{tournament_id}_{page-1}"))
    
    pagination_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="no_action"))
    
    if page < total_pages - 1:
        pagination_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"leaderboard_{tournament_id}_{page+1}"))
    
    if pagination_buttons:
        keyboard.row(*pagination_buttons)
    
    # Кнопка обновления и назад
    keyboard.row(
        InlineKeyboardButton("🔄 Обновить", callback_data=f"leaderboard_{tournament_id}_0"),
        InlineKeyboardButton("🔙 Назад к турниру", callback_data=f"my_tournament_detail_{tournament_id}")
    )
    
    return keyboard

def get_admin_main_keyboard():
    """Основная клавиатура админа"""
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🏆 Турниры", callback_data="admin_tournaments"),
        InlineKeyboardButton("👥 Все пользователи", callback_data="admin_users"),
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("🔙 В главное меню", callback_data="main_menu")
    )

def get_admin_tournaments_keyboard(tournaments):
    """Клавиатура турниров для админа"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопки для каждого турнира
    for tournament in tournaments:
        status = "✅" if tournament[3] == 'active' else "❌"
        keyboard.add(InlineKeyboardButton(
            f"{status} {tournament[1]}", 
            callback_data=f"tournament_{tournament[0]}"
        ))
    
    # Кнопки действий
    keyboard.row(
        InlineKeyboardButton("➕ Добавить турнир", callback_data="add_tournament"),
        InlineKeyboardButton("🔙 Назад в админку", callback_data="admin_main")
    )
    
    return keyboard

def get_admin_tournament_detail_keyboard(tournament_id, tournament_status):
    """Клавиатура для конкретного турнира в админке"""
    status_text = "❌ Деактивировать" if tournament_status == 'active' else "✅ Активировать"
    status_data = "deactivate_tournament" if tournament_status == 'active' else "activate_tournament"
    
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("⚽ Матчи турнира", callback_data=f"tournament_matches_{tournament_id}"),
        InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_tournament_{tournament_id}"),
        InlineKeyboardButton(status_text, callback_data=f"{status_data}_{tournament_id}"),
        InlineKeyboardButton("🗑️ Удалить турнир", callback_data=f"delete_tournament_{tournament_id}"),
        InlineKeyboardButton("🔙 Назад к турнирам", callback_data="admin_tournaments")
    )

def get_admin_tournament_matches_keyboard(tournament_id, matches):
    """Клавиатура матчей турнира для админа"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопки для каждого матча
    for match in matches:
        match_text = f"📅 {match[2]} {match[3]} - {match[4]} vs {match[5]}"
        # Обрезаем текст если слишком длинный
        if len(match_text) > 60:
            match_text = match_text[:57] + "..."
        keyboard.add(InlineKeyboardButton(
            match_text, 
            callback_data=f"admin_match_{match[0]}"
        ))
    
    # Кнопки действий
    keyboard.row(
        InlineKeyboardButton("➕ Добавить матч", callback_data=f"add_match_{tournament_id}"),
        InlineKeyboardButton("🔙 Назад к турниру", callback_data=f"tournament_{tournament_id}")
    )
    
    return keyboard

def get_admin_users_keyboard():
    """Клавиатура управления пользователями"""
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔙 Назад в админку", callback_data="admin_main")
    )

def get_back_keyboard(back_data="main_menu", text="🔙 Назад"):
    """Универсальная клавиатура с кнопкой Назад"""
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(text, callback_data=back_data)
    )    

def get_cancel_keyboard():
    """Клавиатура для отмены действия"""
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("❌ Отмена", callback_data="admin_main")
    )

def get_cancel_registration_keyboard():
    """Клавиатура для отмены регистрации"""
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("❌ Отмена", callback_data="start")
    )

def get_cancel_login_keyboard():
    """Клавиатура для отмены входа"""
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("❌ Отмена", callback_data="start")
    )

def get_cancel_to_tournament_keyboard(tournament_id):
    """Клавиатура для отмены действия с возвратом к турниру"""
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("❌ Отмена", callback_data=f"tournament_{tournament_id}")
    )

def get_cancel_to_matches_keyboard(tournament_id):
    """Клавиатура для отмены действия с возвратом к матчам"""
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("❌ Отмена", callback_data=f"tournament_matches_{tournament_id}")
    )

def remove_keyboard():
    """Убрать клавиатуру"""
    return ReplyKeyboardRemove()

def get_no_action_keyboard():
    """Клавиатура для кнопок без действия"""
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("⏳ Функция в разработке", callback_data="no_action")
    )