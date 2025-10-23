import re
import phonenumbers
from typing import Optional, Tuple

def validate_email(email: str) -> Tuple[bool, str]:
    """Валидация email адреса"""
    if not email:
        return False, "Email не может быть пустым"
    
    if len(email) > 100:
        return False, "Email слишком длинный"
    
    # Базовый паттерн для email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Неверный формат email"
    
    return True, "OK"

def validate_phone(phone: str) -> Tuple[bool, str]:
    """Валидация номера телефона"""
    if not phone:
        return False, "Номер телефона не может быть пустым"
    
    try:
        # Парсим номер телефона
        parsed_number = phonenumbers.parse(phone, "RU")
        
        if not phonenumbers.is_valid_number(parsed_number):
            return False, "Неверный номер телефона"
        
        # Форматируем номер в международном формате
        formatted_phone = phonenumbers.format_number(
            parsed_number, 
            phonenumbers.PhoneNumberFormat.E164
        )
        return True, formatted_phone
        
    except phonenumbers.NumberParseException:
        return False, "Не могу распознать номер телефона"

def validate_username(username: str) -> Tuple[bool, str]:
    """Валидация логина"""
    if not username:
        return False, "Логин не может быть пустым"
    
    if len(username) < 3:
        return False, "Логин должен содержать минимум 3 символа"
    
    if len(username) > 50:
        return False, "Логин слишком длинный"
    
    # Проверяем допустимые символы
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Логин может содержать только буквы, цифры и подчеркивание"
    
    return True, "OK"

def validate_full_name(full_name: str) -> Tuple[bool, str]:
    """Валидация ФИО"""
    if not full_name:
        return False, "ФИО не может быть пустым"
    
    if len(full_name) < 2:
        return False, "ФИО должно содержать минимум 2 символа"
    
    if len(full_name) > 100:
        return False, "ФИО слишком длинное"
    
    # Проверяем, что есть хотя бы 2 слова
    words = full_name.split()
    if len(words) < 2:
        return False, "Введите Фамилию и Имя (минимум 2 слова)"
    
    return True, "OK"

def is_login_identifier(text: str) -> str:
    """Определяет тип идентификатора для входа"""
    if not text:
        return "invalid"
    
    text = text.strip()
    
    # Проверяем email
    email_valid, _ = validate_email(text)
    if email_valid:
        return "email"
    
    # Проверяем телефон
    phone_valid, _ = validate_phone(text)
    if phone_valid:
        return "phone"
    
    # Проверяем логин
    username_valid, _ = validate_username(text)
    if username_valid:
        return "username"
    
    return "invalid"