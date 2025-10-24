import aiosqlite
import logging
import hashlib
import secrets
from typing import Optional, Dict, Any, List
from config_bot import config

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
                        is_banned INTEGER DEFAULT 0,
                        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Таблица турниров
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS tournaments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        rules TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_by INTEGER,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (created_by) REFERENCES users (user_id)
                    )
                ''')
                
                # Таблица матчей
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS matches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tournament_id INTEGER NOT NULL,
                        match_date TEXT NOT NULL,
                        match_time TEXT NOT NULL,
                        team1 TEXT NOT NULL,
                        team2 TEXT NOT NULL,
                        is_active INTEGER DEFAULT 1,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (tournament_id) REFERENCES tournaments (id)
                    )
                ''')
                
                # Таблица участия пользователей в турнирах
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS tournament_participants (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        tournament_id INTEGER NOT NULL,
                        is_participating INTEGER DEFAULT 0,
                        joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, tournament_id),
                        FOREIGN KEY (user_id) REFERENCES users (user_id),
                        FOREIGN KEY (tournament_id) REFERENCES tournaments (id)
                    )
                ''')
                
                # Индексы для быстрого поиска
                await db.execute('CREATE INDEX IF NOT EXISTS idx_username ON users(username)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_email ON users(email)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_phone ON users(phone)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON users(user_id)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_is_banned ON users(is_banned)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_tournaments_active ON tournaments(is_active)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_matches_tournament ON matches(tournament_id)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_participants_user ON tournament_participants(user_id)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_participants_tournament ON tournament_participants(tournament_id)')
                
                await db.commit()
                logger.info("Таблицы и индексы успешно созданы")
                
        except Exception as e:
            logger.error(f"Ошибка при создании таблиц: {e}")
    
    async def create_admin_user(self, admin_id: int):
        """Создание администратора при первом запуске"""
        try:
            # Проверяем, существует ли уже администратор
            admin_user = await self.get_user_by_id(admin_id)
            if admin_user:
                logger.info(f"Администратор уже существует: {admin_user['username']}")
                return True
            
            # Создаем администратора
            salt = self._generate_salt()
            password_hash = self._hash_password("admin", salt)  # временный пароль
            
            async with aiosqlite.connect(self.db_name) as db:
                await db.execute('''
                    INSERT INTO users 
                    (user_id, username, password_hash, password_salt, email, phone, 
                     full_name, tg_username, tg_first_name, tg_last_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (admin_id, "admin", password_hash, salt, "admin@admin.com", 
                      "+79999999999", "Администратор", "admin", "Admin", "Admin"))
                
                await db.commit()
                logger.info("Администратор успешно создан")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка при создании администратора: {e}")
            return False
    
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
        
        # Проверяем, не забанен ли пользователь
        if user.get('is_banned'):
            return False
        
        password_hash = self._hash_password(password, user['password_salt'])
        return password_hash == user['password_hash']
    
    async def user_exists_by_tg_id(self, user_id: int) -> bool:
        """Проверка существования пользователя по Telegram ID"""
        user = await self.get_user_by_id(user_id)
        return user is not None
    
    async def is_user_banned(self, user_id: int) -> bool:
        """Проверка, забанен ли пользователь"""
        user = await self.get_user_by_id(user_id)
        return user and user.get('is_banned', False)
    
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
    
    async def ban_user(self, user_id: int) -> bool:
        """Забанить пользователя"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                await db.execute('''
                    UPDATE users SET is_banned = 1 WHERE user_id = ?
                ''', (user_id,))
                await db.commit()
                logger.info(f"Пользователь {user_id} забанен")
                return True
        except Exception as e:
            logger.error(f"Ошибка при бане пользователя {user_id}: {e}")
            return False
    
    async def unban_user(self, user_id: int) -> bool:
        """Разбанить пользователя"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                await db.execute('''
                    UPDATE users SET is_banned = 0 WHERE user_id = ?
                ''', (user_id,))
                await db.commit()
                logger.info(f"Пользователь {user_id} разбанен")
                return True
        except Exception as e:
            logger.error(f"Ошибка при разбане пользователя {user_id}: {e}")
            return False
    
    async def get_users_count(self) -> int:
        """Получение общего количества пользователей"""
        try:
            async with aiosqlite.connect(self.db_name) as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM users")
                result = await cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Ошибка при получении количества пользователей: {e}")
            return 0
    
    async def get_banned_users_count(self) -> int:
        """Получение количества забаненных пользователей"""
        try:
            async with aiosqlite.connect(self.db_name) as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
                result = await cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Ошибка при получении количества забаненных пользователей: {e}")
            return 0
    
    async def get_all_users(self):
        """Получение всех пользователей"""
        try:
            async with aiosqlite.connect(self.db_name) as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute('''
                    SELECT user_id, username, email, phone, full_name, 
                           registration_date, last_login, is_banned 
                    FROM users 
                    ORDER BY registration_date DESC
                ''')
                users = await cursor.fetchall()
                return [dict(user) for user in users]
        except Exception as e:
            logger.error(f"Ошибка при получении списка пользователей: {e}")
            return []
    
    async def get_today_registrations(self) -> int:
        """Получить количество регистраций за сегодня"""
        try:
            async with aiosqlite.connect(self.db_name) as conn:
                cursor = await conn.execute(
                    "SELECT COUNT(*) FROM users WHERE DATE(registration_date) = DATE('now')"
                )
                result = await cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Ошибка при получении регистраций за сегодня: {e}")
            return 0
    
    async def get_today_logins(self) -> int:
        """Получить количество входов за сегодня"""
        try:
            async with aiosqlite.connect(self.db_name) as conn:
                cursor = await conn.execute(
                    "SELECT COUNT(*) FROM users WHERE DATE(last_login) = DATE('now')"
                )
                result = await cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Ошибка при получении входов за сегодня: {e}")
            return 0

    # ========== МЕТОДЫ ДЛЯ ТУРНИРОВ ==========
    
    async def add_tournament(self, name: str, description: str, rules: str, created_by: int) -> bool:
        """Добавление нового турнира"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                await db.execute('''
                    INSERT INTO tournaments (name, description, rules, created_by)
                    VALUES (?, ?, ?, ?)
                ''', (name, description, rules, created_by))
                
                await db.commit()
                logger.info(f"Турнир '{name}' успешно добавлен")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка при добавлении турнира: {e}")
            return False
    
    async def get_all_tournaments(self) -> List[Dict[str, Any]]:
        """Получение всех активных турниров"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT t.*, u.username as created_by_username 
                    FROM tournaments t
                    LEFT JOIN users u ON t.created_by = u.user_id
                    WHERE t.is_active = 1
                    ORDER BY t.created_date DESC
                ''')
                tournaments = await cursor.fetchall()
                return [dict(tournament) for tournament in tournaments]
        except Exception as e:
            logger.error(f"Ошибка при получении турниров: {e}")
            return []
    
    async def get_tournament_by_id(self, tournament_id: int) -> Optional[Dict[str, Any]]:
        """Получение турнира по ID"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT t.*, u.username as created_by_username 
                    FROM tournaments t
                    LEFT JOIN users u ON t.created_by = u.user_id
                    WHERE t.id = ? AND t.is_active = 1
                ''', (tournament_id,))
                
                tournament = await cursor.fetchone()
                return dict(tournament) if tournament else None
        except Exception as e:
            logger.error(f"Ошибка при получении турнира: {e}")
            return None
    
    async def update_tournament(self, tournament_id: int, name: str, description: str, rules: str) -> bool:
        """Обновление турнира"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                await db.execute('''
                    UPDATE tournaments 
                    SET name = ?, description = ?, rules = ?
                    WHERE id = ?
                ''', (name, description, rules, tournament_id))
                
                await db.commit()
                logger.info(f"Турнир {tournament_id} успешно обновлен")
                return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении турнира: {e}")
            return False
    
    async def update_tournament_rules(self, tournament_id: int, rules: str) -> bool:
        """Обновление правил турнира"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                await db.execute('''
                    UPDATE tournaments SET rules = ? WHERE id = ?
                ''', (rules, tournament_id))
                
                await db.commit()
                logger.info(f"Правила турнира {tournament_id} обновлены")
                return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении правил турнира: {e}")
            return False
    
    async def delete_tournament(self, tournament_id: int) -> bool:
        """Удаление турнира (мягкое удаление)"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                await db.execute('''
                    UPDATE tournaments SET is_active = 0 WHERE id = ?
                ''', (tournament_id,))
                
                await db.commit()
                logger.info(f"Турнир {tournament_id} удален")
                return True
        except Exception as e:
            logger.error(f"Ошибка при удалении турнира: {e}")
            return False
    
    async def get_tournaments_count(self) -> int:
        """Получение количества активных турниров"""
        try:
            async with aiosqlite.connect(self.db_name) as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM tournaments WHERE is_active = 1")
                result = await cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Ошибка при получении количества турниров: {e}")
            return 0

    # ========== МЕТОДЫ ДЛЯ МАТЧЕЙ ==========
    
    async def add_match(self, tournament_id: int, match_date: str, match_time: str, team1: str, team2: str) -> bool:
        """Добавление нового матча"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                await db.execute('''
                    INSERT INTO matches (tournament_id, match_date, match_time, team1, team2)
                    VALUES (?, ?, ?, ?, ?)
                ''', (tournament_id, match_date, match_time, team1, team2))
                
                await db.commit()
                logger.info(f"Матч {team1} vs {team2} успешно добавлен")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка при добавлении матча: {e}")
            return False
    
    async def get_matches_by_tournament(self, tournament_id: int) -> List[Dict[str, Any]]:
        """Получение всех матчей турнира"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT * FROM matches 
                    WHERE tournament_id = ? AND is_active = 1
                    ORDER BY match_date, match_time
                ''', (tournament_id,))
                
                matches = await cursor.fetchall()
                return [dict(match) for match in matches]
        except Exception as e:
            logger.error(f"Ошибка при получении матчей: {e}")
            return []
    
    async def get_match_by_id(self, match_id: int) -> Optional[Dict[str, Any]]:
        """Получение матча по ID"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT * FROM matches WHERE id = ? AND is_active = 1
                ''', (match_id,))
                
                match = await cursor.fetchone()
                return dict(match) if match else None
        except Exception as e:
            logger.error(f"Ошибка при получении матча: {e}")
            return None
    
    async def delete_match(self, match_id: int) -> bool:
        """Удаление матча"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                await db.execute('''
                    UPDATE matches SET is_active = 0 WHERE id = ?
                ''', (match_id,))
                
                await db.commit()
                logger.info(f"Матч {match_id} удален")
                return True
        except Exception as e:
            logger.error(f"Ошибка при удалении матча: {e}")
            return False
    
    async def get_matches_count_by_tournament(self, tournament_id: int) -> int:
        """Получение количества матчей в турнире"""
        try:
            async with aiosqlite.connect(self.db_name) as conn:
                cursor = await conn.execute(
                    "SELECT COUNT(*) FROM matches WHERE tournament_id = ? AND is_active = 1", 
                    (tournament_id,)
                )
                result = await cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Ошибка при получении количества матчей: {e}")
            return 0

    # ========== МЕТОДЫ ДЛЯ УЧАСТИЯ В ТУРНИРАХ ==========
    
    async def add_tournament_participant(self, user_id: int, tournament_id: int, is_participating: bool) -> bool:
        """Добавление/обновление участия пользователя в турнире"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO tournament_participants 
                    (user_id, tournament_id, is_participating) 
                    VALUES (?, ?, ?)
                ''', (user_id, tournament_id, 1 if is_participating else 0))
                
                await db.commit()
                status = "участвует" if is_participating else "отказался"
                logger.info(f"Пользователь {user_id} {status} в турнире {tournament_id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка при добавлении участника турнира: {e}")
            return False
    
    async def get_tournament_participation(self, user_id: int, tournament_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации об участии пользователя в турнире"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT * FROM tournament_participants 
                    WHERE user_id = ? AND tournament_id = ?
                ''', (user_id, tournament_id))
                
                participation = await cursor.fetchone()
                return dict(participation) if participation else None
        except Exception as e:
            logger.error(f"Ошибка при получении участия в турнире: {e}")
            return None
    
    async def is_user_participating(self, user_id: int, tournament_id: int) -> bool:
        """Проверка, участвует ли пользователь в турнире"""
        participation = await self.get_tournament_participation(user_id, tournament_id)
        return participation and participation.get('is_participating', False)
    
    async def get_tournament_participants_count(self, tournament_id: int) -> int:
        """Получение количества участников турнира"""
        try:
            async with aiosqlite.connect(self.db_name) as conn:
                cursor = await conn.execute(
                    "SELECT COUNT(*) FROM tournament_participants WHERE tournament_id = ? AND is_participating = 1", 
                    (tournament_id,)
                )
                result = await cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Ошибка при получении количества участников: {e}")
            return 0

# Создаем экземпляр базы данных
db = Database()