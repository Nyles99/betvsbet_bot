from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import db
from keyboards import (
    get_score_keyboard, 
    get_bets_back_keyboard, 
    get_main_menu,
    get_user_tournaments_keyboard,
    get_match_details_keyboard,
    get_bet_confirmation_keyboard,
    get_edit_bet_keyboard,
    get_bets_list_keyboard,
    get_bet_actions_keyboard,
    get_bet_stats_keyboard,
    get_back_to_tournament_keyboard,
    get_profile_keyboard,
    get_tournaments_for_bets_keyboard,
    get_bets_back_to_tournaments_keyboard
)
from config_bot import config

async def show_match_details(callback: types.CallbackQuery):
    """Показать детали матча и предложить сделать ставку"""
    match_id = int(callback.data.split('_')[1])
    match = await db.get_match_by_id(match_id)
    
    if not match:
        await callback.answer("❌ Матч не найден!")
        return
    
    # Проверяем, сделал ли пользователь уже ставку на этот матч
    user_id = callback.from_user.id
    existing_bet = await db.get_match_bet(user_id, match_id)
    
    tournament = await db.get_tournament_by_id(match['tournament_id'])
    
    if existing_bet:
        # Пользователь уже сделал ставку - показываем его ставку
        await callback.message.edit_text(
            f"⚽ *{match['team1']} vs {match['team2']}*\n\n"
            f"🏆 Турнир: {tournament['name'] if tournament else 'Неизвестно'}\n"
            f"📅 Дата: {match['match_date']}\n"
            f"🕒 Время: {match['match_time']}\n\n"
            f"✅ *Ваша ставка:* {existing_bet['team1_score']}-{existing_bet['team2_score']}\n\n"
            "Ставка уже сделана и отображается в вашем личном кабинете.",
            parse_mode="Markdown",
            reply_markup=get_match_details_keyboard(match_id, has_bet=True)
        )
    else:
        # Предлагаем сделать ставку
        await callback.message.edit_text(
            f"⚽ *{match['team1']} vs {match['team2']}*\n\n"
            f"🏆 Турнир: {tournament['name'] if tournament else 'Неизвестно'}\n"
            f"📅 Дата: {match['match_date']}\n"
            f"🕒 Время: {match['match_time']}\n\n"
            "🎯 *Сделайте ставку на счет матча:*\n"
            "Выберите предполагаемый результат:",
            parse_mode="Markdown",
            reply_markup=get_score_keyboard(match_id)
        )
    
    await callback.answer()

async def process_bet(callback: types.CallbackQuery):
    """Обработка выбора счета для ставки"""
    # callback_data format: bet_123_1-0
    parts = callback.data.split('_')
    match_id = int(parts[1])
    score = parts[2]
    team1_score, team2_score = map(int, score.split('-'))
    
    user_id = callback.from_user.id
    
    # Получаем информацию о матче для подтверждения
    match = await db.get_match_by_id(match_id)
    if not match:
        await callback.answer("❌ Матч не найден!")
        return
    
    tournament = await db.get_tournament_by_id(match['tournament_id'])
    
    # Показываем подтверждение ставки
    await callback.message.edit_text(
        f"🎯 *Подтверждение ставки*\n\n"
        f"⚽ *Матч:* {match['team1']} vs {match['team2']}\n"
        f"🏆 Турнир: {tournament['name'] if tournament else 'Неизвестно'}\n"
        f"📅 Дата: {match['match_date']}\n"
        f"🕒 Время: {match['match_time']}\n\n"
        f"✅ *Ваш прогноз:* **{team1_score}-{team2_score}**\n\n"
        "Подтверждаете ставку?",
        parse_mode="Markdown",
        reply_markup=get_bet_confirmation_keyboard(match_id, score)
    )
    
    await callback.answer()

