from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                          InlineKeyboardMarkup, InlineKeyboardButton)

def get_main_menu():
    """Клавиатура главного меню"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    
    profile_btn = KeyboardButton('👤 Личный кабинет')
    help_btn = KeyboardButton('❓ Помощь')
    
    keyboard.add(profile_btn)
    keyboard.add(help_btn)
    
    return keyboard

def get_start_keyboard():
    """Клавиатура для начала работы"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    
    login_btn = KeyboardButton('🔐 Войти')
    register_btn = KeyboardButton('📝 Регистрация')
    help_btn = KeyboardButton('❓ Помощь')
    
    keyboard.add(login_btn, register_btn)
    keyboard.add(help_btn)
    
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

def get_confirm_keyboard():
    """Клавиатура с кнопками подтверждения"""
    keyboard = InlineKeyboardMarkup()
    
    yes_btn = InlineKeyboardButton('✅ Да', callback_data='confirm_yes')
    no_btn = InlineKeyboardButton('❌ Нет', callback_data='confirm_no')
    
    keyboard.add(yes_btn, no_btn)
    return keyboard