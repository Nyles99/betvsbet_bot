from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
from database.db_handler import DatabaseHandler
from keyboards.menu import (
    get_admin_main_keyboard, 
    get_admin_tournaments_keyboard,
    get_admin_tournament_detail_keyboard,
    get_admin_tournament_matches_keyboard,
    get_admin_match_detail_keyboard,
    get_admin_users_keyboard,
    get_cancel_keyboard,
    get_cancel_to_tournament_keyboard,
    get_cancel_to_matches_keyboard
)
from states.user_states import AdminStates
from utils.validators import validate_score  # Добавляем импорт
from config import config

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in config.ADMIN_IDS

async def admin_command(message: Message):
    """Обработчик команды /admin"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав доступа к этой команде.")
        return
    
    await message.answer(
        "👑 Панель администратора\n\nВыберите раздел:",
        reply_markup=get_admin_main_keyboard()
    )

async def admin_main_callback(callback: CallbackQuery, state: FSMContext):
    """Главное меню админа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return
    
    await state.finish()
    await callback.message.edit_text(
        "👑 Панель администратора\n\nВыберите раздел:",
        reply_markup=get_admin_main_keyboard()
    )

async def admin_tournaments_callback(callback: CallbackQuery, state: FSMContext):
    """Список турниров для админа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return
    
    await state.finish()
    db = DatabaseHandler('users.db')
    tournaments = db.get_all_tournaments_admin()
    
    if tournaments:
        text = "🏆 Список всех турниров:\n\n"
        for tournament in tournaments:
            status = "✅ Активный" if tournament[3] == 'active' else "❌ Неактивный"
            text += f"• {tournament[1]} ({status})\n"
    else:
        text = "🏆 Турниры отсутствуют.\n\nДобавьте первый турнир!"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_tournaments_keyboard(tournaments)
    )

async def admin_users_callback(callback: CallbackQuery, state: FSMContext):
    """Список пользователей для админа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return
    
    await state.finish()
    db = DatabaseHandler('users.db')
    users = db.get_all_users()
    users_count = db.get_users_count()
    
    text = f"👥 Все пользователи\n\n📊 Общее количество: {users_count}\n\n"
    
    # Показываем последних 10 пользователей
    for i, user in enumerate(users[:10], 1):
        text += f"{i}. ID: {user.user_id}\n"
        text += f"   📱: {user.phone_number}\n"
        if user.username:
            text += f"   👤: {user.username}\n"
        if user.full_name:
            text += f"   📛: {user.full_name}\n"
        text += f"   📅: {user.registration_date}\n\n"
    
    if users_count > 10:
        text += f"... и еще {users_count - 10} пользователей"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_users_keyboard()
    )

async def admin_stats_callback(callback: CallbackQuery, state: FSMContext):
    """Статистика для админа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return
    
    await state.finish()
    db = DatabaseHandler('users.db')
    users_count = db.get_users_count()
    tournaments = db.get_all_tournaments_admin()
    active_tournaments = db.get_all_tournaments()
    
    # Получаем общее количество матчей
    total_matches = 0
    for tournament in tournaments:
        matches = db.get_tournament_matches(tournament[0])
        total_matches += len(matches)
    
    text = f"""
📊 Статистика бота:

👥 Пользователи: {users_count}
🏆 Всего турниров: {len(tournaments)}
✅ Активных турниров: {len(active_tournaments)}
⚽ Всего матчей: {total_matches}
    """
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_main_keyboard()
    )

# Управление турнирами
async def tournament_detail_callback(callback: CallbackQuery, state: FSMContext):
    """Детальная информация о турнире"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return
    
    await state.finish()
    
    tournament_id = int(callback.data.split('_')[1])
    
    db = DatabaseHandler('users.db')
    tournament = db.get_tournament(tournament_id)
    matches = db.get_tournament_matches(tournament_id)
    
    if tournament:
        status = "✅ Активный" if tournament[3] == 'active' else "❌ Неактивный"
        text = f"""
🏆 Информация о турнире:

📌 Название: {tournament[1]}
📝 Описание: {tournament[2] or 'Нет описания'}
🔰 Статус: {status}
📅 Дата создания: {tournament[4]}
🆔 ID: {tournament[0]}
⚽ Матчей: {len(matches)}
        """
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_tournament_detail_keyboard(tournament_id, tournament[3])
        )
    else:
        await callback.answer("❌ Турнир не найден.", show_alert=True)