async def confirm_bet(callback: types.CallbackQuery):
    """Подтверждение и сохранение ставки"""
    # callback_data format: confirm_bet_123_1-0
    parts = callback.data.split('_')
    match_id = int(parts[2])
    score = parts[3]
    team1_score, team2_score = map(int, score.split('-'))
    
    user_id = callback.from_user.id
    
    # Сохраняем ставку в базу
    success = await db.add_match_bet(user_id, match_id, team1_score, team2_score)
    
    if success:
        match = await db.get_match_by_id(match_id)
        tournament = await db.get_tournament_by_id(match['tournament_id'])
        
        await callback.message.edit_text(
            f"✅ *Ставка принята!*\n\n"
            f"⚽ {match['team1']} vs {match['team2']}\n"
            f"🏆 Турнир: {tournament['name'] if tournament else 'Неизвестно'}\n"
            f"🎯 Ваш прогноз: **{team1_score}-{team2_score}**\n\n"
            "Ставка добавлена в ваш личный кабинет! 🎉",
            parse_mode="Markdown"
        )
        
        # ВОЗВРАЩАЕМСЯ В МЕНЮ ТУРНИРА ВМЕСТО ПОКАЗА СЛЕДУЮЩЕГО МАТЧА
        from handlers.tournaments import show_tournament_matches
        
        # Создаем mock callback для возврата к турниру
        class MockCallback:
            def __init__(self, message, tournament_id):
                self.message = message
                self.data = f'tournament_matches_{tournament_id}'
                self.from_user = message.from_user
        
        mock_callback = MockCallback(callback.message, match['tournament_id'])
        await show_tournament_matches(mock_callback)
        
    else:
        await callback.message.edit_text(
            "❌ Ошибка при сохранении ставки!\n"
            "Попробуйте позже.",
            parse_mode="Markdown"
        )
    
    await callback.answer()

async def show_match_after_bet(callback: types.CallbackQuery, match_id: int):
    """Показать следующий матч для ставки после успешной ставки"""
    match = await db.get_match_by_id(match_id)
    
    if not match:
        await callback.answer("❌ Матч не найден!")
        return
    
    # Проверяем, сделал ли пользователь уже ставку на этот матч
    user_id = callback.from_user.id
    existing_bet = await db.get_match_bet(user_id, match_id)
    
    tournament = await db.get_tournament_by_id(match['tournament_id'])
    
    if existing_bet:
        # Пользователь уже сделал ставку - показываем его ставку
        await callback.message.answer(
            f"⚽ *{match['team1']} vs {match['team2']}*\n\n"
            f"🏆 Турнир: {tournament['name'] if tournament else 'Неизвестно'}\n"
            f"📅 Дата: {match['match_date']}\n"
            f"🕒 Время: {match['match_time']}\n\n"
            f"✅ *Ваша ставка:* {existing_bet['team1_score']}-{existing_bet['team2_score']}\n\n"
            "Ставка уже сделана и отображается в вашем личном кабинете.",
            parse_mode="Markdown",
            reply_markup=get_match_details_keyboard(match_id, has_bet=True)
        )
    else:
        # Предлагаем сделать ставку
        await callback.message.answer(
            f"🎯 *Следующий матч для прогноза:*\n\n"
            f"⚽ *{match['team1']} vs {match['team2']}*\n\n"
            f"🏆 Турнир: {tournament['name'] if tournament else 'Неизвестно'}\n"
            f"📅 Дата: {match['match_date']}\n"
            f"🕒 Время: {match['match_time']}\n\n"
            "Сделайте ставку на счет матча:",
            parse_mode="Markdown",
            reply_markup=get_score_keyboard(match_id)
        )

async def cancel_bet(callback: types.CallbackQuery):
    """Отмена ставки"""
    match_id = int(callback.data.split('_')[2])
    
    # Возвращаемся к деталям матча
    match = await db.get_match_by_id(match_id)
    if match:
        tournament = await db.get_tournament_by_id(match['tournament_id'])
        
        await callback.message.edit_text(
            f"⚽ *{match['team1']} vs {match['team2']}*\n\n"
            f"🏆 Турнир: {tournament['name'] if tournament else 'Неизвестно'}\n"
            f"📅 Дата: {match['match_date']}\n"
            f"🕒 Время: {match['match_time']}\n\n"
            "🎯 *Сделайте ставку на счет матча:*\n"
            "Выберите предполагаемый результат:",
            parse_mode="Markdown",
            reply_markup=get_score_keyboard(match_id)
        )
    else:
        await callback.message.edit_text(
            "❌ Создание ставки отменено.",
            parse_mode="Markdown"
        )
    
    await callback.answer()

async def show_user_tournaments(callback: types.CallbackQuery):
    """Показать раздел 'Идущие турниры' в личном кабинете"""
    user_id = callback.from_user.id
    
    # Получаем количество ставок пользователя
    bets_count = await db.get_user_bets_count(user_id)
    
    await callback.message.edit_text(
        "📊 *Идущие турниры*\n\n"
        f"🎯 У вас сделано ставок: **{bets_count}**\n\n"
        "Здесь вы можете просмотреть матчи, на которые сделали ставки, "
        "и управлять своими прогнозами.",
        parse_mode="Markdown",
        reply_mup=get_user_tournaments_keyboard()
    )
    await callback.answer()

