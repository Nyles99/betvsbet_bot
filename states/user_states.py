from aiogram.dispatcher.filters.state import State, StatesGroup

class AuthStates(StatesGroup):
    """Состояния для аутентификации"""
    waiting_for_phone = State()
    waiting_for_username = State()
    waiting_for_password = State()
    waiting_for_full_name = State()

class ProfileStates(StatesGroup):
    """Состояния для редактирования профиля"""
    waiting_for_username = State()
    waiting_for_password = State()

class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    waiting_for_tournament_name = State()
    waiting_for_tournament_description = State()
    waiting_for_match_date = State()
    waiting_for_match_time = State()
    waiting_for_team1 = State()
    waiting_for_team2 = State()

class UserBetStates(StatesGroup):
    """Состояния для ставок пользователя"""
    waiting_for_score = State()