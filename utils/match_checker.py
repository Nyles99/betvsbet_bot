import asyncio
import logging
from database.db_handler import DatabaseHandler

async def check_expired_matches():
    """Проверка истекших матчей и обновление их статуса"""
    try:
        db = DatabaseHandler('users.db')
        expired_matches = db.get_expired_matches()
        
        for match in expired_matches:
            # Обновляем статус матча на 'completed'
            if db.update_match_status(match[0], 'completed'):
                logging.info(f"Матч {match[0]} ({match[4]} vs {match[5]}) отмечен как завершенный")
        
        if expired_matches:
            logging.info(f"Обновлено статусов: {len(expired_matches)} матчей")
        
    except Exception as e:
        logging.error(f"Ошибка при проверке истекших матчей: {e}")

async def start_match_checker():
    """Запуск периодической проверки матчей"""
    while True:
        await check_expired_matches()
        # Проверяем каждые 5 минут
        await asyncio.sleep(300)  # 300 секунд = 5 минут