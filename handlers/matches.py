from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from database import db
from states import MatchStates
from keyboards import (
    get_cancel_match_keyboard, 
    get_main_menu,
    get_tournaments_for_matches_keyboard
)
from config_bot import config

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id == config.ADMIN_ID

async def add_match(callback: types.CallbackQuery, state: FSMContext):
    """Начало добавления матча"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    tournament_id = int(callback.data.split('_')[2])
    
    await callback.message.answer(
        "📅 Введите дату матча (ДД.ММ.ГГГГ):\n\n"
        "Пример: *25.12.2024*",
        parse_mode="Markdown",
        reply_markup=get_cancel_match_keyboard()
    )
    
    await state.update_data(tournament_id=tournament_id)
    await MatchStates.waiting_for_match_date.set()
    await callback.answer()

async def process_match_date(message: types.Message, state: FSMContext):
    """Обработка ввода даты матча"""
    if message.text == "❌ Отмена":
        await state.finish()
        await message.answer(
            "Добавление матча отменено.",
            reply_markup=get_main_menu()
        )
        return
    
    match_date = message.text.strip()
    
    # Простая валидация формата даты (ДД.ММ.ГГГГ)
    if len(match_date) != 10 or match_date[2] != '.' or match_date[5] != '.':
        await message.answer(
            "❌ Неверный формат даты!\n"
            "Используйте формат: ДД.ММ.ГГГГ\n\n"
            "Пример: *25.12.2024*\n\n"
            "Введите дату еще раз:",
            parse_mode="Markdown",
            reply_markup=get_cancel_match_keyboard()
        )
        return
    
    await state.update_data(match_date=match_date)
    
    await message.answer(
        "🕒 Введите время матча (ЧЧ:ММ):\n\n"
        "Пример: *20:30*",
        parse_mode="Markdown",
        reply_markup=get_cancel_match_keyboard()
    )
    
    await MatchStates.waiting_for_match_time.set()

async def process_match_time(message: types.Message, state: FSMContext):
    """Обработка ввода времени матча"""
    if message.text == "❌ Отмена":
        await state.finish()
        await message.answer(
            "Добавление матча отменено.",
            reply_markup=get_main_menu()
        )
        return
    
    match_time = message.text.strip()
    
    # Простая валидация формата времени (ЧЧ:ММ)
    if len(match_time) != 5 or match_time[2] != ':':
        await message.answer(
            "❌ Неверный формат времени!\n"
            "Используйте формат: ЧЧ:ММ\n\n"
            "Пример: *20:30*\n\n"
            "Введите время еще раз:",
            parse_mode="Markdown",
            reply_markup=get_cancel_match_keyboard()
        )
        return
    
    await state.update_data(match_time=match_time)
    
    await message.answer(
        "⚽ Введите название первой команды:\n\n"
        "Пример: *Бразилия*",
        parse_mode="Markdown",
        reply_markup=get_cancel_match_keyboard()
    )
    
    await MatchStates.waiting_for_team1.set()

async def process_team1(message: types.Message, state: FSMContext):
    """Обработка ввода первой команды"""
    if message.text == "❌ Отмена":
        await state.finish()
        await message.answer(
            "Добавление матча отменено.",
            reply_markup=get_main_menu()
        )
        return
    
    team1 = message.text.strip()
    
    if len(team1) < 2:
        await message.answer(
            "❌ Название команды слишком короткое!\n"
            "Минимальная длина - 2 символа.\n\n"
            "Введите название первой команды еще раз:",
            reply_markup=get_cancel_match_keyboard()
        )
        return
    
    await state.update_data(team1=team1)
    
    await message.answer(
        "⚽ Введите название второй команды:\n\n"
        "Пример: *Аргентина*",
        parse_mode="Markdown",
        reply_markup=get_cancel_match_keyboard()
    )
    
    await MatchStates.waiting_for_team2.set()

async def process_team2(message: types.Message, state: FSMContext):
    """Обработка ввода второй команды и сохранение матча"""
    if message.text == "❌ Отмена":
        await state.finish()
        await message.answer(
            "Добавление матча отменено.",
            reply_markup=get_main_menu()
        )
        return
    
    team2 = message.text.strip()
    
    # Получаем данные из состояния
    user_data = await state.get_data()
    tournament_id = user_data.get('tournament_id')
    match_date = user_data.get('match_date')
    match_time = user_data.get('match_time')
    team1 = user_data.get('team1')
    
    if len(team2) < 2:
        await message.answer(
            "❌ Название команды слишком короткое!\n"
            "Минимальная длина - 2 символа.\n\n"
            "Введите название второй команды еще раз:",
            reply_markup=get_cancel_match_keyboard()
        )
        return
    
    # Сохраняем матч в базу
    success = await db.add_match(tournament_id, match_date, match_time, team1, team2)
    
    if success:
        await state.finish()
        
        # Получаем информацию о турнире
        tournament = await db.get_tournament_by_id(tournament_id)
        
        # Показываем сообщение об успехе
        await message.answer(
            f"✅ Матч успешно добавлен в турнир '{tournament['name']}'!",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Показываем кнопку для возврата к управлению турниром
        keyboard = InlineKeyboardMarkup()
        back_btn = InlineKeyboardButton(
            '🔙 Назад к управлению турниром', 
            callback_data=f'tournament_manage_{tournament_id}'
        )
        keyboard.add(back_btn)
        
        await message.answer(
            "Выберите действие:",
            reply_markup=keyboard
        )
        
    else:
        await message.answer(
            "❌ Ошибка при добавлении матча!",
            reply_markup=get_main_menu()
        )
        await state.finish()

async def admin_add_match(callback: types.CallbackQuery):
    """Админ: добавление матча - выбор турнира"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    tournaments = await db.get_all_tournaments()
    
    if not tournaments:
        await callback.message.edit_text(
            "❌ Нет активных турниров!\n"
            "Сначала создайте турнир для добавления матчей.",
            parse_mode="Markdown"
        )
        return
    
    await callback.message.edit_text(
        "🏆 Выберите турнир для добавления матча:",
        parse_mode="Markdown",
        reply_markup=get_tournaments_for_matches_keyboard(tournaments)
    )
    
    await callback.answer()