async def show_my_bets(callback: types.CallbackQuery):
    """Показать выбор турниров для просмотра ставок"""
    print("DEBUG: show_my_bets вызвана")
    user_id = callback.from_user.id
    
    # Получаем турниры, в которых у пользователя есть ставки
    tournaments_with_bets = await db.get_user_active_tournaments_with_bets(user_id)
    print(f"DEBUG: Найдено турниров со ставками: {len(tournaments_with_bets)}")
    
    if not tournaments_with_bets:
        await callback.message.edit_text(
            "📭 *У вас пока нет ставок*\n\n"
            "Чтобы сделать ставку:\n"
            "1. Перейдите в раздел '⚽ Турниры'\n"
            "2. Выберите турнир\n" 
            "3. Выберите матч для прогнозирования счета\n"
            "4. Сделайте ставку из предложенных вариантов\n\n"
            "🎯 Ставки помогают участвовать в тотализаторе и соревноваться с другими участниками!",
            parse_mode="Markdown",
            reply_markup=get_bets_back_keyboard()
        )
    else:
        total_bets = sum(t['bets_count'] for t in tournaments_with_bets)
        
        selection_text = (
            "🎯 *Ваши ставки по турнирам*\n\n"
            f"📊 Всего ставок: **{total_bets}**\n"
            f"🏆 Турниров со ставками: **{len(tournaments_with_bets)}**\n\n"
            "Выберите турнир для просмотра ставок:"
        )
        
        keyboard = get_tournaments_for_bets_keyboard(tournaments_with_bets)
        
        await callback.message.edit_text(
            selection_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    await callback.answer()

async def show_bets_by_tournament(callback: types.CallbackQuery):
    """Показать ставки пользователя по выбранному турниру в виде таблицы"""
    print("DEBUG: show_bets_by_tournament вызвана")
    tournament_id = int(callback.data.split('_')[2])
    print(f"DEBUG: tournament_id = {tournament_id}")
    
    user_id = callback.from_user.id
    tournament_bets = await db.get_user_bets_by_tournament(user_id, tournament_id)
    tournament = await db.get_tournament_by_id(tournament_id)
    
    print(f"DEBUG: Найдено ставок в турнире: {len(tournament_bets)}")
    
    if not tournament_bets:
        await callback.message.edit_text(
            f"📭 *Ставки в турнире: {tournament['name']}*\n\n"
            "У вас пока нет ставок в этом турнире.\n\n"
            "Чтобы сделать ставку, перейдите в раздел турниров и выберите матч.",
            parse_mode="Markdown",
            reply_markup=get_bets_back_to_tournaments_keyboard()
        )
        await callback.answer()
        return
    
    # Форматируем ставки в виде таблицы
    bets_text = format_bets_table(tournament_bets, tournament['name'])
    
    await callback.message.edit_text(
        bets_text,
        parse_mode="HTML",
        reply_markup=get_bets_back_to_tournaments_keyboard()
    )
    await callback.answer()

def format_bets_table_simple(bets: list, tournament_name: str) -> str:
    """Простое форматирование ставок в виде таблицы"""
    table_text = (
        f"<b>🎯 Ваши ставки в турнире: {tournament_name}</b>\n\n"
        "<b>Дата        Матч                          Счет</b>\n"
        "─────────────────────────────────────────────\n"
    )
    
    for bet in bets:
        # Форматируем дату
        match_date = bet['match_date']
        if len(match_date) > 5:
            match_date = match_date[:5]  # Берем только ДД.ММ
        
        # Форматируем матч
        match_text = f"{bet['team1']} - {bet['team2']}"
        if len(match_text) > 25:
            match_text = match_text[:22] + "..."
        
        # Форматируем счет
        score = f"{bet['team1_score']}-{bet['team2_score']}"
        
        # Добавляем строку
        table_text += f"{match_date:<10} {match_text:<25} {score:>6}\n"
    
    table_text += f"\n<b>📊 Всего ставок:</b> {len(bets)}"
    
    return table_text

def format_bets_table(bets: list, tournament_name: str) -> str:
    """Форматирование ставок в виде таблицы с выравниванием"""
    
    # Создаем шапку таблицы
    table_header = (
        f"<b>🎯 Ваши ставки в турнире: {tournament_name}</b>\n\n"
        "<b>┌────────────┬──────────────────────────────┬────────┐</b>\n"
        "<b>│   Дата     │            Матч             │  Счет  │</b>\n"
        "<b>├────────────┼──────────────────────────────┼────────┤</b>\n"
    )
    
    table_rows = ""
    
    for i, bet in enumerate(bets, 1):
        # Форматируем дату (ДД.ММ)
        match_date = bet['match_date']
        if len(match_date) > 5:
            match_date = match_date[:5]  # Берем только ДД.ММ
        
        # Форматируем матч (команда1 vs команда2)
        match_text = f"{bet['team1']} vs {bet['team2']}"
        if len(match_text) > 24:
            match_text = match_text[:21] + "..."
        
        # Форматируем счет
        score = f"{bet['team1_score']}-{bet['team2_score']}"
        
        # Создаем строку таблицы
        table_rows += (
            f"<b>│</b> {match_date:<10} <b>│</b> {match_text:<26} <b>│</b> {score:>6} <b>│</b>\n"
        )
    
    # Подвал таблицы
    table_footer = (
        "<b>└────────────┴──────────────────────────────┴────────┘</b>\n\n"
        f"<b>📊 Всего ставок:</b> {len(bets)}"
    )
    
    return table_header + table_rows + table_footer

async def view_bet_details(callback: types.CallbackQuery):
    """Просмотр деталей конкретной ставки"""
    bet_id = int(callback.data.split('_')[2])
    
    # Находим ставку по ID
    user_id = callback.from_user.id
    user_bets = await db.get_user_bets(user_id)
    target_bet = None
    
    for bet in user_bets:
        if bet['id'] == bet_id:
            target_bet = bet
            break
    
    if not target_bet:
        await callback.answer("❌ Ставка не найдена!")
        return
    
    bet_text = (
        f"📊 *Детали ставки*\n\n"
        f"⚽ **{target_bet['team1']} vs {target_bet['team2']}**\n"
        f"🎯 Ваш прогноз: **{target_bet['team1_score']}-{target_bet['team2_score']}**\n"
        f"🏆 Турнир: {target_bet['tournament_name']}\n"
        f"📅 Дата: {target_bet['match_date']}\n"
        f"🕒 Время: {target_bet['match_time']}\n"
        f"⏰ Ставка сделана: {target_bet['bet_date'][:16]}\n\n"
        "Вы можете изменить или удалить ставку:"
    )
    
    await callback.message.edit_text(
        bet_text,
        parse_mode="Markdown",
        reply_markup=get_bet_actions_keyboard(bet_id, target_bet['match_id'])
    )
    await callback.answer()

async def edit_bet(callback: types.CallbackQuery):
    """Редактирование существующей ставки"""
    bet_id = int(callback.data.split('_')[2])
    
    # Находим ставку и переходим к выбору нового счета
    user_id = callback.from_user.id
    user_bets = await db.get_user_bets(user_id)
    target_bet = None
    
    for bet in user_bets:
        if bet['id'] == bet_id:
            target_bet = bet
            break
    
    if not target_bet:
        await callback.answer("❌ Ставка не найдена!")
        return
    
    match = await db.get_match_by_id(target_bet['match_id'])
    if not match:
        await callback.answer("❌ Матч не найден!")
        return
    
    tournament = await db.get_tournament_by_id(match['tournament_id'])
    
    await callback.message.edit_text(
        f"✏️ *Редактирование ставки*\n\n"
        f"⚽ *{match['team1']} vs {match['team2']}*\n"
        f"🏆 Турнир: {tournament['name'] if tournament else 'Неизвестно'}\n"
        f"📅 Дата: {match['match_date']}\n"
        f"🕒 Время: {match['match_time']}\n\n"
        f"📋 Текущая ставка: **{target_bet['team1_score']}-{target_bet['team2_score']}**\n\n"
        "Выберите новый счет матча:",
        parse_mode="Markdown",
        reply_markup=get_score_keyboard(target_bet['match_id'])
    )
    await callback.answer()

async def delete_bet(callback: types.CallbackQuery):
    """Удаление ставки"""
    match_id = int(callback.data.split('_')[2])
    user_id = callback.from_user.id
    
    # Находим информацию о матче перед удалением
    match = await db.get_match_by_id(match_id)
    if not match:
        await callback.answer("❌ Матч не найден!")
        return
    
    # Удаляем ставку
    success = await db.delete_match_bet(user_id, match_id)
    
    if success:
        await callback.message.edit_text(
            f"🗑 *Ставка удалена!*\n\n"
            f"⚽ {match['team1']} vs {match['team2']}\n\n"
            "Ставка успешно удалена из вашего профиля.",
            parse_mode="Markdown",
            reply_markup=get_bets_back_keyboard()
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка при удалении ставки!",
            parse_mode="Markdown",
            reply_markup=get_bets_back_keyboard()
        )
    
    await callback.answer()

async def view_match_bets(callback: types.CallbackQuery):
    """Просмотр всех ставок на конкретный матч"""
    match_id = int(callback.data.split('_')[2])
    
    match = await db.get_match_by_id(match_id)
    if not match:
        await callback.answer("❌ Матч не найден!")
        return
    
    # Получаем все ставки на этот матч
    all_bets = await db.get_bets_by_match(match_id)
    tournament = await db.get_tournament_by_id(match['tournament_id'])
    
    if not all_bets:
        await callback.message.edit_text(
            f"⚽ *{match['team1']} vs {match['team2']}*\n\n"
            f"🏆 Турнир: {tournament['name'] if tournament else 'Неизвестно'}\n"
            f"📅 Дата: {match['match_date']}\n"
            f"🕒 Время: {match['match_time']}\n\n"
            "📊 На этот матч пока нет ставок.",
            parse_mode="Markdown",
            reply_markup=get_bet_stats_keyboard(match_id, is_admin=callback.from_user.id == config.ADMIN_ID)
        )
    else:
        bets_text = (
            f"⚽ *{match['team1']} vs {match['team2']}*\n\n"
            f"🏆 Турнир: {tournament['name'] if tournament else 'Неизвестно'}\n"
            f"📅 Дата: {match['match_date']}\n"
            f"🕒 Время: {match['match_time']}\n\n"
            f"📊 *Ставки на матч ({len(all_bets)}):*\n\n"
        )
        
        # Группируем ставки по счету
        score_counts = {}
        for bet in all_bets:
            score = f"{bet['team1_score']}-{bet['team2_score']}"
            if score in score_counts:
                score_counts[score] += 1
            else:
                score_counts[score] = 1
        
        # Сортируем по популярности
        sorted_scores = sorted(score_counts.items(), key=lambda x: x[1], reverse=True)
        
        for score, count in sorted_scores:
            bets_text += f"• **{score}** - {count} ставок\n"
        
        bets_text += f"\n👥 Всего участников: **{len(all_bets)}**"
        
        await callback.message.edit_text(
            bets_text,
            parse_mode="Markdown",
            reply_markup=get_bet_stats_keyboard(match_id, is_admin=callback.from_user.id == config.ADMIN_ID)
        )
    
    await callback.answer()

async def back_to_tournament(callback: types.CallbackQuery):
    """Возврат к списку матчей турнира"""
    parts = callback.data.split('_')
    if len(parts) >= 3:
        match_id = int(parts[2])
        match = await db.get_match_by_id(match_id)
        
        if match:
            from handlers.tournaments import show_tournament_matches
            await show_tournament_matches(callback, match['tournament_id'])
            return
    
    await callback.answer("❌ Ошибка при возврате к турниру")

async def user_tournaments_back(callback: types.CallbackQuery):
    """Возврат из раздела ставок в личный кабинет"""
    user_id = callback.from_user.id
    user_data = await db.get_user_by_id(user_id)
    
    if not user_data:
        await callback.answer("❌ Ошибка: пользователь не найден")
        return
    
    # Получаем статистику пользователя
    bets_count = await db.get_user_bets_count(user_id)
    tournaments_count = await db.get_tournaments_count()
    
    profile_text = (
        "👤 *Ваш профиль:*\n\n"
        f"🔑 *Логин:* `{user_data['username']}`\n"
        f"📧 *Email:* `{user_data['email']}`\n"
        f"📞 *Телефон:* `{user_data['phone'] or 'Не указан'}`\n"
        f"👨‍💼 *ФИО:* {user_data['full_name']}\n"
        f"📅 *Дата регистрации:* {user_data['registration_date'][:10]}\n"
        f"🕒 *Последнее обновление:* {user_data['last_login'][:16]}\n\n"
        f"📊 *Статистика:*\n"
        f"• Сделано ставок: **{bets_count}**\n"
        f"• Активных турниров: **{tournaments_count}**\n\n"
        "Выберите что хотите изменить:"
    )
    
    await callback.message.edit_text(
        profile_text,
        parse_mode="Markdown",
        reply_markup=get_profile_keyboard()
    )
    await callback.answer()

async def profile_back(callback: types.CallbackQuery):
    """Возврат из личного кабинета в главное меню"""
    await callback.message.edit_text(
        "Возвращаемся в главное меню...",
        reply_markup=None
    )
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_menu()
    )
    await callback.answer()

