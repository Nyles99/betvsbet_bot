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