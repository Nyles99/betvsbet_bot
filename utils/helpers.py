from database.db_handler import DatabaseHandler
from aiogram.utils.exceptions import MessageNotModified

async def get_available_matches(user_id, tournament_id=None):
    """Получение доступных матчей для пользователя"""
    db = DatabaseHandler('users.db')
    if tournament_id:
        all_matches = db.get_tournament_matches(tournament_id)
    else:
        all_matches = db.get_available_matches_for_user(user_id)
    
    available_matches = []
    for match in all_matches:
        user_bet = db.get_user_bet(user_id, match[0])
        if not user_bet:
            available_matches.append(match)
    
    return available_matches

async def safe_edit_message(callback, text, reply_markup=None, parse_mode='Markdown'):
    """Безопасное редактирование сообщения"""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except MessageNotModified:
        pass