# Админ функции для управления ставками
async def admin_view_bets(callback: types.CallbackQuery):
    """Админ: просмотр всех ставок на матч с деталями"""
    match_id = int(callback.data.split('_')[3])
    
    match = await db.get_match_by_id(match_id)
    if not match:
        await callback.answer("❌ Матч не найден!")
        return
    
    all_bets = await db.get_bets_by_match(match_id)
    tournament = await db.get_tournament_by_id(match['tournament_id'])
    
    if not all_bets:
        await callback.message.edit_text(
            f"👑 *Админ: Ставки на матч*\n\n"
            f"⚽ {match['team1']} vs {match['team2']}\n"
            f"🏆 {tournament['name'] if tournament else 'Неизвестно'}\n\n"
            "На этот матч пока нет ставок.",
            parse_mode="Markdown"
        )
    else:
        bets_text = (
            f"👑 *Админ: Все ставки на матч*\n\n"
            f"⚽ {match['team1']} vs {match['team2']}\n"
            f"🏆 {tournament['name'] if tournament else 'Неизвестно'}\n"
            f"📅 {match['match_date']} {match['match_time']}\n\n"
            f"📊 *Детали ставок ({len(all_bets)}):*\n\n"
        )
        
        for i, bet in enumerate(all_bets, 1):
            bets_text += (
                f"{i}. **{bet['full_name']}** (@{bet['username']})\n"
                f"   🎯 {bet['team1_score']}-{bet['team2_score']}\n"
                f"   ⏰ {bet['bet_date'][:16]}\n\n"
            )
        
        await callback.message.edit_text(
            bets_text,
            parse_mode="Markdown"
        )
    
    await callback.answer()

