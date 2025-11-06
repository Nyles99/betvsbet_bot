import sqlite3
import logging
from typing import Optional, List, Tuple
from datetime import datetime

class DatabaseHandler:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._init_db()
    
    def _init_db(self):
        """Инициализация базы данных и таблиц"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._create_tables()
            logging.info(f"Database initialized successfully: {self.db_path}")
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
            raise
    
    def get_moscow_time(self):
        """Получение текущего времени в московском часовом поясе"""
        from datetime import datetime
        import pytz
        
        # Создаем временную зону для Москвы
        moscow_tz = pytz.timezone('Europe/Moscow')
        # Получаем текущее время в Москве
        moscow_time = datetime.now(moscow_tz)
        return moscow_time
    
    def _ensure_connection(self):
        """Убедиться, что соединение с базой активно"""
        if not self.conn:
            self._init_db()
        try:
            # Проверяем, что соединение действительно работает
            self.conn.execute("SELECT 1")
        except sqlite3.ProgrammingError:
            # Если соединение сломалось, пересоздаем его
            self._init_db()
    
    def _create_tables(self):
        """Создание таблиц если они не существуют"""
        with self.conn:
            # Таблица пользователей
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    phone_number TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE,
                    password TEXT NOT NULL,
                    full_name TEXT,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # Таблица турниров
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS tournaments (
                    tournament_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'active',
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER
                )
            ''')
            
            # Таблица матчей
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS matches (
                    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tournament_id INTEGER NOT NULL,
                    match_date TEXT NOT NULL,
                    match_time TEXT NOT NULL,
                    team1 TEXT NOT NULL,
                    team2 TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    result TEXT,
                    created_by INTEGER,
                    FOREIGN KEY (tournament_id) REFERENCES tournaments (tournament_id)
                )
            ''')
            
            # Таблица ставок пользователей
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS user_bets (
                    bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    match_id INTEGER NOT NULL,
                    predicted_score TEXT NOT NULL,
                    bet_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (match_id) REFERENCES matches (match_id),
                    UNIQUE(user_id, match_id)
                )
            ''')
    
    # ========== USER METHODS ==========
    
    def user_exists(self, user_id: int) -> bool:
        """Проверка существования пользователя"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
            return cursor.fetchone() is not None
    
    def is_phone_taken(self, phone: str) -> bool:
        """Проверка занятости номера телефона"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT 1 FROM users WHERE phone_number = ?', (phone,))
            return cursor.fetchone() is not None
    
    def is_username_taken(self, username: str) -> bool:
        """Проверка занятости логина"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT 1 FROM users WHERE username = ?', (username,))
            return cursor.fetchone() is not None
    
    def register_user(self, user_id: int, phone: str, username: str, password: str, full_name: str) -> bool:
        """Регистрация нового пользователя"""
        self._ensure_connection()
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO users (user_id, phone_number, username, password, full_name)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, phone, username, password, full_name))
                return True
        except Exception as e:
            logging.error(f"Error registering user: {e}")
            return False
    
    def get_user(self, user_id: int):
        """Получение информации о пользователе"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return type('User', (), {
                    'user_id': row[0],
                    'phone_number': row[1],
                    'username': row[2],
                    'password': row[3],
                    'full_name': row[4],
                    'registration_date': row[5],
                    'last_login': row[6]
                })()
            return None
    
    def get_user_by_username(self, username: str):
        """Получение пользователя по логину"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            if row:
                return type('User', (), {
                    'user_id': row[0],
                    'phone_number': row[1],
                    'username': row[2],
                    'password': row[3],
                    'full_name': row[4],
                    'registration_date': row[5],
                    'last_login': row[6]
                })()
            return None
    
    def verify_password(self, user_id: int, hashed_password: str) -> bool:
        """Проверка пароля"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT password FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return row and row[0] == hashed_password
    
    def update_profile(self, user_id: int, username: str = None, full_name: str = None) -> bool:
        """Обновление профиля пользователя"""
        self._ensure_connection()
        try:
            with self.conn:
                cursor = self.conn.cursor()
                if username and full_name:
                    cursor.execute('''
                        UPDATE users SET username = ?, full_name = ? WHERE user_id = ?
                    ''', (username, full_name, user_id))
                elif username:
                    cursor.execute('UPDATE users SET username = ? WHERE user_id = ?', (username, user_id))
                elif full_name:
                    cursor.execute('UPDATE users SET full_name = ? WHERE user_id = ?', (full_name, user_id))
                return True
        except Exception as e:
            logging.error(f"Error updating profile: {e}")
            return False
    
    def update_user_password(self, user_id: int, hashed_password: str) -> bool:
        """Обновление пароля пользователя"""
        self._ensure_connection()
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('UPDATE users SET password = ? WHERE user_id = ?', (hashed_password, user_id))
                return True
        except Exception as e:
            logging.error(f"Error updating password: {e}")
            return False
    
    def update_last_login(self, user_id: int) -> bool:
        """Обновление времени последнего входа"""
        self._ensure_connection()
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?', (user_id,))
                return True
        except Exception as e:
            logging.error(f"Error updating last login: {e}")
            return False
    
    def get_all_users(self):
        """Получение всех пользователей"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM users ORDER BY registration_date DESC')
            rows = cursor.fetchall()
            users = []
            for row in rows:
                users.append(type('User', (), {
                    'user_id': row[0],
                    'phone_number': row[1],
                    'username': row[2],
                    'password': row[3],
                    'full_name': row[4],
                    'registration_date': row[5],
                    'last_login': row[6]
                })())
            return users
    
    def get_users_count(self) -> int:
        """Получение количества пользователей"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            return cursor.fetchone()[0]
    
    # ========== TOURNAMENT METHODS ==========
    
    def get_all_tournaments(self):
        """Получение всех активных турниров"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM tournaments WHERE status = "active" ORDER BY created_date DESC')
            return cursor.fetchall()
    
    def get_all_tournaments_admin(self):
        """Получение всех турниров для админки"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM tournaments ORDER BY created_date DESC')
            return cursor.fetchall()
    
    def get_tournament(self, tournament_id: int):
        """Получение информации о турнире"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM tournaments WHERE tournament_id = ?', (tournament_id,))
            return cursor.fetchone()
    
    def add_tournament(self, name: str, description: str, created_by: int) -> bool:
        """Добавление нового турнира"""
        self._ensure_connection()
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO tournaments (name, description, created_by)
                    VALUES (?, ?, ?)
                ''', (name, description, created_by))
                return True
        except Exception as e:
            logging.error(f"Error adding tournament: {e}")
            return False
    
    def update_tournament_status(self, tournament_id: int, status: str) -> bool:
        """Обновление статуса турнира"""
        self._ensure_connection()
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('UPDATE tournaments SET status = ? WHERE tournament_id = ?', (status, tournament_id))
                return True
        except Exception as e:
            logging.error(f"Error updating tournament status: {e}")
            return False
    
    def delete_tournament(self, tournament_id: int) -> bool:
        """Удаление турнира"""
        self._ensure_connection()
        try:
            with self.conn:
                cursor = self.conn.cursor()
                # Сначала удаляем ставки связанные с матчами этого турнира
                cursor.execute('''
                    DELETE FROM user_bets 
                    WHERE match_id IN (SELECT match_id FROM matches WHERE tournament_id = ?)
                ''', (tournament_id,))
                # Затем удаляем матчи
                cursor.execute('DELETE FROM matches WHERE tournament_id = ?', (tournament_id,))
                # И наконец удаляем турнир
                cursor.execute('DELETE FROM tournaments WHERE tournament_id = ?', (tournament_id,))
                return True
        except Exception as e:
            logging.error(f"Error deleting tournament: {e}")
            return False
    
    def get_user_tournaments_with_bets(self, user_id: int):
        """Получение турниров, в которых пользователь сделал ставки"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT DISTINCT t.* 
                FROM tournaments t
                JOIN matches m ON t.tournament_id = m.tournament_id
                JOIN user_bets b ON m.match_id = b.match_id
                WHERE b.user_id = ? AND t.status = 'active'
                ORDER BY t.created_date DESC
            ''', (user_id,))
            return cursor.fetchall()
    
    def get_tournament_participants(self, tournament_id: int):
        """Получение участников турнира"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT DISTINCT u.* 
                FROM users u
                JOIN user_bets b ON u.user_id = b.user_id
                JOIN matches m ON b.match_id = m.match_id
                WHERE m.tournament_id = ?
                ORDER BY u.registration_date DESC
            ''', (tournament_id,))
            rows = cursor.fetchall()
            users = []
            for row in rows:
                users.append(type('User', (), {
                    'user_id': row[0],
                    'phone_number': row[1],
                    'username': row[2],
                    'password': row[3],
                    'full_name': row[4],
                    'registration_date': row[5],
                    'last_login': row[6]
                })())
            return users
    
    # ========== MATCH METHODS ==========
    
    def get_tournament_matches(self, tournament_id: int):
        """Получение матчей турнира"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM matches 
                WHERE tournament_id = ? 
                ORDER BY match_date, match_time
            ''', (tournament_id,))
            return cursor.fetchall()
    
    def get_match(self, match_id: int):
        """Получение информации о матче"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM matches WHERE match_id = ?', (match_id,))
            return cursor.fetchone()
    
    def get_match_with_bets(self, match_id: int):
        """Получение информации о матче с количеством ставок"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT m.*, COUNT(b.bet_id) as bets_count
                FROM matches m
                LEFT JOIN user_bets b ON m.match_id = b.match_id
                WHERE m.match_id = ?
                GROUP BY m.match_id
            ''', (match_id,))
            return cursor.fetchone()
    
    def add_match(self, tournament_id: int, match_date: str, match_time: str, team1: str, team2: str, created_by: int) -> bool:
        """Добавление матча в турнир"""
        self._ensure_connection()
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO matches (tournament_id, match_date, match_time, team1, team2, created_by, result)
                    VALUES (?, ?, ?, ?, ?, ?, NULL)
                ''', (tournament_id, match_date, match_time, team1, team2, created_by))
                return True
        except Exception as e:
            logging.error(f"Error adding match: {e}")
            return False
    
    def update_match_result(self, match_id: int, result: str) -> bool:
        """Обновление результата матча"""
        self._ensure_connection()
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('UPDATE matches SET result = ? WHERE match_id = ?', (result, match_id))
                return True
        except Exception as e:
            logging.error(f"Error updating match result: {e}")
            return False
    
    def delete_match(self, match_id: int) -> bool:
        """Удаление матча"""
        self._ensure_connection()
        try:
            with self.conn:
                cursor = self.conn.cursor()
                # Сначала удаляем ставки на этот матч
                cursor.execute('DELETE FROM user_bets WHERE match_id = ?', (match_id,))
                # Затем удаляем матч
                cursor.execute('DELETE FROM matches WHERE match_id = ?', (match_id,))
                return True
        except Exception as e:
            logging.error(f"Error deleting match: {e}")
            return False
    
    def is_match_expired(self, match_date: str, match_time: str) -> bool:
        """Проверка, истекло ли время матча"""
        try:
            from datetime import datetime
            import pytz
            
            # Создаем datetime объект из даты и времени матча
            match_datetime_str = f"{match_date} {match_time}"
            match_datetime_naive = datetime.strptime(match_datetime_str, "%d.%m.%Y %H:%M")
            
            # Предполагаем, что время матча указано в московском часовом поясе
            moscow_tz = pytz.timezone('Europe/Moscow')
            match_datetime = moscow_tz.localize(match_datetime_naive)
            
            # Получаем текущее время в Москве
            current_time = self.get_moscow_time()
            
            return current_time > match_datetime
        except Exception as e:
            logging.error(f"Error checking match expiration: {e}")
            return False  # В случае ошибки считаем матч активным
    
    def get_expired_matches(self):
        """Получение списка истекших матчей без результатов"""
        self._ensure_connection()
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('''
                    SELECT m.*, t.name as tournament_name
                    FROM matches m
                    JOIN tournaments t ON m.tournament_id = t.tournament_id
                    WHERE m.result IS NULL 
                    AND datetime(m.match_date || ' ' || m.match_time, '+3 hours') <= datetime('now')
                    AND m.status = 'active'
                ''')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting expired matches: {e}")
            return []
    
    def get_available_tournament_matches(self, tournament_id: int, user_id: int):
        """Получение доступных для ставок матчей турнира"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT m.* 
                FROM matches m
                WHERE m.tournament_id = ? 
                AND m.status = 'active'
                AND NOT EXISTS (
                    SELECT 1 FROM user_bets b 
                    WHERE b.match_id = m.match_id AND b.user_id = ?
                )
                ORDER BY m.match_date, m.match_time
            ''', (tournament_id, user_id))
            
            # Фильтруем матчи с помощью нашей функции
            all_matches = cursor.fetchall()
            available_matches = []
            
            for match in all_matches:
                if not self.is_match_expired(match[2], match[3]):  # match_date, match_time
                    available_matches.append(match)
            
            return available_matches
    
    # ========== BET METHODS ==========
    
    def add_user_bet(self, user_id: int, match_id: int, predicted_score: str) -> bool:
        """Добавление ставки пользователя"""
        self._ensure_connection()
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO user_bets (user_id, match_id, predicted_score)
                    VALUES (?, ?, ?)
                ''', (user_id, match_id, predicted_score))
                return True
        except Exception as e:
            logging.error(f"Error adding user bet: {e}")
            return False
    
    def get_user_bet(self, user_id: int, match_id: int):
        """Получение ставки пользователя на матч"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM user_bets 
                WHERE user_id = ? AND match_id = ?
            ''', (user_id, match_id))
            return cursor.fetchone()
    
    def get_user_bets_with_match_info(self, user_id: int):
        """Получить ставки пользователя с информацией о матчах"""
        self._ensure_connection()
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
                    m.result as match_result,
                    t.name as tournament_name
                FROM user_bets b
                JOIN matches m ON b.match_id = m.match_id
                JOIN tournaments t ON m.tournament_id = t.tournament_id
                WHERE b.user_id = ?
                ORDER BY m.match_date DESC, m.match_time DESC
            ''', (user_id,))
            return cursor.fetchall()
    
    def get_tournament_bets_by_user(self, user_id: int, tournament_id: int) -> list:
        """Получить ставки пользователя в конкретном турнире с актуальными результатами матчей"""
        self._ensure_connection()
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT 
                    b.bet_id,
                    b.user_id,
                    b.match_id,
                    b.predicted_score,
                    b.bet_date,
                    m.match_date,
                    m.match_time,
                    m.team1,
                    m.team2,
                    m.result as match_result,
                    t.name as tournament_name
                FROM user_bets b
                JOIN matches m ON b.match_id = m.match_id
                JOIN tournaments t ON m.tournament_id = t.tournament_id
                WHERE b.user_id = ? AND m.tournament_id = ?
                ORDER BY m.match_date DESC, m.match_time DESC
            ''', (user_id, tournament_id))
            
            bets = cursor.fetchall()
            return bets
        except Exception as e:
            logging.error(f"Error in get_tournament_bets_by_user: {e}")
            return []
    
    def get_match_bets(self, match_id: int):
        """Получение всех ставок на матч"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT b.*, u.username, u.full_name 
                FROM user_bets b
                JOIN users u ON b.user_id = u.user_id
                WHERE b.match_id = ?
            ''', (match_id,))
            return cursor.fetchall()
    
    def get_match_bets_count(self, match_id: int) -> int:
        """Получение количества ставок на матч"""
        self._ensure_connection()
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM user_bets WHERE match_id = ?', (match_id,))
            return cursor.fetchone()[0]
    
    def close(self):
        """Закрытие соединения с базой данных"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_tournament_leaderboard(self, tournament_id: int, limit: int = None, offset: int = 0):
        """Получение рейтинга игроков турнира"""
        self._ensure_connection()
        try:
            cursor = self.conn.cursor()
            
            # Сначала получаем всех игроков с их ставками и результатами
            cursor.execute('''
                SELECT 
                    u.user_id,
                    u.username,
                    b.bet_id,
                    b.predicted_score,
                    m.result
                FROM users u
                JOIN user_bets b ON u.user_id = b.user_id
                JOIN matches m ON b.match_id = m.match_id
                WHERE m.tournament_id = ? AND m.result IS NOT NULL AND m.result != 'None'
            ''', (tournament_id,))
            
            # Группируем по игрокам и рассчитываем очки в Python
            player_stats = {}
            
            for row in cursor.fetchall():
                user_id = row[0]
                username = row[1] or f"ID{row[0]}"
                predicted_score = row[3]
                actual_score = row[4]
                
                if user_id not in player_stats:
                    player_stats[user_id] = {
                        'username': username,
                        'matches_played': 0,
                        'exact_scores': 0,
                        'total_points': 0
                    }
                
                player_stats[user_id]['matches_played'] += 1
                
                # Рассчитываем очки с помощью нашей функции
                from utils.scoring_system import calculate_points
                points = calculate_points(predicted_score, actual_score)
                player_stats[user_id]['total_points'] += points
                
                if points == 4:  # Точный счет
                    player_stats[user_id]['exact_scores'] += 1
            
            # Преобразуем в список и сортируем
            leaderboard = []
            for user_id, stats in player_stats.items():
                leaderboard.append({
                    'user_id': user_id,
                    'username': stats['username'],
                    'matches_played': stats['matches_played'],
                    'exact_scores': stats['exact_scores'],
                    'total_points': stats['total_points']
                })
            
            # Сортируем по очкам (по убыванию)
            leaderboard.sort(key=lambda x: x['total_points'], reverse=True)
            
            # Применяем пагинацию
            if limit:
                return leaderboard[offset:offset + limit]
            return leaderboard
            
        except Exception as e:
            logging.error(f"Error getting tournament leaderboard: {e}")
            return []
    
    def get_user_completed_bets(self, user_id: int, tournament_id: int):
        """Получение завершенных ставок пользователя в турнире (только матчи с результатами или истекшие)"""
        self._ensure_connection()
        try:
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
                    m.result as match_result,
                    t.name as tournament_name
                FROM user_bets b
                JOIN matches m ON b.match_id = m.match_id
                JOIN tournaments t ON m.tournament_id = t.tournament_id
                WHERE b.user_id = ? AND m.tournament_id = ?
                AND (m.result IS NOT NULL AND m.result != 'None' OR 
                    datetime(m.match_date || ' ' || m.match_time, '+3 hours') <= datetime('now'))
                ORDER BY m.match_date DESC, m.match_time DESC
            ''', (user_id, tournament_id))
            
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting user completed bets: {e}")
            return []