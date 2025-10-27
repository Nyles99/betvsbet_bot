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
    get_profile_keyboard
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
        
        # Получаем все матчи турнира
        tournament_matches = await db.get_matches_by_tournament(match['tournament_id'])
        
        # Находим матчи, на которые пользователь еще не сделал ставки
        matches_without_bets = []
        for tournament_match in tournament_matches:
            user_bet = await db.get_match_bet(user_id, tournament_match['id'])
            if not user_bet and tournament_match['id'] != match_id:  # Исключаем текущий матч
                matches_without_bets.append(tournament_match)
        
        if matches_without_bets:
            # Есть матчи без ставок - показываем следующий матч
            next_match = matches_without_bets[0]
            await show_match_after_bet(callback, next_match['id'])
        else:
            # Все ставки сделаны - показываем сообщение
            await callback.message.answer(
                f"🎉 *Поздравляем!*\n\n"
                f"Вы сделали прогнозы на все матчи турнира:\n"
                f"**{tournament['name']}**\n\n"
                f"📊 Всего матчей: {len(tournament_matches)}\n"
                f"✅ Ваших прогнозов: {len(tournament_matches)}\n\n"
                "Следите за результатами в личном кабинете!",
                parse_mode="Markdown",
                reply_markup=get_back_to_tournament_keyboard(match['tournament_id'])
            )
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
        reply_markup=get_user_tournaments_keyboard()
    )
    await callback.answer()

async def show_my_bets(callback: types.CallbackQuery):
    """Показать все ставки пользователя"""
    user_id = callback.from_user.id
    user_bets = await db.get_user_bets(user_id)
    
    if not user_bets:
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
        # Группируем ставки по турнирам
        tournaments_bets = {}
        for bet in user_bets:
            tournament_name = bet['tournament_name']
            if tournament_name not in tournaments_bets:
                tournaments_bets[tournament_name] = []
            tournaments_bets[tournament_name].append(bet)
        
        bets_text = "📊 *Ваши ставки по турнирам:*\n\n"
        
        for tournament_name, bets in tournaments_bets.items():
            bets_text += f"🏆 *{tournament_name}* ({len(bets)} ставок):\n"
            
            for i, bet in enumerate(bets, 1):
                bets_text += (
                    f"  {i}. {bet['team1']} vs {bet['team2']}\n"
                    f"      🎯 {bet['team1_score']}-{bet['team2_score']}\n"
                    f"      📅 {bet['match_date']} {bet['match_time']}\n"
                )
            
            bets_text += "\n"
        
        bets_text += f"📈 Всего ставок: **{len(user_bets)}**"
        
        await callback.message.edit_text(
            bets_text,
            parse_mode="Markdown",
            reply_markup=get_bets_back_keyboard()
        )
    
    await callback.answer()

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
    dp.register_callback_query_handler(view_bet_details, lambda c: c.data.startswith('view_bet_'))
    dp.register_callback_query_handler(edit_bet, lambda c: c.data.startswith('edit_bet_'))
    dp.register_callback_query_handler(delete_bet, lambda c: c.data.startswith('delete_bet_'))
    dp.register_callback_query_handler(view_match_bets, lambda c: c.data.startswith('view_bets_'))
    
    # Обработчики навигации
    dp.register_callback_query_handler(user_tournaments_back, lambda c: c.data == 'user_tournaments_back')
    dp.register_callback_query_handler(profile_back, lambda c: c.data == 'profile_back')
    dp.register_callback_query_handler(back_to_tournament, lambda c: c.data.startswith('tournament_back_'))
    
    # Админ обработчики
    dp.register_callback_query_handler(admin_view_bets, lambda c: c.data.startswith('admin_view_bets_'))
    dp.register_callback_query_handler(admin_clear_bets, lambda c: c.data.startswith('admin_clear_bets_'))