async def select_tournament_for_match(callback: types.CallbackQuery, state: FSMContext):
    """Выбор турнира для добавления матча"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    tournament_id = int(callback.data.split('_')[2])
    
    await callback.message.answer(
        "📅 Введите дату матча (ДД.ММ.ГГГГ):\n\n"
        "Пример: *25.12.2024*",
        parse_mode="Markdown",
        reply_markup=get_cancel_match_keyboard()
    )
    
    await state.update_data(tournament_id=tournament_id)
    await MatchStates.waiting_for_match_date.set()
    await callback.answer()

async def admin_view_matches(callback: types.CallbackQuery):
    """Админ: просмотр всех матчей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    tournaments = await db.get_all_tournaments()
    
    if not tournaments:
        await callback.message.edit_text(
            "📭 Нет активных турниров с матчами.",
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    matches_text = "📋 Все матчи по турнирам:\n\n"
    
    for tournament in tournaments:
        matches = await db.get_matches_by_tournament(tournament['id'])
        
        matches_text += f"🏆 *{tournament['name']}* ({len(matches)} матчей):\n"
        
        if matches:
            for i, match in enumerate(matches, 1):
                matches_text += (
                    f"  {i}. {match['match_date']} {match['match_time']} "
                    f"{match['team1']} vs {match['team2']}\n"
                )
        else:
            matches_text += "  Матчей пока нет\n"
        
        matches_text += "\n"
    
    await callback.message.edit_text(
        matches_text,
        parse_mode="Markdown"
    )
    await callback.answer()

async def matches_back(callback: types.CallbackQuery):
    """Возврат из управления матчами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    from handlers.admin import show_admin_panel
    await show_admin_panel(callback)

async def admin_match_management(callback: types.CallbackQuery):
    """Управление конкретным матчем для администратора"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    match_id = int(callback.data.split('_')[2])
    match = await db.get_match_by_id(match_id)
    
    if not match:
        await callback.answer("❌ Матч не найден!")
        return
    
    tournament = await db.get_tournament_by_id(match['tournament_id'])
    bets = await db.get_bets_by_match(match_id)
    
    match_text = (
        f"👑 *Управление матчем*\n\n"
        f"⚽ *Матч:* {match['team1']} vs {match['team2']}\n"
        f"🏆 *Турнир:* {tournament['name']}\n"
        f"📅 *Дата:* {match['match_date']}\n"
        f"🕒 *Время:* {match['match_time']}\n"
        f"🎯 *Ставок сделано:* {len(bets)}\n\n"
        "Выберите действие:"
    )
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    view_bets_btn = InlineKeyboardButton('📊 Посмотреть ставки', callback_data=f'admin_view_bets_{match_id}')
    delete_match_btn = InlineKeyboardButton('🗑 Удалить матч', callback_data=f'admin_delete_match_{match_id}')
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data=f'tournament_matches_{match["tournament_id"]}')
    
    keyboard.add(view_bets_btn, delete_match_btn)
    keyboard.add(back_btn)
    
    await callback.message.edit_text(
        match_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()

async def admin_delete_match_confirm(callback: types.CallbackQuery):
    """Подтверждение удаления матча"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    match_id = int(callback.data.split('_')[3])
    match = await db.get_match_by_id(match_id)
    
    if not match:
        await callback.answer("❌ Матч не найден!")
        return
    
    tournament = await db.get_tournament_by_id(match['tournament_id'])
    bets = await db.get_bets_by_match(match_id)
    
    warning_text = (
        f"⚠️ *Внимание! Удаление матча*\n\n"
        f"⚽ *Матч:* {match['team1']} vs {match['team2']}\n"
        f"🏆 *Турнир:* {tournament['name']}\n"
        f"📅 *Дата:* {match['match_date']} {match['match_time']}\n\n"
        f"❌ *Будет удалено:*\n"
        f"• Матч из турнира\n"
        f"• Все ставки на этот матч ({len(bets)} шт.)\n\n"
        f"Это действие нельзя отменить!\n\n"
        f"Подтверждаете удаление?"
    )
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    confirm_btn = InlineKeyboardButton('✅ Да, удалить', callback_data=f'admin_delete_confirm_{match_id}')
    cancel_btn = InlineKeyboardButton('❌ Отмена', callback_data=f'admin_match_{match_id}')
    
    keyboard.add(confirm_btn, cancel_btn)
    
    await callback.message.edit_text(
        warning_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()

async def admin_delete_match_execute(callback: types.CallbackQuery):
    """Выполнение удаления матча"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    match_id = int(callback.data.split('_')[3])
    match = await db.get_match_by_id(match_id)
    
    if not match:
        await callback.answer("❌ Матч не найден!")
        return
    
    # Удаляем матч
    success = await db.delete_match(match_id)
    
    if success:
        await callback.message.edit_text(
            f"✅ *Матч удален!*\n\n"
            f"⚽ {match['team1']} vs {match['team2']}\n\n"
            f"Матч и все связанные ставки были удалены из системы.",
            parse_mode="Markdown"
        )
        
        # Возвращаемся к списку матчей турнира
        from handlers.tournaments import show_tournament_matches
        
        # Создаем mock callback для возврата
        class MockCallback:
            def __init__(self, message, tournament_id):
                self.message = message
                self.data = f'tournament_matches_{tournament_id}'
                self.from_user = message.from_user
        
        mock_callback = MockCallback(callback.message, match['tournament_id'])
        await show_tournament_matches(mock_callback)
        
    else:
        await callback.message.edit_text(
            "❌ Ошибка при удалении матча!",
            parse_mode="Markdown"
        )
    
    await callback.answer()

async def add_another_match(callback: types.CallbackQuery, state: FSMContext):
    """Добавление следующего матча в тот же турнир"""
    tournament_id = int(callback.data.split('_')[2])
    
    # Начинаем процесс добавления матча заново
    await callback.message.answer(
        "📅 Введите дату матча (ДД.ММ.ГГГГ):\n\n"
        "Пример: *25.12.2024*",
        parse_mode="Markdown",
        reply_markup=get_cancel_match_keyboard()
    )
    
    await state.update_data(tournament_id=tournament_id)
    await MatchStates.waiting_for_match_date.set()
    await callback.answer()

def register_handlers_matches(dp: Dispatcher):
    """Регистрация обработчиков матчей"""
    
    # Обработчики добавления матча из турнира
    dp.register_callback_query_handler(add_match, lambda c: c.data.startswith('add_match_'))
    
    # Обработчики состояний добавления матча
    dp.register_message_handler(process_match_date, state=MatchStates.waiting_for_match_date)
    dp.register_message_handler(process_match_time, state=MatchStates.waiting_for_match_time)
    dp.register_message_handler(process_team1, state=MatchStates.waiting_for_team1)
    dp.register_message_handler(process_team2, state=MatchStates.waiting_for_team2)
    
    # Обработчики админ-панели для матчей
    dp.register_callback_query_handler(admin_add_match, lambda c: c.data == 'admin_add_match')
    dp.register_callback_query_handler(admin_view_matches, lambda c: c.data == 'admin_view_matches')
    dp.register_callback_query_handler(select_tournament_for_match, lambda c: c.data.startswith('select_tournament_'))
    dp.register_callback_query_handler(matches_back, lambda c: c.data == 'matches_back')
    
    # Обработчики управления матчами для админа
    dp.register_callback_query_handler(admin_match_management, lambda c: c.data.startswith('admin_match_'))
    dp.register_callback_query_handler(admin_delete_match_confirm, lambda c: c.data.startswith('admin_delete_match_'))
    dp.register_callback_query_handler(admin_delete_match_execute, lambda c: c.data.startswith('admin_delete_confirm_'))
    
    # Обработчик для добавления следующего матча
    dp.register_callback_query_handler(
        add_another_match, 
        lambda c: c.data.startswith('add_match_'),
        state="*"
    )