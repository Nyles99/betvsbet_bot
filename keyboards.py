from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                          InlineKeyboardMarkup, InlineKeyboardButton)

def get_main_menu():
    """Клавиатура главного меню"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    
    profile_btn = KeyboardButton('👤 Личный кабинет')
    tournaments_btn = KeyboardButton('⚽ Турниры')
    about_btn = KeyboardButton('ℹ️ О нас')
    help_btn = KeyboardButton('❓ Помощь')
    
    keyboard.add(profile_btn, tournaments_btn)
    keyboard.add(about_btn, help_btn)
    
    return keyboard

def get_start_keyboard():
    """Клавиатура для начала работы"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    
    login_btn = KeyboardButton('🔐 Войти')
    register_btn = KeyboardButton('📝 Регистрация')
    about_btn = KeyboardButton('ℹ️ О нас')
    help_btn = KeyboardButton('❓ Помощь')
    
    keyboard.add(login_btn, register_btn)
    keyboard.add(about_btn, help_btn)
    
    return keyboard

def get_registration_keyboard():
    """Клавиатура для регистрации"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    back_btn = KeyboardButton('🔙 Назад')
    keyboard.add(back_btn)
    return keyboard

def get_phone_keyboard():
    """Клавиатура для запроса номера телефона"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    phone_btn = KeyboardButton('📱 Отправить номер телефона', request_contact=True)
    back_btn = KeyboardButton('🔙 Назад')
    keyboard.add(phone_btn)
    keyboard.add(back_btn)
    return keyboard

def get_profile_keyboard():
    """Инлайн клавиатура личного кабинета"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    edit_username_btn = InlineKeyboardButton('✏️ Логин', callback_data='edit_username')
    edit_email_btn = InlineKeyboardButton('✏️ Email', callback_data='edit_email')
    edit_phone_btn = InlineKeyboardButton('✏️ Телефон', callback_data='edit_phone')
    edit_name_btn = InlineKeyboardButton('✏️ ФИО', callback_data='edit_name')
    change_password_btn = InlineKeyboardButton('🔑 Пароль', callback_data='change_password')
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')
    
    keyboard.add(edit_username_btn, edit_email_btn)
    keyboard.add(edit_phone_btn, edit_name_btn)
    keyboard.add(change_password_btn)
    keyboard.add(back_btn)
    
    return keyboard

def get_tournaments_keyboard(is_admin: bool = False):
    """Инлайн клавиатура для турниров"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    list_btn = InlineKeyboardButton('📋 Список турниров', callback_data='tournaments_list')
    
    # Кнопки только для администратора
    if is_admin:
        add_btn = InlineKeyboardButton('➕ Добавить турнир', callback_data='tournament_add')
        manage_btn = InlineKeyboardButton('🛠 Управление турнирами', callback_data='tournaments_manage')
        keyboard.add(add_btn, manage_btn)
    
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')
    
    keyboard.add(list_btn)
    keyboard.add(back_btn)
    
    return keyboard

def get_tournaments_list_keyboard(tournaments: list, is_admin: bool = False):
    """Инлайн клавиатура со списком турниров"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    for tournament in tournaments:
        btn = InlineKeyboardButton(
            f"⚽ {tournament['name']}", 
            callback_data=f'tournament_matches_{tournament["id"]}'
        )
        keyboard.add(btn)
    
    if is_admin:
        add_btn = InlineKeyboardButton('➕ Добавить турнир', callback_data='tournament_add')
        manage_btn = InlineKeyboardButton('🛠 Управление', callback_data='tournaments_manage')
        keyboard.add(add_btn, manage_btn)
    
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data='tournaments_back')
    keyboard.add(back_btn)
    
    return keyboard

def get_tournament_participation_keyboard(tournament_id: int):
    """Клавиатура для участия в турнире"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    participate_btn = InlineKeyboardButton('✅ Готов участвовать', callback_data=f'participate_{tournament_id}')
    decline_btn = InlineKeyboardButton('❌ Отказаться', callback_data=f'decline_{tournament_id}')
    
    keyboard.add(participate_btn, decline_btn)
    return keyboard

def get_tournament_matches_keyboard(matches: list, tournament_id: int, is_admin: bool = False):
    """Инлайн клавиатура со списком матчей турнира"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for match in matches:
        # Форматируем дату и время
        match_date = match['match_date']
        match_time = match['match_time']
        btn_text = f"{match_date} {match_time} {match['team1']} - {match['team2']}"
        
        btn = InlineKeyboardButton(
            btn_text, 
            callback_data=f'match_{match["id"]}'
        )
        keyboard.add(btn)
    
    # Кнопка правил турнира
    rules_btn = InlineKeyboardButton('📋 Правила турнира', callback_data=f'tournament_rules_{tournament_id}')
    keyboard.add(rules_btn)
    
    # Кнопка добавления матча только для администратора
    if is_admin:
        add_match_btn = InlineKeyboardButton('➕ Добавить матч', callback_data=f'add_match_{tournament_id}')
        keyboard.add(add_match_btn)
    
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data='tournaments_back')
    keyboard.add(back_btn)
    
    return keyboard

def get_tournament_rules_keyboard(tournament_id: int, is_admin: bool = False):
    """Клавиатура для просмотра правил турнира"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    back_btn = InlineKeyboardButton('🔙 Назад к матчам', callback_data=f'tournament_matches_{tournament_id}')
    
    if is_admin:
        edit_rules_btn = InlineKeyboardButton('✏️ Редактировать правила', callback_data=f'edit_rules_{tournament_id}')
        keyboard.add(edit_rules_btn)
    
    keyboard.add(back_btn)
    return keyboard

