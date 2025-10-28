from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import db
from config_bot import config
from keyboards import (
    get_tournaments_keyboard, 
    get_tournaments_list_keyboard, 
    get_tournament_manage_keyboard, 
    get_tournaments_manage_list_keyboard,
    get_back_keyboard, 
    get_cancel_keyboard, 
    get_main_menu,
    get_tournament_matches_keyboard,
    get_tournament_participation_keyboard,
    get_tournament_rules_keyboard,
    get_tournament_edit_rules_keyboard
)

class TournamentStates(StatesGroup):
    """Состояния для управления турнирами"""
    waiting_for_tournament_name = State()
    waiting_for_tournament_description = State()
    waiting_for_tournament_rules = State()
    waiting_for_tournament_edit_name = State()
    waiting_for_tournament_edit_description = State()
    waiting_for_tournament_edit_rules = State()

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id == config.ADMIN_ID

async def show_tournaments(message: types.Message):
    """Показать меню турниров"""
    user_id = message.from_user.id
    
    # Проверяем авторизацию
    if not await db.user_exists_by_tg_id(user_id):
        await message.answer(
            "❌ Для просмотра турниров необходимо авторизоваться!\n\n"
            "Войдите в систему или зарегистрируйтесь.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return
    
    # Проверяем бан
    if await db.is_user_banned(user_id):
        await message.answer(
            "🚫 Ваш аккаунт заблокирован!\n"
            "Доступ к турнирам ограничен.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return
    
    admin_status = is_admin(user_id)
    tournaments_count = await db.get_tournaments_count()
    
    await message.answer(
        "⚽ *Футбольные турниры*\n\n"
        "Здесь вы можете просматривать доступные турниры по футболу, "
        "участвовать в них и делать ставки на матчи.\n\n"
        f"📊 Активных турниров: **{tournaments_count}**",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await message.answer(
        "Выберите действие:",
        reply_markup=get_tournaments_keyboard(admin_status)
    )

async def show_tournaments_list(callback: types.CallbackQuery):
    """Показать список турниров"""
    user_id = callback.from_user.id
    
    # Проверяем авторизацию
    if not await db.user_exists_by_tg_id(user_id):
        await callback.answer("❌ Необходима авторизация!")
        return
    
    tournaments = await db.get_all_tournaments()
    admin_status = is_admin(user_id)
    
    if not tournaments:
        await callback.message.edit_text(
            "📭 На данный момент нет активных турниров.\n\n"
            "Следите за обновлениями! Новые турниры появятся скоро.",
            reply_markup=get_tournaments_keyboard(admin_status)
        )
    else:
        # Используем простой текст без разметки
        tournaments_text = "📋 Список турниров:\n\n"
        for i, tournament in enumerate(tournaments, 1):
            # Получаем количество матчей в турнире
            matches_count = await db.get_matches_count_by_tournament(tournament['id'])
            
            description = tournament.get('description', 'Описание отсутствует')
            created_by = tournament.get('created_by_username', 'Админ')
            
            tournaments_text += (
                f"{i}. {tournament['name']}\n"
                f"   📝 {description}\n"
                f"   👤 Создал: {created_by}\n"
                f"   🔢 Матчей: {matches_count}\n"
                f"   📅 {tournament['created_date'][:10]}\n\n"
            )
        
        await callback.message.edit_text(
            tournaments_text,
            parse_mode=None,  # Без разметки
            reply_markup=get_tournaments_list_keyboard(tournaments, admin_status)
        )
    
    await callback.answer()

async def show_tournament_detail(callback: types.CallbackQuery):
    """Показать детали турнира и предложить участие"""
    tournament_id = int(callback.data.split('_')[2])
    tournament = await db.get_tournament_by_id(tournament_id)
    
    if not tournament:
        await callback.answer("❌ Турнир не найден!")
        return
    
    user_id = callback.from_user.id
    is_admin_user = is_admin(user_id)
    
    # Для администратора сразу показываем матчи
    if is_admin_user:
        await show_tournament_matches(callback, tournament_id)
        return
    
    # Проверяем, участвует ли уже пользователь в турнире
    is_participating = await db.is_user_participating(user_id, tournament_id)
    
    if is_participating:
        # Пользователь уже участвует - показываем матчи
        await show_tournament_matches(callback, tournament_id)
    else:
        # Предлагаем участие в турнире
        matches_count = await db.get_matches_count_by_tournament(tournament_id)
        
        tournament_text = (
            f"⚽ *{tournament['name']}*\n\n"
            f"📝 *Описание:* {tournament.get('description', 'Отсутствует')}\n"
            f"🔢 *Матчей в турнире:* {matches_count}\n\n"
            "❓ *Вы готовы принять участие в этом турнире?*\n\n"
            "После подтверждения участия вы сможете:\n"
            "• Просматривать матчи турнира\n"
            "• Делать ставки на результаты\n"
            "• Участвовать в тотализаторе\n"
            "• Следить за своей статистикой\n\n"
            "Выберите действие:"
        )
        
        keyboard = get_tournament_participation_keyboard(tournament_id)
        
        await callback.message.edit_text(
            tournament_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    await callback.answer()

async def show_tournament_matches(callback: types.CallbackQuery, tournament_id: int = None):
    """Показать матчи турнира"""
    if not tournament_id:
        tournament_id = int(callback.data.split('_')[2])
    
    tournament = await db.get_tournament_by_id(tournament_id)
    
    if not tournament:
        await callback.answer("❌ Турнир не найден!")
        return
    
    # Получаем ВСЕ матчи турнира
    all_matches = await db.get_matches_by_tournament(tournament_id)
    is_admin_user = is_admin(callback.from_user.id)
    user_id = callback.from_user.id
    
    # Для администратора показываем ВСЕ матчи
    if is_admin_user:
        matches_to_show = all_matches
        matches_with_bets = []
    else:
        # Для обычного пользователя фильтруем матчи
        matches_to_show = []
        matches_with_bets = []
        
        for match in all_matches:
            user_bet = await db.get_match_bet(user_id, match['id'])
            if not user_bet:
                matches_to_show.append(match)
            else:
                matches_with_bets.append(match)
    
    # Формируем текст сообщения
    tournament_text = (
        f"⚽ *{tournament['name']}*\n\n"
        f"📝 *Описание:* {tournament.get('description', 'Отсутствует')}\n"
    )
    
    if is_admin_user:
        tournament_text += f"🔢 *Всего матчей:* {len(all_matches)}\n\n"
        if all_matches:
            tournament_text += "📋 *Все матчи турнира:*\n\n"
            for i, match in enumerate(all_matches, 1):
                # Для админа показываем дополнительную информацию
                bets_count = len(await db.get_bets_by_match(match['id']))
                tournament_text += f"{i}. {match['match_date']} {match['match_time']} {match['team1']} - {match['team2']} (ставок: {bets_count})\n"
    else:
        tournament_text += (
            f"🔢 *Всего матчей в турнире:* {len(all_matches)}\n"
            f"🎯 *Доступно для ставок:* {len(matches_to_show)}\n"
            f"✅ *Ставок сделано:* {len(matches_with_bets)}\n\n"
        )
        
        if matches_to_show:
            tournament_text += "📋 *Матчи для ставок:*\n\n"
            for i, match in enumerate(matches_to_show, 1):
                tournament_text += f"{i}. {match['match_date']} {match['match_time']} {match['team1']} - {match['team2']}\n"
        else:
            tournament_text += "🎉 *Поздравляем!*\n\n"
            tournament_text += "Вы сделали ставки на все матчи этого турнира! 🏆\n"
            tournament_text += "Следите за результатами в личном кабинете.\n\n"
            tournament_text += f"✅ Вы сделали ставки на {len(matches_with_bets)} матчей"
    
    # Для админа передаем все матчи, для пользователя - только доступные
    keyboard = get_tournament_matches_keyboard(
        all_matches if is_admin_user else matches_to_show, 
        tournament_id, 
        is_admin_user
    )
    
    await callback.message.edit_text(
        tournament_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()

async def participate_tournament(callback: types.CallbackQuery):
    """Пользователь соглашается участвовать в турнире"""
    tournament_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    
    # Сохраняем участие пользователя
    success = await db.add_tournament_participant(user_id, tournament_id, True)
    
    if success:
        await callback.answer("✅ Вы успешно присоединились к турниру!")
        await show_tournament_matches(callback, tournament_id)
    else:
        await callback.answer("❌ Ошибка при присоединении к турниру!")

async def decline_tournament(callback: types.CallbackQuery):
    """Пользователь отказывается от участия в турнире"""
    tournament_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    
    # Сохраняем отказ пользователя
    success = await db.add_tournament_participant(user_id, tournament_id, False)
    
    if success:
        await callback.answer("❌ Вы отказались от участия в турнире")
        await show_tournaments_list(callback)
    else:
        await callback.answer("❌ Ошибка при обработке отказа!")

async def show_tournament_rules(callback: types.CallbackQuery):
    """Показать правила турнира"""
    tournament_id = int(callback.data.split('_')[2])
    tournament = await db.get_tournament_by_id(tournament_id)
    
    if not tournament:
        await callback.answer("❌ Турнир не найден!")
        return
    
    rules = tournament.get('rules', 'Правила турнира еще не установлены.')
    is_admin_user = is_admin(callback.from_user.id)
    
    rules_text = (
        f"⚽ *{tournament['name']}*\n\n"
        f"📋 *Правила турнира:*\n\n{rules}"
    )
    
    keyboard = get_tournament_rules_keyboard(tournament_id, is_admin_user)
    
    await callback.message.edit_text(
        rules_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()

async def edit_tournament_rules(callback: types.CallbackQuery, state: FSMContext):
    """Редактирование правил турнира"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    tournament_id = int(callback.data.split('_')[2])
    tournament = await db.get_tournament_by_id(tournament_id)
    
    if not tournament:
        await callback.answer("❌ Турнир не найден!")
        return
    
    await state.update_data(tournament_id=tournament_id)
    
    current_rules = tournament.get('rules', '')
    
    await callback.message.edit_text(
        f"✏️ *Редактирование правил турнира: {tournament['name']}*\n\n"
        f"Текущие правила:\n{current_rules}\n\n"
        "Введите новые правила турнира:",
        parse_mode="Markdown"
    )
    
    await TournamentStates.waiting_for_tournament_edit_rules.set()
    await callback.answer()

async def process_tournament_edit_rules(message: types.Message, state: FSMContext):
    """Обработка ввода новых правил турнира"""
    new_rules = message.text.strip()
    
    if len(new_rules) < 10:
        await message.answer(
            "❌ Правила турнира слишком короткие!\n"
            "Минимальная длина - 10 символов.\n\n"
            "Введите правила еще раз:"
        )
        return
    
    user_data = await state.get_data()
    tournament_id = user_data.get('tournament_id')
    
    # Обновляем правила турнира
    success = await db.update_tournament_rules(tournament_id, new_rules)
    
    if success:
        await message.answer(
            "✅ Правила турнира успешно обновлены!",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            "❌ Ошибка при обновлении правил турнира!",
            reply_markup=get_main_menu()
        )
    
    await state.finish()

async def tournament_add(callback: types.CallbackQuery):
    """Добавление нового турнира"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    await callback.message.edit_text(
        "➕ *Добавление нового турнира*\n\n"
        "Введите название турнира:\n\n"
        "Пример: *Чемпионат мира по футболу 2024*",
        parse_mode="Markdown"
    )
    
    await TournamentStates.waiting_for_tournament_name.set()
    await callback.answer()

async def process_tournament_name(message: types.Message, state: FSMContext):
    """Обработка ввода названия турнира"""
    if message.text == "❌ Отмена":
        await state.finish()
        await message.answer(
            "Добавление турнира отменено.",
            reply_markup=get_main_menu()
        )
        return
    
    tournament_name = message.text.strip()
    
    if len(tournament_name) < 3:
        await message.answer(
            "❌ Название турнира слишком короткое!\n"
            "Минимальная длина - 3 символа.\n\n"
            "Введите название еще раз:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(tournament_name=tournament_name)
    
    await message.answer(
        "✅ Название принято!\n\n"
        "Теперь введите описание турнира (необязательно):\n\n"
        "Или нажмите 'Пропустить' чтобы оставить без описания",
        reply_markup=get_back_keyboard()
    )
    
    await TournamentStates.waiting_for_tournament_description.set()

async def process_tournament_description(message: types.Message, state: FSMContext):
    """Обработка ввода описания турнира"""
    if message.text == "🔙 Назад":
        await message.answer(
            "Введите название турнира:",
            reply_markup=get_cancel_keyboard()
        )
        await TournamentStates.waiting_for_tournament_name.set()
        return
    
    tournament_description = message.text.strip()
    user_data = await state.get_data()
    tournament_name = user_data.get('tournament_name')
    
    await state.update_data(tournament_description=tournament_description)
    
    await message.answer(
        "✅ Описание принято!\n\n"
        "Теперь введите правила турнира:\n\n"
        "Опишите основные правила, условия участия и систему начисления очков.",
        reply_markup=get_back_keyboard()
    )
    
    await TournamentStates.waiting_for_tournament_rules.set()

async def process_tournament_rules(message: types.Message, state: FSMContext):
    """Обработка ввода правил турнира"""
    if message.text == "🔙 Назад":
        await message.answer(
            "Введите описание турнира:",
            reply_markup=get_back_keyboard()
        )
        await TournamentStates.waiting_for_tournament_description.set()
        return
    
    tournament_rules = message.text.strip()
    user_data = await state.get_data()
    tournament_name = user_data.get('tournament_name')
    tournament_description = user_data.get('tournament_description')
    
    if len(tournament_rules) < 10:
        await message.answer(
            "❌ Правила турнира слишком короткие!\n"
            "Минимальная длина - 10 символов.\n\n"
            "Введите правила еще раз:",
            reply_markup=get_back_keyboard()
        )
        return
    
    # Добавляем турнир в базу
    success = await db.add_tournament(
        name=tournament_name,
        description=tournament_description if tournament_description != "Пропустить" else "",
        rules=tournament_rules,
        created_by=message.from_user.id
    )
    
    if success:
        await message.answer(
            f"✅ Турнир *{tournament_name}* успешно добавлен!",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            "❌ Ошибка при добавлении турнира!",
            reply_markup=get_main_menu()
        )
    
    await state.finish()

async def tournaments_manage(callback: types.CallbackQuery):
    """Управление турнирами (админ)"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    tournaments = await db.get_all_tournaments()
    
    if not tournaments:
        await callback.message.edit_text(
            "🛠 *Управление турнирами*\n\n"
            "На данный момент нет активных турниров для управления.",
            parse_mode="Markdown",
            reply_markup=get_tournaments_manage_list_keyboard(tournaments)
        )
    else:
        await callback.message.edit_text(
            "🛠 *Управление турнирами*\n\n"
            "Выберите турнир для управления:",
            parse_mode="Markdown",
            reply_markup=get_tournaments_manage_list_keyboard(tournaments)
        )
    
    await callback.answer()

async def tournament_manage_detail(callback: types.CallbackQuery):
    """Управление конкретным турниром"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    tournament_id = int(callback.data.split('_')[2])
    tournament = await db.get_tournament_by_id(tournament_id)
    
    if not tournament:
        await callback.answer("❌ Турнир не найден!")
        return
    
    # Получаем количество матчей в турнире
    matches_count = await db.get_matches_count_by_tournament(tournament_id)
    
    # Без разметки
    tournament_text = (
        f"🛠 Управление турниром:\n\n"
        f"⚽ Название: {tournament['name']}\n"
        f"📝 Описание: {tournament.get('description', 'Отсутствует')}\n"
        f"👤 Создатель: {tournament.get('created_by_username', 'Админ')}\n"
        f"📅 Дата создания: {tournament['created_date'][:16]}\n"
        f"🔢 Матчей в турнире: {matches_count}\n\n"
        "Выберите действие:"
    )
    
    # Создаем клавиатуру с кнопкой управления матчами
    keyboard = get_tournament_manage_keyboard(tournament_id)
    
    await callback.message.edit_text(
        tournament_text,
        parse_mode=None,  # Без разметки
        reply_markup=keyboard
    )
    await callback.answer()

async def tournament_edit(callback: types.CallbackQuery, state: FSMContext):
    """Редактирование турнира"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    tournament_id = int(callback.data.split('_')[2])
    tournament = await db.get_tournament_by_id(tournament_id)
    
    if not tournament:
        await callback.answer("❌ Турнир не найден!")
        return
    
    await state.update_data(tournament_id=tournament_id)
    
    await callback.message.edit_text(
        f"✏️ *Редактирование турнира*\n\n"
        f"Текущее название: *{tournament['name']}*\n"
        f"Текущее описание: {tournament.get('description', 'Отсутствует')}\n\n"
        "Введите новое название турнира:",
        parse_mode="Markdown"
    )
    
    await TournamentStates.waiting_for_tournament_edit_name.set()
    await callback.answer()

async def process_tournament_edit_name(message: types.Message, state: FSMContext):
    """Обработка ввода нового названия турнира"""
    new_name = message.text.strip()
    
    if len(new_name) < 3:
        await message.answer(
            "❌ Название турнира слишком короткое!\n"
            "Минимальная длина - 3 символа.\n\n"
            "Введите название еще раз:"
        )
        return
    
    await state.update_data(new_name=new_name)
    
    await message.answer(
        "✅ Новое название принято!\n\n"
        "Теперь введите новое описание турнира:"
    )
    
    await TournamentStates.waiting_for_tournament_edit_description.set()

async def process_tournament_edit_description(message: types.Message, state: FSMContext):
    """Обработка ввода нового описания турнира"""
    new_description = message.text.strip()
    user_data = await state.get_data()
    tournament_id = user_data.get('tournament_id')
    new_name = user_data.get('new_name')
    
    # Получаем текущие правила турнира
    tournament = await db.get_tournament_by_id(tournament_id)
    current_rules = tournament.get('rules', '')
    
    # Обновляем турнир
    success = await db.update_tournament(tournament_id, new_name, new_description, current_rules)
    
    if success:
        await message.answer(
            f"✅ Турнир успешно обновлен!\n"
            f"Новое название: *{new_name}*",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            "❌ Ошибка при обновлении турнира!",
            reply_markup=get_main_menu()
        )
    
    await state.finish()

async def tournament_delete(callback: types.CallbackQuery):
    """Удаление турнира"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    tournament_id = int(callback.data.split('_')[2])
    tournament = await db.get_tournament_by_id(tournament_id)
    
    if not tournament:
        await callback.answer("❌ Турнир не найден!")
        return
    
    # Удаляем турнир
    success = await db.delete_tournament(tournament_id)
    
    if success:
        await callback.message.edit_text(
            f"✅ Турнир *{tournament['name']}* успешно удален!",
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка при удалении турнира!",
            parse_mode="Markdown"
        )
    
    await callback.answer()

async def handle_all_back_buttons(callback: types.CallbackQuery):
    """Универсальный обработчик кнопок Назад"""
    user_id = callback.from_user.id
    
    # Немедленно отвечаем на callback чтобы убрать "часики"
    await callback.answer()
    
    try:
        if callback.data == 'tournaments_back':
            admin_status = is_admin(user_id)
            
            await callback.message.delete()
            await callback.message.answer(
                "⚽ Футбольные турниры\n\n"
                "Выберите действие:",
                parse_mode=None,
                reply_markup=get_tournaments_keyboard(admin_status)
            )
            return
        
        elif callback.data == 'tournaments_manage_back':
            if not is_admin(user_id):
                await callback.answer("❌ Недостаточно прав!")
                return
            
            tournaments = await db.get_all_tournaments()
            
            await callback.message.delete()
            await callback.message.answer(
                "🛠 Управление турнирами\n\n"
                "Выберите турнир для управления:",
                parse_mode=None,
                reply_markup=get_tournaments_manage_list_keyboard(tournaments)
            )
            return
        
        elif callback.data == 'back_to_main':
            from keyboards import get_main_menu
            await callback.message.delete()
            await callback.message.answer(
                "Главное меню:",
                reply_markup=get_main_menu()
            )
            return
        
        elif callback.data == 'admin_back':
            from handlers.admin import show_admin_panel
            await show_admin_panel(callback)
            return
        
    except Exception as e:
        await callback.message.answer("❌ Произошла ошибка. Попробуйте снова.")

def register_handlers_tournaments(dp: Dispatcher):
    """Регистрация обработчиков турниров"""
    
    # Обработчик кнопки "Турниры" из главного меню
    dp.register_message_handler(
        show_tournaments, 
        lambda message: message.text == "⚽ Турниры",
        state="*"
    )
    
    # Основные callback-обработчики
    dp.register_callback_query_handler(show_tournaments_list, lambda c: c.data == 'tournaments_list')
    dp.register_callback_query_handler(tournament_add, lambda c: c.data == 'tournament_add')
    dp.register_callback_query_handler(tournaments_manage, lambda c: c.data == 'tournaments_manage')
    
    # УНИВЕРСАЛЬНЫЙ обработчик всех кнопок "Назад"
    dp.register_callback_query_handler(
        handle_all_back_buttons, 
        lambda c: c.data in [
            'tournaments_back', 
            'tournaments_manage_back', 
            'back_to_main',
            'admin_back'
        ]
    )
    
    # Обработчики просмотра турниров и матчей
    dp.register_callback_query_handler(show_tournament_detail, lambda c: c.data.startswith('tournament_matches_'))
    dp.register_callback_query_handler(show_tournament_rules, lambda c: c.data.startswith('tournament_rules_'))
    
    # Обработчики участия в турнирах
    dp.register_callback_query_handler(participate_tournament, lambda c: c.data.startswith('participate_'))
    dp.register_callback_query_handler(decline_tournament, lambda c: c.data.startswith('decline_'))
    
    # Обработчики управления турнирами (админ)
    dp.register_callback_query_handler(tournament_manage_detail, lambda c: c.data.startswith('tournament_manage_'))
    dp.register_callback_query_handler(tournament_edit, lambda c: c.data.startswith('tournament_edit_'))
    dp.register_callback_query_handler(tournament_delete, lambda c: c.data.startswith('tournament_delete_'))
    dp.register_callback_query_handler(edit_tournament_rules, lambda c: c.data.startswith('edit_rules_'))
    
    # Обработчики состояний создания/редактирования турниров
    dp.register_message_handler(process_tournament_name, state=TournamentStates.waiting_for_tournament_name)
    dp.register_message_handler(process_tournament_description, state=TournamentStates.waiting_for_tournament_description)
    dp.register_message_handler(process_tournament_rules, state=TournamentStates.waiting_for_tournament_rules)
    dp.register_message_handler(process_tournament_edit_name, state=TournamentStates.waiting_for_tournament_edit_name)
    dp.register_message_handler(process_tournament_edit_description, state=TournamentStates.waiting_for_tournament_edit_description)
    dp.register_message_handler(process_tournament_edit_rules, state=TournamentStates.waiting_for_tournament_edit_rules)