async def tournament_matches_callback(callback: CallbackQuery, state: FSMContext):
    """Список матчей турнира для админа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return
    
    await state.finish()
    
    tournament_id = int(callback.data.split('_')[2])
    
    db = DatabaseHandler('users.db')
    tournament = db.get_tournament(tournament_id)
    matches = db.get_tournament_matches(tournament_id)
    
    if tournament:
        if matches:
            text = f"🏆 Матчи турнира: {tournament[1]}\n\n"
            for match in matches:
                # Проверяем истекло ли время матча
                is_expired = db.is_match_expired(match[2], match[3])
                status = "⏰ Истек" if is_expired else "✅ Активен"
                text += f"📅 {match[2]} {match[3]} - {match[4]} vs {match[5]} ({status})\n\n"
        else:
            text = f"🏆 В турнире '{tournament[1]}' пока нет матчей.\n\nДобавьте первый матч!"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_tournament_matches_keyboard(tournament_id, matches)
        )
    else:
        await callback.answer("❌ Турнир не найден.", show_alert=True)

async def add_tournament_callback(callback: CallbackQuery, state: FSMContext):
    """Начало добавления турнира"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🏆 Добавление турнира\n\nВведите название турнира:",
        reply_markup=get_cancel_keyboard()
    )
    await AdminStates.waiting_for_tournament_name.set()

async def process_tournament_name(message: Message, state: FSMContext):
    """Обработка названия турнира"""
    async with state.proxy() as data:
        data['name'] = message.text
    
    await message.answer(
        "📝 Введите описание турнира:",
        reply_markup=get_cancel_keyboard()
    )
    await AdminStates.waiting_for_tournament_description.set()

async def process_tournament_description(message: Message, state: FSMContext):
    """Обработка описания турнира и сохранение"""
    async with state.proxy() as data:
        data['description'] = message.text
    
    db = DatabaseHandler('users.db')
    if db.add_tournament(data['name'], data['description'], message.from_user.id):
        await message.answer(
            "✅ Турнир успешно добавлен!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        # Показываем обновленный список турниров
        tournaments = db.get_all_tournaments_admin()
        text = "🏆 Список всех турниров:\n\n"
        for tournament in tournaments:
            status = "✅ Активный" if tournament[3] == 'active' else "❌ Неактивный"
            text += f"• {tournament[1]} ({status})\n"
        
        await message.answer(
            text,
            reply_markup=get_admin_tournaments_keyboard(tournaments)
        )
    else:
        await message.answer(
            "❌ Ошибка при добавлении турнира.",
            reply_markup=get_admin_main_keyboard()
        )
    
    await state.finish()

async def activate_tournament_callback(callback: CallbackQuery):
    """Активация турнира"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return
    
    tournament_id = int(callback.data.split('_')[2])
    
    db = DatabaseHandler('users.db')
    if db.update_tournament_status(tournament_id, 'active'):
        await callback.answer("✅ Турнир активирован!", show_alert=True)
        # Обновляем сообщение
        tournament = db.get_tournament(tournament_id)
        matches = db.get_tournament_matches(tournament_id)
        
        text = f"""
🏆 Информация о турнире:

📌 Название: {tournament[1]}
📝 Описание: {tournament[2] or 'Нет описания'}
🔰 Статус: ✅ Активный
📅 Дата создания: {tournament[4]}
🆔 ID: {tournament[0]}
⚽ Матчей: {len(matches)}
        """
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_tournament_detail_keyboard(tournament_id, 'active')
        )
    else:
        await callback.answer("❌ Ошибка при активации турнира.", show_alert=True)

async def deactivate_tournament_callback(callback: CallbackQuery):
    """Деактивация турнира"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return
    
    tournament_id = int(callback.data.split('_')[2])
    
    db = DatabaseHandler('users.db')
    if db.update_tournament_status(tournament_id, 'inactive'):
        await callback.answer("✅ Турнир деактивирован!", show_alert=True)
        # Обновляем сообщение
        tournament = db.get_tournament(tournament_id)
        matches = db.get_tournament_matches(tournament_id)
        
        text = f"""
🏆 Информация о турнире:

📌 Название: {tournament[1]}
📝 Описание: {tournament[2] or 'Нет описания'}
🔰 Статус: ❌ Неактивный
📅 Дата создания: {tournament[4]}
🆔 ID: {tournament[0]}
⚽ Матчей: {len(matches)}
        """
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_tournament_detail_keyboard(tournament_id, 'inactive')
        )
    else:
        await callback.answer("❌ Ошибка при деактивации турнира.", show_alert=True)

