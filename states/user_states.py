from aiogram.dispatcher.filters.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_username = State()
    waiting_for_password = State()

class LoginStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_password = State()

class ProfileStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_full_name = State()

class AdminStates(StatesGroup):
    waiting_for_tournament_name = State()
    waiting_for_tournament_description = State()
    waiting_for_match_date = State()
    waiting_for_match_time = State()
    waiting_for_team1 = State()
    waiting_for_team2 = State()

class UserBetStates(StatesGroup):
    waiting_for_score = State()