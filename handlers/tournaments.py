from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from database import db
from config_bot import config
from keyboards import (get_tournaments_keyboard, get_tournaments_list_keyboard, 
                      get_tournament_manage_keyboard, get_tournaments_manage_list_keyboard,
                      get_back_keyboard, get_cancel_keyboard, get_main_menu)

class TournamentStates(StatesGroup):
    """Состояния для управления турнирами"""
    waiting_for_tournament_name = State()
    waiting_for_tournament_description = State()
    waiting_for_tournament_edit_name = State()
    waiting_for_tournament_edit_description = State()

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
    await message.answer(
        "⚽ *Футбольные турниры*\n\n"
        "Здесь вы можете просматривать доступные турниры по футболу.\n\n"
        f"📊 Активных турниров: {await db.get_tournaments_count()}",
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
            "Следите за обновлениями!",
            reply_markup=get_tournaments_keyboard(admin_status)
        )
    else:
        tournaments_text = "📋 *Список турниров:*\n\n"
        for i, tournament in enumerate(tournaments, 1):
            tournaments_text += (
                f"{i}. *{tournament['name']}*\n"
                f"   📝 {tournament.get('description', 'Описание отсутствует')}\n"
                f"   👤 Создал: {tournament.get('created_by_username', 'Админ')}\n"
                f"   📅 {tournament['created_date'][:10]}\n\n"
            )
        
        await callback.message.edit_text(
            tournaments_text,
            parse_mode="Markdown",
            reply_markup=get_tournaments_list_keyboard(tournaments, admin_status)
        )
    
    await callback.answer()

async def show_tournament_detail(callback: types.CallbackQuery):
    """Показать детали турнира и список матчей"""
    tournament_id = int(callback.data.split('_')[2])
    tournament = await db.get_tournament_by_id(tournament_id)
    
    if not tournament:
        await callback.answer("❌ Турнир не найден!")
        return
    
    # Получаем матчи турнира
    matches = await db.get_matches_by_tournament(tournament_id)
    is_admin = callback.from_user.id == config.ADMIN_ID
    
    # Формируем текст сообщения
    tournament_text = (
        f"⚽ *{tournament['name']}*\n\n"
        f"📝 *Описание:* {tournament.get('description', 'Отсутствует')}\n"
        f"👤 *Создатель:* {tournament.get('created_by_username', 'Админ')}\n"
        f"📅 *Дата создания:* {tournament['created_date'][:10]}\n"
        f"🔢 *Количество матчей:* {len(matches)}\n\n"
    )
    
    if matches:
        tournament_text += "📋 *Список матчей:*\n\n"
        for i, match in enumerate(matches, 1):
            tournament_text += f"{i}. {match['match_date']} {match['match_time']} {match['team1']} - {match['team2']}\n"
    else:
        tournament_text += "📭 В этом турнире пока нет матчей.\n"
    
    # Создаем клавиатуру с матчами (только для просмотра)
    from keyboards import get_tournament_matches_keyboard
    keyboard = get_tournament_matches_keyboard(matches, tournament_id, is_admin)
    
    await callback.message.edit_text(
        tournament_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()

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
    
    # Добавляем турнир в базу
    success = await db.add_tournament(
        name=tournament_name,
        description=tournament_description if tournament_description != "Пропустить" else "",
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
    
    tournament_text = (
        f"🛠 *Управление турниром:*\n\n"
        f"⚽ *Название:* {tournament['name']}\n"
        f"📝 *Описание:* {tournament.get('description', 'Отсутствует')}\n"
        f"👤 *Создатель:* {tournament.get('created_by_username', 'Админ')}\n"
        f"📅 *Дата создания:* {tournament['created_date'][:16]}\n\n"
        "Выберите действие:"
    )
    
    await callback.message.edit_text(
        tournament_text,
        parse_mode="Markdown",
        reply_markup=get_tournament_manage_keyboard(tournament_id)
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
    
    # Обновляем турнир
    success = await db.update_tournament(tournament_id, new_name, new_description)
    
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

async def tournaments_back(callback: types.CallbackQuery):
    """Возврат к меню турниров"""
    user_id = callback.from_user.id
    admin_status = is_admin(user_id)
    
    await callback.message.edit_text(
        "⚽ *Футбольные турниры*\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=get_tournaments_keyboard(admin_status)
    )
    await callback.answer()

async def tournaments_manage_back(callback: types.CallbackQuery):
    """Возврат к управлению турнирами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    tournaments = await db.get_all_tournaments()
    
    await callback.message.edit_text(
        "🛠 *Управление турнирами*\n\n"
        "Выберите турнир для управления:",
        parse_mode="Markdown",
        reply_markup=get_tournaments_manage_list_keyboard(tournaments)
    )
    await callback.answer()

def register_handlers_tournaments(dp: Dispatcher):
    """Регистрация обработчиков турниров"""
    # Обработчик кнопки "Турниры"
    dp.register_message_handler(
        show_tournaments, 
        lambda message: message.text == "⚽ Турниры",
        state="*"
    )
    
    # Обработчики callback-кнопок
    dp.register_callback_query_handler(show_tournaments_list, lambda c: c.data == 'tournaments_list')
    dp.register_callback_query_handler(tournament_add, lambda c: c.data == 'tournament_add')
    dp.register_callback_query_handler(tournaments_manage, lambda c: c.data == 'tournaments_manage')
    dp.register_callback_query_handler(tournaments_back, lambda c: c.data == 'tournaments_back')
    dp.register_callback_query_handler(tournaments_manage_back, lambda c: c.data == 'tournaments_manage_back')
    
    # Обработчик для просмотра матчей турнира (заменяет старый show_tournament_detail)
    dp.register_callback_query_handler(show_tournament_detail, lambda c: c.data.startswith('tournament_matches_'))
    
    dp.register_callback_query_handler(tournament_manage_detail, lambda c: c.data.startswith('tournament_manage_'))
    dp.register_callback_query_handler(tournament_edit, lambda c: c.data.startswith('tournament_edit_'))
    dp.register_callback_query_handler(tournament_delete, lambda c: c.data.startswith('tournament_delete_'))
    
    # Обработчики состояний
    dp.register_message_handler(process_tournament_name, state=TournamentStates.waiting_for_tournament_name)
    dp.register_message_handler(process_tournament_description, state=TournamentStates.waiting_for_tournament_description)
    dp.register_message_handler(process_tournament_edit_name, state=TournamentStates.waiting_for_tournament_edit_name)
    dp.register_message_handler(process_tournament_edit_description, state=TournamentStates.waiting_for_tournament_edit_description)