def get_tournaments_for_matches_keyboard(tournaments: list):
    """Клавиатура для выбора турнира при добавлении матча"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for tournament in tournaments:
        btn = InlineKeyboardButton(
            f"⚽ {tournament['name']}", 
            callback_data=f'select_tournament_{tournament["id"]}'
        )
        keyboard.add(btn)
    
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data='matches_back')
    keyboard.add(back_btn)
    
    return keyboard

def get_tournament_manage_keyboard(tournament_id: int):
    """Инлайн клавиатура для управления конкретным турниром"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    edit_btn = InlineKeyboardButton('✏️ Редактировать', callback_data=f'tournament_edit_{tournament_id}')
    delete_btn = InlineKeyboardButton('🗑 Удалить', callback_data=f'tournament_delete_{tournament_id}')
    matches_btn = InlineKeyboardButton('⚽ Управление матчами', callback_data=f'tournament_matches_{tournament_id}')
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data='tournaments_manage_back')
    
    keyboard.add(edit_btn, delete_btn)
    keyboard.add(matches_btn)
    keyboard.add(back_btn)
    
    return keyboard

def get_tournaments_manage_list_keyboard(tournaments: list):
    """Инлайн клавиатура для управления всеми турнирами"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    for tournament in tournaments:
        btn = InlineKeyboardButton(
            f"⚽ {tournament['name']}", 
            callback_data=f'tournament_manage_{tournament["id"]}'
        )
        keyboard.add(btn)
    
    add_btn = InlineKeyboardButton('➕ Добавить турнир', callback_data='tournament_add')
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data='admin_back')
    keyboard.add(add_btn)
    keyboard.add(back_btn)
    
    return keyboard

def get_admin_keyboard():
    """Клавиатура админ-панели"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    users_btn = InlineKeyboardButton('📋 Список пользователей', callback_data='admin_users_list')
    search_btn = InlineKeyboardButton('🔍 Поиск пользователя', callback_data='admin_search_user')
    ban_btn = InlineKeyboardButton('🚫 Забанить', callback_data='admin_ban_user')
    unban_btn = InlineKeyboardButton('✅ Разбанить', callback_data='admin_unban_user')
    tournaments_btn = InlineKeyboardButton('⚽ Управление турнирами', callback_data='admin_tournaments')
    matches_btn = InlineKeyboardButton('➕ Управление матчами', callback_data='admin_matches')
    stats_btn = InlineKeyboardButton('📊 Статистика', callback_data='admin_stats')
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data='admin_back')
    
    keyboard.add(users_btn, search_btn)
    keyboard.add(ban_btn, unban_btn)
    keyboard.add(tournaments_btn, matches_btn)
    keyboard.add(stats_btn)
    keyboard.add(back_btn)
    
    return keyboard

def get_admin_matches_keyboard():
    """Клавиатура управления матчами в админ-панели"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    add_match_btn = InlineKeyboardButton('➕ Добавить матч', callback_data='admin_add_match')
    view_matches_btn = InlineKeyboardButton('📋 Просмотр матчей', callback_data='admin_view_matches')
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data='admin_back')
    
    keyboard.add(add_match_btn, view_matches_btn)
    keyboard.add(back_btn)
    
    return keyboard

def get_back_keyboard():
    """Клавиатура с кнопкой Назад"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    back_btn = KeyboardButton('🔙 Назад')
    keyboard.add(back_btn)
    return keyboard

def get_cancel_keyboard():
    """Клавиатура с кнопкой Отмена"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    cancel_btn = KeyboardButton('❌ Отмена')
    keyboard.add(cancel_btn)
    return keyboard

def get_cancel_match_keyboard():
    """Клавиатура с кнопкой Отмена для процесса добавления матча"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    cancel_btn = KeyboardButton('❌ Отмена')
    keyboard.add(cancel_btn)
    return keyboard

def get_confirm_keyboard():
    """Клавиатура с кнопками подтверждения"""
    keyboard = InlineKeyboardMarkup()
    
    yes_btn = InlineKeyboardButton('✅ Да', callback_data='confirm_yes')
    no_btn = InlineKeyboardButton('❌ Нет', callback_data='confirm_no')
    
    keyboard.add(yes_btn, no_btn)
    return keyboard

def get_user_actions_keyboard(user_id: int, is_banned: bool):
    """Клавиатура действий с пользователем в админ-панели"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    if is_banned:
        unban_btn = InlineKeyboardButton('✅ Разбанить', callback_data=f'unban_{user_id}')
        keyboard.add(unban_btn)
    else:
        ban_btn = InlineKeyboardButton('🚫 Забанить', callback_data=f'ban_{user_id}')
        keyboard.add(ban_btn)
    
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data='admin_back')
    keyboard.add(back_btn)
    
    return keyboard

def get_tournament_edit_rules_keyboard(tournament_id: int):
    """Клавиатура для редактирования правил турнира"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    save_btn = InlineKeyboardButton('💾 Сохранить правила', callback_data=f'save_rules_{tournament_id}')
    cancel_btn = InlineKeyboardButton('❌ Отмена', callback_data=f'tournament_rules_{tournament_id}')
    
    keyboard.add(save_btn, cancel_btn)
    return keyboard