async def delete_tournament_callback(callback: CallbackQuery):
    """Удаление турнира"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return
    
    tournament_id = int(callback.data.split('_')[2])
    
    db = DatabaseHandler('users.db')
    if db.delete_tournament(tournament_id):
        await callback.answer("✅ Турнир удален!", show_alert=True)
        # Возвращаемся к списку турниров
        tournaments = db.get_all_tournaments_admin()
        text = "🏆 Список всех турниров:\n\n"
        for tournament in tournaments:
            status = "✅ Активный" if tournament[3] == 'active' else "❌ Неактивный"
            text += f"• {tournament[1]} ({status})\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_tournaments_keyboard(tournaments)
        )
    else:
        await callback.answer("❌ Ошибка при удалении турнира.", show_alert=True)

# Управление матчами
async def add_match_callback(callback: CallbackQuery, state: FSMContext):
    """Начало добавления матча"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return
    
    tournament_id = int(callback.data.split('_')[2])
    
    async with state.proxy() as data:
        data['tournament_id'] = tournament_id
    
    await callback.message.edit_text(
        "⚽ Добавление матча\n\nВведите дату матча в формате ДД.ММ.ГГГГ (например: 04.11.2025):",
        reply_markup=get_cancel_to_tournament_keyboard(tournament_id)
    )
    await AdminStates.waiting_for_match_date.set()

async def process_match_date(message: Message, state: FSMContext):
    """Обработка даты матча"""
    date_parts = message.text.split('.')
    if len(date_parts) != 3 or not all(part.isdigit() for part in date_parts):
        await message.answer("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ (например: 04.11.2025):")
        return
    
    async with state.proxy() as data:
        data['match_date'] = message.text
    
    await message.answer(
        "⏰ Введите время матча в формате ЧЧ:ММ (например: 20:45):",
        reply_markup=get_cancel_to_tournament_keyboard(data['tournament_id'])
    )
    await AdminStates.waiting_for_match_time.set()

async def process_match_time(message: Message, state: FSMContext):
    """Обработка времени матча"""
    time_parts = message.text.split(':')
    if len(time_parts) != 2 or not all(part.isdigit() for part in time_parts):
        await message.answer("❌ Неверный формат времени. Используйте ЧЧ:ММ (например: 20:45):")
        return
    
    async with state.proxy() as data:
        data['match_time'] = message.text
    
    await message.answer(
        "🏆 Введите название первой команды:",
        reply_markup=get_cancel_to_tournament_keyboard(data['tournament_id'])
    )
    await AdminStates.waiting_for_team1.set()

async def process_team1(message: Message, state: FSMContext):
    """Обработка названия первой команды"""
    async with state.proxy() as data:
        data['team1'] = message.text
    
    await message.answer(
        "🏆 Введите название второй команды:",
        reply_markup=get_cancel_to_tournament_keyboard(data['tournament_id'])
    )
    await AdminStates.waiting_for_team2.set()

