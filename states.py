from aiogram.dispatcher.filters.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    """Состояния для процесса регистрации"""
    waiting_for_username = State()
    waiting_for_full_name = State()
    waiting_for_email = State()
    waiting_for_phone = State()

class LoginStates(StatesGroup):
    """Состояния для процесса входа"""
    waiting_for_login = State()
    waiting_for_password = State()

class ProfileStates(StatesGroup):
    """Состояния для редактирования профиля"""
    editing_username = State()
    editing_email = State()
    editing_phone = State()
    editing_full_name = State()
    
class RegistrationStates(StatesGroup):
    """Состояния для процесса регистрации"""
    waiting_for_username = State()
    waiting_for_full_name = State()
    waiting_for_email = State()
    waiting_for_phone = State()

class LoginStates(StatesGroup):
    """Состояния для процесса входа"""
    waiting_for_login = State()
    waiting_for_password = State()

class ProfileStates(StatesGroup):
    """Состояния для редактирования профиля"""
    editing_username = State()
    editing_email = State()
    editing_phone = State()
    editing_full_name = State()

class MatchStates(StatesGroup):
    """Состояния для добавления матчей"""
    waiting_for_tournament_select = State()
    waiting_for_match_date = State()
    waiting_for_match_time = State()
    waiting_for_team1 = State()
    waiting_for_team2 = State()

class TournamentStates(StatesGroup):
    """Состояния для управления турнирами"""
    waiting_for_tournament_name = State()
    waiting_for_tournament_description = State()
    waiting_for_tournament_rules = State()
    waiting_for_tournament_edit_name = State()
    waiting_for_tournament_edit_description = State()
    waiting_for_tournament_edit_rules = State()