import aiosqlite
import logging
import hashlib
import secrets
from typing import Optional, Dict, Any
from config import config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name: str = config.DATABASE_NAME):
        self.db_name = db_name
    
    async def create_tables(self):
        """Создание таблиц в базе данных"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                # Таблица пользователей
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER UNIQUE NOT NULL,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        password_salt TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        phone TEXT UNIQUE,
                        full_name TEXT NOT NULL,
                        tg_username TEXT,
                        tg_first_name TEXT,
                        tg_last_name TEXT,
                        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Индексы для быстрого поиска
                await db.execute('CREATE INDEX IF NOT EXISTS idx_username ON users(username)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_email ON users(email)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_phone ON users(phone)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON users(user_id)')
                
                await db.commit()
                logger.info("Таблицы и индексы успешно созданы")
                
        except Exception as e:
            logger.error(f"Ошибка при создании таблиц: {e}")
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Хеширование пароля с солью"""
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def _generate_salt(self) -> str:
        """Генерация соли для пароля"""
        return secrets.token_hex(16)
    
    async def add_user(self, user_id: int, username: str, password: str, 
                      email: str, phone: str, full_name: str,
                      tg_username: str, tg_first_name: str, tg_last_name: str):
        """Добавление нового пользователя в базу данных"""
        try:
            # Генерируем соль и хешируем пароль
            salt = self._generate_salt()
            password_hash = self._hash_password(password, salt)
            
            async with aiosqlite.connect(self.db_name) as db:
                await db.execute('''
                    INSERT INTO users 
                    (user_id, username, password_hash, password_salt, email, phone, 
                     full_name, tg_username, tg_first_name, tg_last_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, username, password_hash, salt, email, phone,
                      full_name, tg_username, tg_first_name, tg_last_name))
                
                await db.commit()
                logger.info(f"Пользователь {username} успешно добавлен")
                return True
                
        except aiosqlite.IntegrityError as e:
            if "username" in str(e):
                logger.error(f"Логин {username} уже занят")
                return "username_exists"
            elif "email" in str(e):
                logger.error(f"Email {email} уже занят")
                return "email_exists"
            elif "phone" in str(e):
                logger.error(f"Телефон {phone} уже занят")
                return "phone_exists"
            else:
                logger.error(f"Ошибка целостности при добавлении пользователя: {e}")
                return "error"
        except Exception as e:
            logger.error(f"Ошибка при добавлении пользователя: {e}")
            return "error"
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе по ID"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT * FROM users WHERE user_id = ?
                ''', (user_id,))
                
                user = await cursor.fetchone()
                return dict(user) if user else None
                
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя по ID: {e}")
            return None
    
    async def get_user_by_login(self, login_identifier: str) -> Optional[Dict[str, Any]]:
        """Получение пользователя по логину, email или телефону"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT * FROM users 
                    WHERE username = ? OR email = ? OR phone = ?
                ''', (login_identifier, login_identifier, login_identifier))
                
                user = await cursor.fetchone()
                return dict(user) if user else None
                
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя по логину: {e}")
            return None
    
    async def verify_password(self, login_identifier: str, password: str) -> bool:
        """Проверка пароля пользователя"""
        user = await self.get_user_by_login(login_identifier)
        if not user:
            return False
        
        password_hash = self._hash_password(password, user['password_salt'])
        return password_hash == user['password_hash']
    
    async def user_exists_by_tg_id(self, user_id: int) -> bool:
        """Проверка существования пользователя по Telegram ID"""
        user = await self.get_user_by_id(user_id)
        return user is not None
    
    async def update_last_login(self, user_id: int):
        """Обновление времени последнего входа"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                await db.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                ''', (user_id,))
                await db.commit()
        except Exception as e:
            logger.error(f"Ошибка при обновлении времени входа: {e}")
    
    async def update_user_field(self, user_id: int, field: str, value: str) -> bool:
        """Обновление поля пользователя"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                await db.execute(f'''
                    UPDATE users SET {field} = ? WHERE user_id = ?
                ''', (value, user_id))
                await db.commit()
                return True
        except aiosqlite.IntegrityError as e:
            logger.error(f"Ошибка целостности при обновлении {field}: {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка при обновлении {field}: {e}")
            return False
    
    async def check_field_unique(self, field: str, value: str, exclude_user_id: int = None) -> bool:
        """Проверка уникальности поля"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                if exclude_user_id:
                    cursor = await db.execute(f'''
                        SELECT COUNT(*) FROM users 
                        WHERE {field} = ? AND user_id != ?
                    ''', (value, exclude_user_id))
                else:
                    cursor = await db.execute(f'''
                        SELECT COUNT(*) FROM users WHERE {field} = ?
                    ''', (value,))
                
                count = await cursor.fetchone()
                return count[0] == 0
                
        except Exception as e:
            logger.error(f"Ошибка при проверке уникальности {field}: {e}")
            return False

# Создаем экземпляр базы данных
db = Database()