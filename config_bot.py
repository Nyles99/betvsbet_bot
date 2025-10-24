import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

@dataclass
class Config:
    """Класс для хранения конфигурации бота"""
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')
    ADMIN_ID: int = int(os.getenv('ADMIN_ID', 831040832))  # Ваш ID по умолчанию
    
    # Настройки базы данных
    DATABASE_NAME: str = 'users.db'
    
    # Длины полей
    MAX_USERNAME_LENGTH: int = 50
    MAX_EMAIL_LENGTH: int = 100
    MAX_NAME_LENGTH: int = 100

# Создаем экземпляр конфигурации
config = Config()