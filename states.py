from aiogram.dispatcher.filters.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    """Состояния для процесса регистрации"""
    waiting_for_username = State()      # Шаг 1: Ввод логина
    waiting_for_password = State()      # Шаг 2: Ввод пароля
    waiting_for_full_name = State()     # Шаг 3: Ввод ФИО
    waiting_for_email = State()         # Шаг 4: Ввод email
    waiting_for_phone = State()         # Шаг 5: Ввод телефона

class LoginStates(StatesGroup):
    """Состояния для процесса входа"""
    waiting_for_login = State()         # Ввод логина/email/телефона
    waiting_for_password = State()      # Ввод пароля

class ProfileStates(StatesGroup):
    """Состояния для редактирования профиля"""
    editing_username = State()          # Редактирование логина
    editing_email = State()             # Редактирование email
    editing_phone = State()             # Редактирование телефона
    editing_full_name = State()         # Редактирование ФИО

class MatchStates(StatesGroup):
    """Состояния для добавления матчей"""
    waiting_for_tournament_select = State()  # Выбор турнира для матча
    waiting_for_match_date = State()         # Ввод даты матча
    waiting_for_match_time = State()         # Ввод времени матча
    waiting_for_team1 = State()              # Ввод первой команды
    waiting_for_team2 = State()              # Ввод второй команды

class TournamentStates(StatesGroup):
    """Состояния для управления турнирами"""
    waiting_for_tournament_name = State()           # Ввод названия турнира
    waiting_for_tournament_description = State()    # Ввод описания турнира
    waiting_for_tournament_rules = State()          # Ввод правил турнира
    waiting_for_tournament_edit_name = State()      # Редактирование названия
    waiting_for_tournament_edit_description = State()  # Редактирование описания
    waiting_for_tournament_edit_rules = State()     # Редактирование правил

class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    waiting_for_user_search = State()   # Поиск пользователя
    waiting_for_ban_user = State()      # Бан пользователя
    waiting_for_unban_user = State()    # Разбан пользователя