async def admin_clear_bets(callback: types.CallbackQuery):
    """Админ: очистка всех ставок на матч"""
    match_id = int(callback.data.split('_')[3])
    
    # Здесь можно добавить логику очистки ставок
    # Пока просто сообщение о функции
    await callback.message.edit_text(
        "👑 *Функция очистки ставок*\n\n"
        "Эта функция находится в разработке.\n"
        "В будущем здесь можно будет удалить все ставки на выбранный матч.",
        parse_mode="Markdown"
    )
    await callback.answer()

# Новые функции для списка игроков
async def show_all_players(callback: types.CallbackQuery):
    """Показать список всех игроков в турнирах"""
    user_id = callback.from_user.id
    
    # Получаем все активные турниры
    tournaments = await db.get_all_tournaments()
    if not tournaments:
        await callback.message.edit_text(
            "📭 *Список игроков*\n\n"
            "На данный момент нет активных турниров с участниками.",
            parse_mode="Markdown",
            reply_markup=get_bets_back_keyboard()
        )
        await callback.answer()
        return
    
    # Собираем всех участников из всех турниров
    all_players = []
    seen_players = set()
    
    for tournament in tournaments:
        participants = await db.get_tournament_participants(tournament['id'])
        for player in participants:
            if player['user_id'] not in seen_players:
                # Добавляем информацию о турнире к игроку
                player_with_tournament = player.copy()
                player_with_tournament['source_tournament_id'] = tournament['id']
                all_players.append(player_with_tournament)
                seen_players.add(player['user_id'])
    
    if not all_players:
        await callback.message.edit_text(
            "📭 *Список игроков*\n\n"
            "Пока нет участников в турнирах.",
            parse_mode="Markdown",
            reply_markup=get_bets_back_keyboard()
        )
        await callback.answer()
        return
    
    # Сортируем игроков по имени
    all_players.sort(key=lambda x: x['full_name'])
    
    # Используем tournament_id = 0 для обозначения "все турниры"
    await show_players_page(callback, all_players, 0, tournament_id=0)
    await callback.answer()

