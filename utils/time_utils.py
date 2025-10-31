from datetime import datetime
import pytz

def get_moscow_time():
    """Получение текущего московского времени"""
    moscow_tz = pytz.timezone('Europe/Moscow')
    return datetime.now(moscow_tz)

def format_moscow_time(dt=None, format_str='%Y-%m-%d %H:%M:%S'):
    """Форматирование времени в московском часовом поясе"""
    moscow_tz = pytz.timezone('Europe/Moscow')
    if dt is None:
        dt = get_moscow_time()
    elif isinstance(dt, str):
        # Если передана строка, парсим её
        dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        dt = moscow_tz.localize(dt)
    elif dt.tzinfo is None:
        # Если время наивное, локализуем его
        dt = moscow_tz.localize(dt)
    else:
        # Если время уже с часовым поясом, конвертируем в Москву
        dt = dt.astimezone(moscow_tz)
    
    return dt.strftime(format_str)

def format_moscow_date(dt=None):
    """Форматирование даты в московском часовом поясе"""
    return format_moscow_time(dt, '%d.%m.%Y')

def format_moscow_datetime(dt=None):
    """Форматирование даты и времени в московском часовом поясе"""
    return format_moscow_time(dt, '%d.%m.%Y %H:%M')

def parse_user_date(date_str: str):
    """Парсинг даты от пользователя (формат ДД.ММ.ГГГГ)"""
    try:
        moscow_tz = pytz.timezone('Europe/Moscow')
        dt = datetime.strptime(date_str, '%d.%m.%Y')
        return moscow_tz.localize(dt)
    except ValueError:
        return None

def parse_user_time(time_str: str):
    """Парсинг времени от пользователя (формат ЧЧ:ММ)"""
    try:
        moscow_tz = pytz.timezone('Europe/Moscow')
        today = get_moscow_time().date()
        dt = datetime.strptime(time_str, '%H:%M')
        dt = datetime.combine(today, dt.time())
        return moscow_tz.localize(dt)
    except ValueError:
        return None