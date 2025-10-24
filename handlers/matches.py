from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from datetime import datetime
import re

from database import db
from states import MatchStates
from keyboards import (
    get_tournaments_for_matches_keyboard, 
    get_tournament_matches_keyboard,
    get_cancel_match_keyboard,
    get_main_menu
)
from config_bot import config

async def start_add_match(callback: types.CallbackQuery, state: FSMContext):
    """Начало процесса добавления матча"""
    if not callback.from_user.id == config.ADMIN_ID:
        await callback.answer("❌ Недостаточно прав!")
        return
    
    tournaments = await db.get_all_tournaments()
    
    if not tournaments:
        await callback.message.edit_text(
            "❌ Нет доступных турниров!\n"
            "Сначала создайте турнир.",
            reply_markup=None
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "⚽ *Добавление матча*\n\n"
        "Выберите турнир для добавления матча:",
        parse_mode="Markdown",
        reply_markup=get_tournaments_for_matches_keyboard(tournaments)
    )
    
    await MatchStates.waiting_for_tournament_select.set()
    await callback.answer()

async def select_tournament_for_match(callback: types.CallbackQuery, state: FSMContext):
    """Выбор турнира для добавления матча"""
    if not callback.from_user.id == config.ADMIN_ID:
        await callback.answer("❌ Недостаточно прав!")
        return
    
    tournament_id = int(callback.data.split('_')[2])
    tournament = await db.get_tournament_by_id(tournament_id)
    
    if not tournament:
        await callback.answer("❌ Турнир не найден!")
        return
    
    await state.update_data(tournament_id=tournament_id, tournament_name=tournament['name'])
    
    await callback.message.edit_text(
        f"⚽ *Добавление матча в турнир: {tournament['name']}*\n\n"
        "📅 Введите дату матча в формате *ДД.ММ.ГГГГ*:\n\n"
        "Пример: *19.11.2024*",
        parse_mode="Markdown"
    )
    
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
    
    # Проверяем формат даты
    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', match_date):
        await message.answer(
            "❌ Неверный формат даты!\n"
            "Введите дату в формате *ДД.ММ.ГГГГ*\n\n"
            "Пример: *19.11.2024*\n\n"
            "Попробуйте еще раз:",
            parse_mode="Markdown",
            reply_markup=get_cancel_match_keyboard()
        )
        return
    
    # Проверяем валидность даты
    try:
        day, month, year = map(int, match_date.split('.'))
        datetime(year, month, day)
    except ValueError:
        await message.answer(
            "❌ Неверная дата!\n"
            "Проверьте правильность введенной даты.\n\n"
            "Попробуйте еще раз:",
            reply_markup=get_cancel_match_keyboard()
        )
        return
    
    await state.update_data(match_date=match_date)
    
    await message.answer(
        "✅ Дата принята!\n\n"
        "🕒 Теперь введите время матча по *Московскому времени* в формате *ЧЧ:ММ*:\n\n"
        "Пример: *17:00*",
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
    
    # Проверяем формат времени
    if not re.match(r'^\d{2}:\d{2}$', match_time):
        await message.answer(
            "❌ Неверный формат времени!\n"
            "Введите время в формате *ЧЧ:ММ*\n\n"
            "Пример: *17:00*\n\n"
            "Попробуйте еще раз:",
            parse_mode="Markdown",
            reply_markup=get_cancel_match_keyboard()
        )
        return
    
    # Проверяем валидность времени
    try:
        hours, minutes = map(int, match_time.split(':'))
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Неверное время!\n"
            "Часы должны быть от 00 до 23, минуты от 00 до 59.\n\n"
            "Попробуйте еще раз:",
            reply_markup=get_cancel_match_keyboard()
        )
        return
    
    await state.update_data(match_time=match_time)
    
    await message.answer(
        "✅ Время принято!\n\n"
        "🏆 Теперь введите название *первой команды*:\n\n"
        "Пример: *Англия*",
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
            "Попробуйте еще раз:",
            reply_markup=get_cancel_match_keyboard()
        )
        return
    
    await state.update_data(team1=team1)
    
    await message.answer(
        f"✅ Первая команда: *{team1}*\n\n"
        "🏆 Теперь введите название *второй команды*:\n\n"
        "Пример: *Испания*",
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
    
    if len(team2) < 2:
        await message.answer(
            "❌ Название команды слишком короткое!\n"
            "Минимальная длина - 2 символа.\n\n"
            "Попробуйте еще раз:",
            reply_markup=get_cancel_match_keyboard()
        )
        return
    
    # Получаем все данные из состояния
    user_data = await state.get_data()
    tournament_id = user_data.get('tournament_id')
    tournament_name = user_data.get('tournament_name')
    match_date = user_data.get('match_date')
    match_time = user_data.get('match_time')
    team1 = user_data.get('team1')
    
    # Сохраняем матч в базу
    success = await db.add_match(tournament_id, match_date, match_time, team1, team2)
    
    if success:
        await message.answer(
            f"✅ Матч успешно добавлен в турнир *{tournament_name}*!\n\n"
            f"📅 *Дата:* {match_date}\n"
            f"🕒 *Время:* {match_time}\n"
            f"⚽ *Матч:* {team1} - {team2}",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            "❌ Ошибка при добавлении матча!",
            reply_markup=get_main_menu()
        )
    
    await state.finish()

async def show_tournament_matches(callback: types.CallbackQuery):
    """Показать матчи турнира"""
    tournament_id = int(callback.data.split('_')[1])
    tournament = await db.get_tournament_by_id(tournament_id)
    
    if not tournament:
        await callback.answer("❌ Турнир не найден!")
        return
    
    matches = await db.get_matches_by_tournament(tournament_id)
    is_admin = callback.from_user.id == config.ADMIN_ID
    
    if not matches:
        await callback.message.edit_text(
            f"⚽ *{tournament['name']}*\n\n"
            "📭 В этом турнире пока нет матчей.",
            parse_mode="Markdown",
            reply_markup=get_tournament_matches_keyboard(matches, tournament_id, is_admin)
        )
    else:
        matches_text = f"⚽ *{tournament['name']}*\n\n"
        matches_text += "📋 *Список матчей:*\n\n"
        
        for i, match in enumerate(matches, 1):
            matches_text += f"{i}. {match['match_date']} {match['match_time']} {match['team1']} - {match['team2']}\n"
        
        await callback.message.edit_text(
            matches_text,
            parse_mode="Markdown",
            reply_markup=get_tournament_matches_keyboard(matches, tournament_id, is_admin)
        )
    
    await callback.answer()

async def matches_back(callback: types.CallbackQuery, state: FSMContext):
    """Возврат из управления матчами"""
    await state.finish()
    from handlers.tournaments import show_tournaments
    await show_tournaments(callback.message)
    await callback.answer()

def register_handlers_matches(dp: Dispatcher):
    """Регистрация обработчиков матчей"""
    # Обработчики callback-кнопок
    dp.register_callback_query_handler(start_add_match, lambda c: c.data.startswith('add_match_'))
    dp.register_callback_query_handler(select_tournament_for_match, lambda c: c.data.startswith('select_tournament_'))
    dp.register_callback_query_handler(show_tournament_matches, lambda c: c.data.startswith('tournament_matches_'))
    dp.register_callback_query_handler(matches_back, lambda c: c.data == 'matches_back')
    
    # Обработчики состояний добавления матча
    dp.register_message_handler(process_match_date, state=MatchStates.waiting_for_match_date)
    dp.register_message_handler(process_match_time, state=MatchStates.waiting_for_match_time)
    dp.register_message_handler(process_team1, state=MatchStates.waiting_for_team1)
    dp.register_message_handler(process_team2, state=MatchStates.waiting_for_team2)