async def show_players_page(callback: types.CallbackQuery, players: list, page: int, tournament_id: int = 0):
    """Показать страницу со списком игроков"""
    ITEMS_PER_PAGE = 10
    total_pages = (len(players) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_players = players[start_idx:end_idx]
    
    if tournament_id == 0:
        page_text = (
            f"👥 *Все игроки турниров*\n\n"
            f"📊 Всего игроков: **{len(players)}**\n"
            f"📄 Страница **{page + 1}** из **{total_pages}**\n\n"
            "Выберите игрока для просмотра информации:"
        )
    else:
        tournament = await db.get_tournament_by_id(tournament_id)
        tournament_name = tournament['name'] if tournament else "Неизвестный турнир"
        page_text = (
            f"👥 *Игроки турнира: {tournament_name}*\n\n"
            f"📊 Всего игроков: **{len(players)}**\n"
            f"📄 Страница **{page + 1}** из **{total_pages}**\n\n"
            "Выберите игрока для просмотра информации:"
        )
    
    keyboard = get_player_list_keyboard(current_players, tournament_id, page, total_pages)
    
    await callback.message.edit_text(
        page_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def handle_players_pagination(callback: types.CallbackQuery):
    """Обработка пагинации списка игроков"""
    # callback_data format: players_page_tournamentId_pageNumber
    parts = callback.data.split('_')
    tournament_id = int(parts[2])
    page = int(parts[3])
    
    if tournament_id == 0:
        # Получаем всех участников из всех турниров
        tournaments = await db.get_all_tournaments()
        all_players = []
        seen_players = set()
        
        for tournament in tournaments:
            participants = await db.get_tournament_participants(tournament['id'])
            for player in participants:
                if player['user_id'] not in seen_players:
                    player_with_tournament = player.copy()
                    player_with_tournament['source_tournament_id'] = tournament['id']
                    all_players.append(player_with_tournament)
                    seen_players.add(player['user_id'])
        
        all_players.sort(key=lambda x: x['full_name'])
        await show_players_page(callback, all_players, page, tournament_id)
    else:
        # Получаем участников конкретного турнира
        participants = await db.get_tournament_participants(tournament_id)
        if not participants:
            await callback.answer("❌ Нет участников в турнире!")
            return
        
        await show_players_page(callback, participants, page, tournament_id)
    
    await callback.answer()

async def show_player_info(callback: types.CallbackQuery):
    """Показать информацию о выбранном игроке"""
    # callback_data format: player_info_tournamentId_userId_page
    parts = callback.data.split('_')
    tournament_id = int(parts[2])
    target_user_id = int(parts[3])
    current_page = int(parts[4])
    
    # Получаем информацию о игроке
    player_data = await db.get_user_by_id(target_user_id)
    if not player_data:
        await callback.answer("❌ Игрок не найден!")
        return
    
    # Получаем активные турниры игрока
    active_tournaments = await db.get_user_active_tournaments(target_user_id)
    
    # Используем HTML разметку
    player_info = (
        "👤 <b>Информация об игроке</b>\n\n"
        f"🔑 <b>Логин:</b> <code>{player_data['username']}</code>\n"
        f"👨‍💼 <b>Имя:</b> {player_data['full_name']}\n"
    )
    
    if player_data.get('tg_username'):
        player_info += f"🤖 <b>Telegram:</b> @{player_data['tg_username']}\n"
    
    player_info += f"\n🏆 <b>Участвует в турнирах</b> ({len(active_tournaments)}):\n"
    
    if active_tournaments:
        for i, tournament in enumerate(active_tournaments, 1):
            player_info += f"{i}. {tournament['name']}\n"
    else:
        player_info += "Пока не участвует в турнирах\n"
    
    keyboard = get_player_info_keyboard(tournament_id, target_user_id, current_page)
    
    await callback.message.edit_text(
        player_info,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

def get_player_list_keyboard(players: list, tournament_id: int, page: int, total_pages: int):
    """Клавиатура со списком игроков для текущей страницы"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопки для каждого игрока на текущей странице
    for player in players:
        btn_text = f"👤 {player['full_name']} (@{player['username']})"
        if len(btn_text) > 50:  # Ограничение длины текста кнопки
            btn_text = f"👤 {player['full_name'][:30]}... (@{player['username']})"
        
        btn = InlineKeyboardButton(
            btn_text, 
            callback_data=f'player_info_{tournament_id}_{player["user_id"]}_{page}'
        )
        keyboard.add(btn)
    
    # Добавляем пагинацию
    pagination_keyboard = get_tournament_players_keyboard(tournament_id, page, total_pages)
    if pagination_keyboard.inline_keyboard:
        keyboard.row(*pagination_keyboard.inline_keyboard[0])  # Добавляем кнопки пагинации
        if len(pagination_keyboard.inline_keyboard) > 1:
            for row in pagination_keyboard.inline_keyboard[1:]:
                keyboard.add(*row)  # Добавляем остальные кнопки
    
    return keyboard

def get_tournament_players_keyboard(tournament_id: int, page: int = 0, total_pages: int = 1):
    """Клавиатура для списка игроков турнира с пагинация"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        prev_btn = InlineKeyboardButton('◀️ Назад', callback_data=f'players_page_{tournament_id}_{page-1}')
        nav_buttons.append(prev_btn)
    
    page_info = InlineKeyboardButton(f'{page+1}/{total_pages}', callback_data='current_page')
    nav_buttons.append(page_info)
    
    if page < total_pages - 1:
        next_btn = InlineKeyboardButton('Вперед ▶️', callback_data=f'players_page_{tournament_id}_{page+1}')
        nav_buttons.append(next_btn)
    
    if nav_buttons:
        keyboard.row(*nav_buttons)
    
    back_btn = InlineKeyboardButton('🔙 Назад к турнирам', callback_data='user_tournaments_back')
    keyboard.add(back_btn)
    
    return keyboard

def get_player_info_keyboard(tournament_id: int, user_id: int, current_page: int = 0):
    """Клавиатура для информации о игроке"""
    keyboard = InlineKeyboardMarkup()
    
    back_to_players_btn = InlineKeyboardButton(
        '🔙 Назад к списку', 
        callback_data=f'players_page_{tournament_id}_{current_page}'
    )
    tournaments_back_btn = InlineKeyboardButton('🔙 В личный кабинет', callback_data='user_tournaments_back')
    
    keyboard.add(back_to_players_btn)
    keyboard.add(tournaments_back_btn)
    
    return keyboard

def register_handlers_bets(dp: Dispatcher):
    """Регистрация обработчиков ставок"""
    
    # Обработчик просмотра матча и ставок
    dp.register_callback_query_handler(show_match_details, lambda c: c.data.startswith('match_'))
    
    # Обработчики создания ставок
    dp.register_callback_query_handler(process_bet, lambda c: c.data.startswith('bet_'))
    dp.register_callback_query_handler(confirm_bet, lambda c: c.data.startswith('confirm_bet_'))
    dp.register_callback_query_handler(cancel_bet, lambda c: c.data.startswith('cancel_bet_'))
    
    # Обработчики личного кабинета и ставок
    dp.register_callback_query_handler(show_user_tournaments, lambda c: c.data == 'user_tournaments')
    dp.register_callback_query_handler(show_my_bets, lambda c: c.data == 'my_bets')
    dp.register_callback_query_handler(show_bets_by_tournament, lambda c: c.data.startswith('bets_tournament_'))
    dp.register_callback_query_handler(view_bet_details, lambda c: c.data.startswith('view_bet_'))
    dp.register_callback_query_handler(edit_bet, lambda c: c.data.startswith('edit_bet_'))
    dp.register_callback_query_handler(delete_bet, lambda c: c.data.startswith('delete_bet_'))
    dp.register_callback_query_handler(view_match_bets, lambda c: c.data.startswith('view_bets_'))
    
    # Обработчики навигации
    dp.register_callback_query_handler(user_tournaments_back, lambda c: c.data == 'user_tournaments_back')
    dp.register_callback_query_handler(profile_back, lambda c: c.data == 'profile_back')
    dp.register_callback_query_handler(back_to_tournament, lambda c: c.data.startswith('tournament_back_'))
    
    # Обработчики списка игроков
    dp.register_callback_query_handler(show_all_players, lambda c: c.data == 'all_players')
    dp.register_callback_query_handler(show_player_info, lambda c: c.data.startswith('player_info_'))
    dp.register_callback_query_handler(handle_players_pagination, lambda c: c.data.startswith('players_page_'))
    
    # Админ обработчики
    dp.register_callback_query_handler(admin_view_bets, lambda c: c.data.startswith('admin_view_bets_'))
    dp.register_callback_query_handler(admin_clear_bets, lambda c: c.data.startswith('admin_clear_bets_'))