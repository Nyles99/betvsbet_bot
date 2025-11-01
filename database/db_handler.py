import sqlite3
import logging
from typing import Optional, List
from datetime import datetime
import pytz
from database.models import User

class DatabaseHandler:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.init_database()
    
    def get_moscow_time(self):
        """Получение текущего московского времени"""
        moscow_tz = pytz.timezone('Europe/Moscow')
        return datetime.now(moscow_tz)

    def is_match_expired(self, match_date: str, match_time: str) -> bool:
        """Проверка, истекло ли время матча"""
        try:
            moscow_tz = pytz.timezone('Europe/Moscow')
            current_time = self.get_moscow_time()
            
            # Парсим дату и время матча
            match_datetime_str = f"{match_date} {match_time}"
            match_datetime = datetime.strptime(match_datetime_str, '%d.%m.%Y %H:%M')
            match_datetime = moscow_tz.localize(match_datetime)
            
            # Сравниваем с текущим временем
            return current_time >= match_datetime
        except Exception as e:
            logging.error(f"Error checking match expiration: {e}")
            return False
    
    def get_available_tournament_matches(self, tournament_id: int, user_id: int):
        """Получение доступных матчей турнира (не истекших и без ставок пользователя)"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT m.* 
                FROM matches m
                WHERE m.tournament_id = ? 
                AND m.id NOT IN (
                    SELECT match_id FROM user_bets WHERE user_id = ?
                )
                ORDER BY m.match_date, m.match_time
            ''', (tournament_id, user_id))
            all_matches = cursor.fetchall()
            
            # Фильтруем матчи по времени
            available_matches = []
            for match in all_matches:
                if not self.is_match_expired(match[2], match[3]):
                    available_matches.append(match)
            
            return available_matches
    
    def get_expired_matches(self):
        """Получение всех истекших матчей"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM matches')
            all_matches = cursor.fetchall()
            
            expired_matches = []
            for match in all_matches:
                if self.is_match_expired(match[2], match[3]):
                    expired_matches.append(match)
            
            return expired_matches
    
    def update_match_status(self, match_id: int, status: str) -> bool:
        """Обновление статуса матча"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE matches SET status = ? WHERE id = ?
                ''', (status, match_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error updating match status: {e}")
            return False
    
    def update_match_result(self, match_id: int, result: str) -> bool:
        """Обновление результата матча"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE matches SET result = ?, status = 'completed' WHERE id = ?
                ''', (result, match_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error updating match result: {e}")
            return False

    def get_match_with_bets(self, match_id: int):
        """Получение информации о матче со ставками пользователей"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT m.*, COUNT(ub.id) as bets_count
                FROM matches m
                LEFT JOIN user_bets ub ON m.id = ub.match_id
                WHERE m.id = ?
                GROUP BY m.id
            ''', (match_id,))
            result = cursor.fetchone()
            return result

    def get_match_bets_count(self, match_id: int) -> int:
        """Получение количества ставок на матч"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM user_bets WHERE match_id = ?
            ''', (match_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def get_user_bets_with_match_info(self, user_id: int) -> list:
        """Получить ставки пользователя с информацией о матчах"""
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT 
                    b.bet_id,
                    b.match_id,
                    b.predicted_score,
                    b.bet_date,
                    m.match_date,
                    m.match_time,
                    m.team1,
                    m.team2,
                    m.result as match_result,  -- Берем результат из таблицы matches
                    t.name as tournament_name
                FROM user_bets b
                JOIN matches m ON b.match_id = m.match_id
                JOIN tournaments t ON m.tournament_id = t.tournament_id
                WHERE b.user_id = ?
                ORDER BY m.match_date DESC, m.match_time DESC
            ''', (user_id,))
            
            bets = cursor.fetchall()
            return bets
        
    def init_database(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    phone_number TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE,
                    full_name TEXT,
                    password_hash TEXT NOT NULL,
                    registration_date TEXT,
                    last_login TEXT
                )
            ''')
            
            # Таблица турниров
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tournaments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'active',
                    created_date TEXT,
                    created_by INTEGER
                )
            ''')
            
            # Таблица матчей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tournament_id INTEGER NOT NULL,
                    match_date TEXT NOT NULL,
                    match_time TEXT NOT NULL,
                    team1 TEXT NOT NULL,
                    team2 TEXT NOT NULL,
                    status TEXT DEFAULT 'scheduled',
                    result TEXT,
                    created_date TEXT,
                    created_by INTEGER,
                    FOREIGN KEY (tournament_id) REFERENCES tournaments (id)
                )
            ''')
            
            # Таблица ставок пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_bets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    match_id INTEGER NOT NULL,
                    score TEXT NOT NULL,
                    bet_date TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (match_id) REFERENCES matches (id),
                    UNIQUE(user_id, match_id)
                )
            ''')
            conn.commit()
    
    def is_phone_taken(self, phone_number: str) -> bool:
        """Проверка, занят ли номер телефона"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users WHERE phone_number = ?', (phone_number,))
            return cursor.fetchone() is not None
    
    def is_username_taken(self, username: str) -> bool:
        """Проверка, занят ли логин"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
            return cursor.fetchone() is not None
    
    def register_user(self, user_id: int, phone_number: str, username: str, password_hash: str, full_name: str = None) -> bool:
        """Регистрация нового пользователя с логином, паролем и ФИО"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Проверяем, не заняты ли номер или логин
                cursor.execute('SELECT user_id FROM users WHERE phone_number = ? OR username = ?', (phone_number, username))
                existing_user = cursor.fetchone()
                if existing_user:
                    return False
                
                cursor.execute('''
                    INSERT INTO users (user_id, phone_number, username, full_name, password_hash, registration_date, last_login)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, phone_number, username, full_name, password_hash, self.get_moscow_time(), self.get_moscow_time()))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row:
                return User(
                    user_id=row[0],
                    phone_number=row[1],
                    username=row[2],
                    full_name=row[3],
                    registration_date=row[5],
                    last_login=row[6]
                )
            return None
    
    def get_user_by_username(self, username: str):
        """Получение пользователя по логину"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            
            if row:
                return User(
                    user_id=row[0],
                    phone_number=row[1],
                    username=row[2],
                    full_name=row[3],
                    registration_date=row[5],
                    last_login=row[6]
                )
            return None
    
    def verify_password(self, user_id: int, password_hash: str) -> bool:
        """Проверка пароля пользователя"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT password_hash FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row and row[0] == password_hash:
                return True
            return False
    
    def update_last_login(self, user_id: int):
        """Обновление времени последнего входа"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE user_id = ?
            ''', (self.get_moscow_time(), user_id))
            conn.commit()
    
    def update_profile(self, user_id: int, username: str = None, full_name: str = None) -> bool:
        """Обновление профиля пользователя"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                if username and full_name:
                    cursor.execute('''
                        UPDATE users SET username = ?, full_name = ?, last_login = ?
                        WHERE user_id = ?
                    ''', (username, full_name, self.get_moscow_time(), user_id))
                elif username:
                    cursor.execute('''
                        UPDATE users SET username = ?, last_login = ?
                        WHERE user_id = ?
                    ''', (username, self.get_moscow_time(), user_id))
                elif full_name:
                    cursor.execute('''
                        UPDATE users SET full_name = ?, last_login = ?
                        WHERE user_id = ?
                    ''', (full_name, self.get_moscow_time(), user_id))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error updating profile: {e}")
            return False
    
    def update_user_password(self, user_id: int, new_password_hash: str) -> bool:
        """Обновление пароля пользователя"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET password_hash = ?, last_login = ?
                    WHERE user_id = ?
                ''', (new_password_hash, self.get_moscow_time(), user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error updating password: {e}")
            return False
    
    def user_exists(self, user_id: int) -> bool:
        """Проверка существования пользователя"""
        return self.get_user(user_id) is not None
    
    def get_all_users(self) -> List[User]:
        """Получение всех пользователей (для админа)"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users ORDER BY registration_date DESC')
            rows = cursor.fetchall()
            
            users = []
            for row in rows:
                users.append(User(
                    user_id=row[0],
                    phone_number=row[1],
                    username=row[2],
                    full_name=row[3],
                    registration_date=row[5],
                    last_login=row[6]
                ))
            return users
    
    def get_users_count(self) -> int:
        """Получение количества пользователей"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            return cursor.fetchone()[0]
    
    # Методы для турниров
    def add_tournament(self, name: str, description: str, created_by: int) -> bool:
        """Добавление нового турнира"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tournaments (name, description, created_date, created_by)
                    VALUES (?, ?, ?, ?)
                ''', (name, description, self.get_moscow_time(), created_by))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding tournament: {e}")
            return False
    
    def get_all_tournaments(self):
        """Получение всех активных турниров"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tournaments WHERE status = "active" ORDER BY created_date DESC')
            return cursor.fetchall()
    
    def get_all_tournaments_admin(self):
        """Получение всех турниров (включая неактивные) для админа"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tournaments ORDER BY created_date DESC')
            return cursor.fetchall()
    
    def get_tournament(self, tournament_id: int):
        """Получение турнира по ID"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tournaments WHERE id = ?', (tournament_id,))
            return cursor.fetchone()
    
    def update_tournament_status(self, tournament_id: int, status: str) -> bool:
        """Обновление статуса турнира"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tournaments SET status = ? WHERE id = ?
                ''', (status, tournament_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error updating tournament status: {e}")
            return False
    
    def delete_tournament(self, tournament_id: int) -> bool:
        """Удаление турнира"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                # Сначала удаляем все матчи турнира
                cursor.execute('DELETE FROM matches WHERE tournament_id = ?', (tournament_id,))
                # Затем удаляем сам турнир
                cursor.execute('DELETE FROM tournaments WHERE id = ?', (tournament_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error deleting tournament: {e}")
            return False
    
    # Методы для матчей
    def add_match(self, tournament_id: int, match_date: str, match_time: str, team1: str, team2: str, created_by: int) -> bool:
        """Добавление матча в турнир"""
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO matches (tournament_id, match_date, match_time, team1, team2, created_by, result)
                    VALUES (?, ?, ?, ?, ?, ?, NULL)  -- Явно устанавливаем result в NULL
                ''', (tournament_id, match_date, match_time, team1, team2, created_by))
                return True
        except Exception as e:
            logging.error(f"Error adding match: {e}")
            return False
    
    def get_tournament_matches(self, tournament_id: int):
        """Получение всех матчей турнира"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM matches 
                WHERE tournament_id = ? 
                ORDER BY match_date, match_time
            ''', (tournament_id,))
            return cursor.fetchall()
    
    def get_match(self, match_id: int):
        """Получение матча по ID"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM matches WHERE id = ?', (match_id,))
            return cursor.fetchone()
    
    def delete_match(self, match_id: int) -> bool:
        """Удаление матча"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM matches WHERE id = ?', (match_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error deleting match: {e}")
            return False
    
    def update_match(self, match_id: int, match_date: str = None, match_time: str = None, team1: str = None, team2: str = None) -> bool:
        """Обновление информации о матче"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                updates = []
                params = []
                
                if match_date:
                    updates.append("match_date = ?")
                    params.append(match_date)
                if match_time:
                    updates.append("match_time = ?")
                    params.append(match_time)
                if team1:
                    updates.append("team1 = ?")
                    params.append(team1)
                if team2:
                    updates.append("team2 = ?")
                    params.append(team2)
                
                if updates:
                    params.append(match_id)
                    cursor.execute(f'''
                        UPDATE matches SET {", ".join(updates)} WHERE id = ?
                    ''', params)
                    conn.commit()
                    return cursor.rowcount > 0
                return False
                
        except Exception as e:
            logging.error(f"Error updating match: {e}")
            return False

    # Методы для ставок
    def add_user_bet(self, user_id: int, match_id: int, score: str) -> bool:
        """Добавление ставки пользователя"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_bets (user_id, match_id, score, bet_date)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, match_id, score, self.get_moscow_time()))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # Обновляем ставку если она уже существует
            return self.update_user_bet(user_id, match_id, score)
        except Exception as e:
            logging.error(f"Error adding user bet: {e}")
            return False
    
    def update_user_bet(self, user_id: int, match_id: int, score: str) -> bool:
        """Обновление ставки пользователя"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_bets SET score = ?, bet_date = ?
                    WHERE user_id = ? AND match_id = ?
                ''', (score, self.get_moscow_time(), user_id, match_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error updating user bet: {e}")
            return False
    
    def get_user_bet(self, user_id: int, match_id: int):
        """Получение ставки пользователя на матч"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM user_bets WHERE user_id = ? AND match_id = ?
            ''', (user_id, match_id))
            return cursor.fetchone()
    
    def get_user_bets(self, user_id: int):
        """Получение всех ставок пользователя"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ub.*, m.match_date, m.match_time, m.team1, m.team2, t.name as tournament_name
                FROM user_bets ub
                JOIN matches m ON ub.match_id = m.id
                JOIN tournaments t ON m.tournament_id = t.id
                WHERE ub.user_id = ?
                ORDER BY m.match_date, m.match_time
            ''', (user_id,))
            return cursor.fetchall()
    
    def get_available_matches_for_user(self, user_id: int):
        """Получение матчей, на которые пользователь еще не делал ставку"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT m.*, t.name as tournament_name
                FROM matches m
                JOIN tournaments t ON m.tournament_id = t.id
                WHERE m.status = 'scheduled' 
                AND m.id NOT IN (
                    SELECT match_id FROM user_bets WHERE user_id = ?
                )
                ORDER BY m.match_date, m.match_time
            ''', (user_id,))
            return cursor.fetchall()
    
    def get_user_tournaments_with_bets(self, user_id: int):
        """Получение турниров, в которых пользователь делал ставки"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT t.*
                FROM tournaments t
                JOIN matches m ON t.id = m.tournament_id
                JOIN user_bets ub ON m.id = ub.match_id
                WHERE ub.user_id = ?
                ORDER BY t.name
            ''', (user_id,))
            return cursor.fetchall()
    
    def get_tournament_bets_by_user(self, user_id: int, tournament_id: int):
        """Получение ставок пользователя в конкретном турнире"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ub.*, m.match_date, m.match_time, m.team1, m.team2
                FROM user_bets ub
                JOIN matches m ON ub.match_id = m.id
                WHERE ub.user_id = ? AND m.tournament_id = ?
                ORDER BY m.match_date, m.match_time
            ''', (user_id, tournament_id))
            return cursor.fetchall()
    
    def get_user_bets_count(self, user_id: int) -> int:
        """Получение количества ставок пользователя"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM user_bets WHERE user_id = ?', (user_id,))
            return cursor.fetchone()[0]
    
    def get_tournament_participants(self, tournament_id: int):
        """Получение всех участников турнира"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT u.*
                FROM users u
                JOIN user_bets ub ON u.user_id = ub.user_id
                JOIN matches m ON ub.match_id = m.id
                WHERE m.tournament_id = ?
                ORDER BY u.registration_date
            ''', (tournament_id,))
            rows = cursor.fetchall()
            
            users = []
            for row in rows:
                users.append(User(
                    user_id=row[0],
                    phone_number=row[1],
                    username=row[2],
                    full_name=row[3],
                    registration_date=row[5],
                    last_login=row[6]
                ))
            return users
