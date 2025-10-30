import re

def validate_phone_number(phone: str) -> bool:
    """Валидация номера телефона формата +7"""
    # Убираем все пробелы и дефисы
    phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    # Проверяем формат +7XXXXXXXXXX
    pattern = r'^\+7\d{10}$'
    return bool(re.match(pattern, phone))

def validate_username(username: str) -> bool:
    """Валидация логина"""
    if len(username) < 3 or len(username) > 20:
        return False
    pattern = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, username))

def validate_full_name(full_name: str) -> bool:
    """Валидация ФИО"""
    if len(full_name) < 2 or len(full_name) > 100:
        return False
    # Проверяем, что в ФИО есть только буквы и пробелы
    pattern = r'^[a-zA-Zа-яА-ЯёЁ\s\-]+$'
    return bool(re.match(pattern, full_name))

def format_phone_number(phone: str) -> str:
    """Форматирование номера телефона в формат +7"""
    # Убираем все нецифровые символы
    digits = ''.join(filter(str.isdigit, phone))
    
    # Если номер начинается с 8, заменяем на +7
    if digits.startswith('8') and len(digits) == 11:
        return '+7' + digits[1:]
    # Если номер начинается с 7 и имеет 11 цифр
    elif digits.startswith('7') and len(digits) == 11:
        return '+' + digits
    # Если номер имеет 10 цифр (без кода страны)
    elif len(digits) == 10:
        return '+7' + digits
    else:
        return phone

def validate_score(score: str) -> bool:
    """Валидация счета матча в формате X-Y"""
    pattern = r'^\d+-\d+$'
    if not bool(re.match(pattern, score)):
        return False
    
    # Проверяем что числа не слишком большие
    parts = score.split('-')
    if len(parts) != 2:
        return False
    
    try:
        score1 = int(parts[0])
        score2 = int(parts[1])
        # Ограничим разумными значениями (например, до 20 голов)
        return 0 <= score1 <= 20 and 0 <= score2 <= 20
    except ValueError:
        return False

def validate_password(password: str) -> bool:
    """Валидация пароля"""
    return len(password) >= 6