async def process_team2(message: Message, state: FSMContext):
    """Обработка названия второй команды и сохранение матча"""
    async with state.proxy() as data:
        data['team2'] = message.text
    
    db = DatabaseHandler('users.db')
    if db.add_match(
        data['tournament_id'], 
        data['match_date'], 
        data['match_time'], 
        data['team1'], 
        data['team2'], 
        message.from_user.id
    ):
        await message.answer(
            "✅ Матч успешно добавлен!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        # Показываем обновленный список матчей
        tournament = db.get_tournament(data['tournament_id'])
        matches = db.get_tournament_matches(data['tournament_id'])
        
        if matches:
            text = f"🏆 Матчи турнира: {tournament[1]}\n\n"
            for match in matches:
                text += f"📅 {match[2]} {match[3]} - {match[4]} vs {match[5]}\n\n"
        else:
            text = f"🏆 В турнире '{tournament[1]}' пока нет матчей.\n\nДобавьте первый матч!"
        
        await message.answer(
            text,
            reply_markup=get_admin_tournament_matches_keyboard(data['tournament_id'], matches)
        )
    else:
        await message.answer(
            "❌ Ошибка при добавлении матча.",
            reply_markup=get_admin_tournament_detail_keyboard(data['tournament_id'], 'active')
        )
    
    await state.finish()

async def admin_match_detail_callback(callback: CallbackQuery, state: FSMContext):
    """Детальная информация о матче для админа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return
    
    await state.finish()
    match_id = int(callback.data.split('_')[2])
    
    db = DatabaseHandler('users.db')
    match = db.get_match(match_id)
    
    if match:
        # Получаем количество ставок на матч
        bets_count = db.get_match_bets_count(match_id)
        
        text = f"""
⚽ Информация о матче:

📅 Дата: {match[2]}
⏰ Время: {match[3]}
🏆 Команда 1: {match[4]}
🏆 Команда 2: {match[5]}
🔰 Статус: {match[6]}
📊 Ставок сделано: {bets_count}
📅 Создан: {match[7] if match[7] else 'Не указана'}
🆔 ID: {match[0]}
        """
        
        # Добавляем информацию о результате, если он есть и не является датой
        match_result = match[8] if len(match) > 8 else None
        
        # Простая проверка: если результат содержит "-" и состоит только из цифр и дефиса, то это счет
        if (match_result and 
            match_result != 'None' and 
            '-' in str(match_result) and
            all(c.isdigit() or c == '-' for c in str(match_result).strip())):
            text += f"\n🎯 Результат: {match_result}"
        else:
            text += f"\n🎯 Результат: `Неизвестно`"  # Зеленый шрифт
        
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_match_detail_keyboard(match_id, match[1])
        )
    else:
        await callback.answer("❌ Матч не найден.", show_alert=True)

async def enter_result_callback(callback: CallbackQuery, state: FSMContext):
    """Начало ввода результата матча"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return
    
    match_id = int(callback.data.split('_')[2])
    
    db = DatabaseHandler('users.db')
    match = db.get_match(match_id)
    
    if not match:
        await callback.answer("❌ Матч не найден.", show_alert=True)
        return
    
    async with state.proxy() as data:
        data['match_id'] = match_id
        data['tournament_id'] = match[1]
    
    await callback.message.edit_text(
        f"⚽ Ввод результата матча:\n\n"
        f"📅 {match[2]} {match[3]}\n"
        f"🏆 {match[4]} vs {match[5]}\n\n"
        f"📝 Введите окончательный счет матча в формате X-Y (например: 2-1):",
        reply_markup=get_cancel_to_matches_keyboard(match[1])
    )
    await AdminStates.waiting_for_match_result.set()

async def process_match_result(message: Message, state: FSMContext):
    """Обработка результата матча"""
    result = message.text.strip()
    
    if not validate_score(result):
        async with state.proxy() as data:
            tournament_id = data['tournament_id']
        
        await message.answer(
            "❌ Неверный формат счета. Используйте формат X-Y (например: 2-1). Попробуйте еще раз:",
            reply_markup=get_cancel_to_matches_keyboard(tournament_id)
        )
        return
    
    async with state.proxy() as data:
        match_id = data['match_id']
        tournament_id = data['tournament_id']
    
    db = DatabaseHandler('users.db')
    
    if db.update_match_result(match_id, result):
        await message.answer(
            f"✅ Результат матча {result} успешно сохранен!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        # Возвращаемся к информации о матче
        match = db.get_match(match_id)
        match_with_bets = db.get_match_with_bets(match_id)
        bets_count = match_with_bets[8] if match_with_bets else 0
        
        text = f"""
⚽ Информация о матче:

📅 Дата: {match[2]}
⏰ Время: {match[3]}
🏆 Команда 1: {match[4]}
🏆 Команда 2: {match[5]}
🔰 Статус: {match[6]}
🎯 Результат: {match[8]}
📊 Ставок сделано: {bets_count}
📅 Создан: {match[7] if match[7] else 'Не указана'}
🆔 ID: {match[0]}
        """
        
        await message.answer(
            text,
            reply_markup=get_admin_match_detail_keyboard(match_id, tournament_id)
        )
    else:
        await message.answer(
            "❌ Ошибка при сохранении результата.",
            reply_markup=get_admin_match_detail_keyboard(match_id, tournament_id)
        )
    
    await state.finish()

async def delete_match_callback(callback: CallbackQuery):
    """Удаление матча"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return
    
    match_id = int(callback.data.split('_')[2])
    
    db = DatabaseHandler('users.db')
    match = db.get_match(match_id)
    
    if match and db.delete_match(match_id):
        await callback.answer("✅ Матч удален!", show_alert=True)
        # Возвращаемся к списку матчей турнира
        tournament_id = match[1]
        tournament = db.get_tournament(tournament_id)
        matches = db.get_tournament_matches(tournament_id)
        
        if matches:
            text = f"🏆 Матчи турнира: {tournament[1]}\n\n"
            for match_item in matches:
                text += f"📅 {match_item[2]} {match_item[3]} - {match_item[4]} vs {match_item[5]}\n\n"
        else:
            text = f"🏆 В турнире '{tournament[1]}' пока нет матчей.\n\nДобавьте первый матч!"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_tournament_matches_keyboard(tournament_id, matches)
        )
    else:
        await callback.answer("❌ Ошибка при удалении матча.", show_alert=True)

async def admin_back_to_main(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню админа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа.", show_alert=True)
        return
    
    await state.finish()
    await callback.message.edit_text(
        "👑 Панель администратора\n\nВыберите раздел:",
        reply_markup=get_admin_main_keyboard()
    )

def register_admin_handlers(dp: Dispatcher):
    """Регистрация обработчиков админ-панели"""
    # Команда /admin
    dp.register_message_handler(admin_command, commands=['admin'])
    
    # Главное меню админа
    dp.register_callback_query_handler(admin_main_callback, lambda c: c.data == "admin_main", state="*")
    dp.register_callback_query_handler(admin_back_to_main, lambda c: c.data == "admin_main", state="*")
    
    # Разделы админ-панели
    dp.register_callback_query_handler(admin_tournaments_callback, lambda c: c.data == "admin_tournaments", state="*")
    dp.register_callback_query_handler(admin_users_callback, lambda c: c.data == "admin_users", state="*")
    dp.register_callback_query_handler(admin_stats_callback, lambda c: c.data == "admin_stats", state="*")
    
    # Управление турнирами
    dp.register_callback_query_handler(add_tournament_callback, lambda c: c.data == "add_tournament", state="*")
    dp.register_callback_query_handler(tournament_detail_callback, lambda c: c.data.startswith("tournament_") and not c.data.startswith("tournament_matches_"), state="*")
    dp.register_callback_query_handler(tournament_matches_callback, lambda c: c.data.startswith("tournament_matches_"), state="*")
    dp.register_callback_query_handler(activate_tournament_callback, lambda c: c.data.startswith("activate_tournament_"))
    dp.register_callback_query_handler(deactivate_tournament_callback, lambda c: c.data.startswith("deactivate_tournament_"))
    dp.register_callback_query_handler(delete_tournament_callback, lambda c: c.data.startswith("delete_tournament_"))
    
    # Управление матчами
    dp.register_callback_query_handler(add_match_callback, lambda c: c.data.startswith("add_match_"), state="*")
    dp.register_callback_query_handler(admin_match_detail_callback, lambda c: c.data.startswith("admin_match_"), state="*")
    dp.register_callback_query_handler(enter_result_callback, lambda c: c.data.startswith("enter_result_"), state="*")
    dp.register_callback_query_handler(delete_match_callback, lambda c: c.data.startswith("delete_match_"))
    
    # FSM для добавления турнира
    dp.register_message_handler(process_tournament_name, state=AdminStates.waiting_for_tournament_name)
    dp.register_message_handler(process_tournament_description, state=AdminStates.waiting_for_tournament_description)
    
    # FSM для добавления матча
    dp.register_message_handler(process_match_date, state=AdminStates.waiting_for_match_date)
    dp.register_message_handler(process_match_time, state=AdminStates.waiting_for_match_time)
    dp.register_message_handler(process_team1, state=AdminStates.waiting_for_team1)
    dp.register_message_handler(process_team2, state=AdminStates.waiting_for_team2)
    
    # FSM для ввода результата матча
    dp.register_message_handler(process_match_result, state=AdminStates.waiting_for_match_result)