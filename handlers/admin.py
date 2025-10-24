from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite
import logging

from database import db
from config_bot import config
from keyboards import get_main_menu

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния для админ-панели
from aiogram.dispatcher.filters.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_for_ban_user = State()
    waiting_for_unban_user = State()
    waiting_for_user_search = State()

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id == config.ADMIN_ID

async def check_admin_access(message: types.Message) -> bool:
    """Проверка доступа к админ-панели"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели!")
        return False
    return True

async def cmd_admin(message: types.Message):
    """Команда для открытия админ-панели"""
    if not await check_admin_access(message):
        return
    
    total_users = await db.get_users_count()
    banned_users = await db.get_banned_users_count()
    tournaments_count = await db.get_tournaments_count()
    
    admin_text = (
        "👑 *Админ-панель*\n\n"
        "📊 *Статистика:*\n"
        f"• Пользователей всего: {total_users}\n"
        f"• Забанено: {banned_users}\n"
        f"• Турниров: {tournaments_count}\n\n"
        "🛠 *Доступные действия:*"
    )
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    users_btn = InlineKeyboardButton('📋 Список пользователей', callback_data='admin_users_list')
    search_btn = InlineKeyboardButton('🔍 Поиск пользователя', callback_data='admin_search_user')
    ban_btn = InlineKeyboardButton('🚫 Забанить', callback_data='admin_ban_user')
    unban_btn = InlineKeyboardButton('✅ Разбанить', callback_data='admin_unban_user')
    tournaments_btn = InlineKeyboardButton('⚽ Управление турнирами', callback_data='admin_tournaments')
    matches_btn = InlineKeyboardButton('➕ Управление матчами', callback_data='admin_matches')  # Новая кнопка
    stats_btn = InlineKeyboardButton('📊 Статистика', callback_data='admin_stats')
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data='admin_back')
    
    keyboard.add(users_btn, search_btn)
    keyboard.add(ban_btn, unban_btn)
    keyboard.add(tournaments_btn, matches_btn)  # Добавляем кнопку матчей
    keyboard.add(stats_btn)
    keyboard.add(back_btn)
    
    await message.answer(admin_text, parse_mode="Markdown", reply_markup=keyboard)

async def get_users_count() -> int:
    """Получение общего количества пользователей"""
    try:
        async with aiosqlite.connect(db.db_name) as conn:
            cursor = await conn.execute("SELECT COUNT(*) FROM users")
            result = await cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        logging.error(f"Ошибка при получении количества пользователей: {e}")
        return 0

async def get_banned_users_count() -> int:
    """Получение количества забаненных пользователей"""
    try:
        async with aiosqlite.connect(db.db_name) as conn:
            cursor = await conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
            result = await cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        logging.error(f"Ошибка при получении количества забаненных пользователей: {e}")
        return 0

async def admin_users_list(callback: types.CallbackQuery):
    """Показать список пользователей"""
    if not await check_admin_access(callback.message):
        return
    
    users = await get_all_users()
    
    if not users:
        await callback.message.edit_text("📭 Нет зарегистрированных пользователей.")
        return
    
    # Показываем первых 10 пользователей
    users_text = "📋 *Список пользователей (первые 10):*\n\n"
    
    for i, user in enumerate(users[:10], 1):
        status = "🚫" if user.get('is_banned') else "✅"
        users_text += (
            f"{i}. {status} ID: {user['user_id']}\n"
            f"   👤: {user['full_name']}\n"
            f"   🔑: {user['username']}\n"
            f"   📧: {user['email']}\n"
            f"   📅: {user['registration_date'][:10]}\n\n"
        )
    
    if len(users) > 10:
        users_text += f"... и еще {len(users) - 10} пользователей"
    
    keyboard = InlineKeyboardMarkup()
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data='admin_back')
    keyboard.add(back_btn)
    
    await callback.message.edit_text(users_text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

async def get_all_users():
    """Получение всех пользователей"""
    try:
        async with aiosqlite.connect(db.db_name) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute('''
                SELECT user_id, username, email, phone, full_name, 
                       registration_date, last_login, is_banned 
                FROM users 
                ORDER BY registration_date DESC
            ''')
            users = await cursor.fetchall()
            return [dict(user) for user in users]
    except Exception as e:
        logging.error(f"Ошибка при получении списка пользователей: {e}")
        return []

async def admin_search_user(callback: types.CallbackQuery):
    """Поиск пользователя"""
    if not await check_admin_access(callback.message):
        return
    
    await callback.message.edit_text(
        "🔍 *Поиск пользователя*\n\n"
        "Введите ID пользователя, логин, email или телефон:\n\n"
        "Примеры:\n"
        "• `123456789` (ID)\n"
        "• `ivanov` (логин)\n"
        "• `ivan@mail.ru` (email)\n"
        "• `+79123456789` (телефон)",
        parse_mode="Markdown"
    )
    
    await AdminStates.waiting_for_user_search.set()
    await callback.answer()

async def process_user_search(message: types.Message, state: FSMContext):
    """Обработка поиска пользователя"""
    if not await check_admin_access(message):
        await state.finish()
        return
    
    search_query = message.text.strip()
    
    # Ищем пользователя
    user = await find_user_by_any_identifier(search_query)
    
    if not user:
        await message.answer(
            "❌ Пользователь не найден!\n\n"
            "Попробуйте другой запрос или вернитесь в админ-панель: /admin",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.finish()
        return
    
    # Показываем информацию о пользователе
    status = "🚫 ЗАБАНЕН" if user.get('is_banned') else "✅ АКТИВЕН"
    user_info = (
        f"👤 *Информация о пользователе:*\n\n"
        f"🆔 *ID:* {user['user_id']}\n"
        f"📊 *Статус:* {status}\n"
        f"🔑 *Логин:* {user['username']}\n"
        f"📧 *Email:* {user['email']}\n"
        f"📞 *Телефон:* {user.get('phone', 'Не указан')}\n"
        f"👨‍💼 *ФИО:* {user['full_name']}\n"
        f"📅 *Регистрация:* {user['registration_date'][:16]}\n"
        f"🕒 *Последний вход:* {user.get('last_login', 'Никогда')[:16]}\n"
        f"🤖 *TG Username:* @{user.get('tg_username', 'Не указан')}\n"
        f"👤 *TG Имя:* {user.get('tg_first_name', 'Не указано')}"
    )
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    if user.get('is_banned'):
        unban_btn = InlineKeyboardButton('✅ Разбанить', callback_data=f'unban_{user["user_id"]}')
        keyboard.add(unban_btn)
    else:
        ban_btn = InlineKeyboardButton('🚫 Забанить', callback_data=f'ban_{user["user_id"]}')
        keyboard.add(ban_btn)
    
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data='admin_back')
    keyboard.add(back_btn)
    
    await message.answer(user_info, parse_mode="Markdown", reply_markup=keyboard)
    await state.finish()

async def find_user_by_any_identifier(identifier: str):
    """Поиск пользователя по любому идентификатору"""
    try:
        async with aiosqlite.connect(db.db_name) as conn:
            conn.row_factory = aiosqlite.Row
            
            # Пробуем найти по user_id (если это число)
            if identifier.isdigit():
                cursor = await conn.execute(
                    "SELECT * FROM users WHERE user_id = ?", 
                    (int(identifier),)
                )
                user = await cursor.fetchone()
                if user:
                    return dict(user)
            
            # Ищем по username, email или phone
            cursor = await conn.execute('''
                SELECT * FROM users 
                WHERE username = ? OR email = ? OR phone = ?
            ''', (identifier, identifier, identifier))
            
            user = await cursor.fetchone()
            return dict(user) if user else None
            
    except Exception as e:
        logging.error(f"Ошибка при поиске пользователя: {e}")
        return None

async def admin_ban_user(callback: types.CallbackQuery):
    """Забанить пользователя"""
    if not await check_admin_access(callback.message):
        return
    
    await callback.message.edit_text(
        "🚫 *Бан пользователя*\n\n"
        "Введите ID, логин, email или телефон пользователя:\n\n"
        "⚠️ *Внимание:* После бана пользователь не сможет войти в систему!",
        parse_mode="Markdown"
    )
    
    await AdminStates.waiting_for_ban_user.set()
    await callback.answer()

async def process_ban_user(message: types.Message, state: FSMContext):
    """Обработка бана пользователя"""
    if not await check_admin_access(message):
        await state.finish()
        return
    
    identifier = message.text.strip()
    
    # Находим пользователя
    user = await find_user_by_any_identifier(identifier)
    
    if not user:
        await message.answer(
            "❌ Пользователь не найден!\n\n"
            "Попробуйте другой запрос или вернитесь в админ-панель: /admin",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.finish()
        return
    
    # Проверяем, не забанен ли уже
    if user.get('is_banned'):
        await message.answer(
            f"⚠️ Пользователь {user['username']} уже забанен!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.finish()
        return
    
    # Баним пользователя
    success = await ban_user(user['user_id'])
    
    if success:
        await message.answer(
            f"✅ Пользователь *{user['username']}* успешно забанен!\n"
            f"🆔 ID: {user['user_id']}\n"
            f"👤 ФИО: {user['full_name']}",
            parse_mode="Markdown",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "❌ Ошибка при бане пользователя!",
            reply_markup=types.ReplyKeyboardRemove()
        )
    
    await state.finish()

async def ban_user(user_id: int) -> bool:
    """Забанить пользователя в базе данных"""
    try:
        async with aiosqlite.connect(db.db_name) as conn:
            await conn.execute(
                "UPDATE users SET is_banned = 1 WHERE user_id = ?",
                (user_id,)
            )
            await conn.commit()
            
            logging.info(f"Пользователь {user_id} забанен")
            return True
    except Exception as e:
        logging.error(f"Ошибка при бане пользователя {user_id}: {e}")
        return False

async def admin_unban_user(callback: types.CallbackQuery):
    """Разбанить пользователя"""
    if not await check_admin_access(callback.message):
        return
    
    await callback.message.edit_text(
        "✅ *Разбан пользователя*\n\n"
        "Введите ID, логин, email или телефон пользователя:\n\n"
        "ℹ️ Можно разблокировать только забаненных пользователей",
        parse_mode="Markdown"
    )
    
    await AdminStates.waiting_for_unban_user.set()
    await callback.answer()

async def process_unban_user(message: types.Message, state: FSMContext):
    """Обработка разбана пользователя"""
    if not await check_admin_access(message):
        await state.finish()
        return
    
    identifier = message.text.strip()
    
    # Находим пользователя
    user = await find_user_by_any_identifier(identifier)
    
    if not user:
        await message.answer(
            "❌ Пользователь не найден!\n\n"
            "Попробуйте другой запрос или вернитесь в админ-панель: /admin",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.finish()
        return
    
    # Проверяем, забанен ли
    if not user.get('is_banned'):
        await message.answer(
            f"ℹ️ Пользователь {user['username']} не забанен!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.finish()
        return
    
    # Разбаниваем пользователя
    success = await unban_user(user['user_id'])
    
    if success:
        await message.answer(
            f"✅ Пользователь *{user['username']}* успешно разбанен!\n"
            f"🆔 ID: {user['user_id']}\n"
            f"👤 ФИО: {user['full_name']}",
            parse_mode="Markdown",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "❌ Ошибка при разбане пользователя!",
            reply_markup=types.ReplyKeyboardRemove()
        )
    
    await state.finish()

async def unban_user(user_id: int) -> bool:
    """Разбанить пользователя в базе данных"""
    try:
        async with aiosqlite.connect(db.db_name) as conn:
            await conn.execute(
                "UPDATE users SET is_banned = 0 WHERE user_id = ?",
                (user_id,)
            )
            await conn.commit()
            
            logging.info(f"Пользователь {user_id} разбанен")
            return True
    except Exception as e:
        logging.error(f"Ошибка при разбане пользователя {user_id}: {e}")
        return False

async def admin_stats(callback: types.CallbackQuery):
    """Показать статистику"""
    if not await check_admin_access(callback.message):
        return
    
    total_users = await db.get_users_count()
    banned_users = await db.get_banned_users_count()
    active_users = total_users - banned_users
    tournaments_count = await db.get_tournaments_count()
    
    stats_text = (
        "📊 *Статистика системы*\n\n"
        f"👥 *Всего пользователей:* {total_users}\n"
        f"✅ *Активных:* {active_users}\n"
        f"🚫 *Забанено:* {banned_users}\n"
        f"⚽ *Турниров:* {tournaments_count}\n\n"
        
        f"📈 *Активность:*\n"
        f"• Регистраций за сегодня: {await get_today_registrations()}\n"
        f"• Входов за сегодня: {await get_today_logins()}\n\n"
        
        "🔄 *Обновлено:* сейчас"
    )
    
    keyboard = InlineKeyboardMarkup()
    refresh_btn = InlineKeyboardButton('🔄 Обновить', callback_data='admin_stats')
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data='admin_back')
    keyboard.add(refresh_btn, back_btn)
    
    await callback.message.edit_text(stats_text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

async def get_today_registrations() -> int:
    """Получить количество регистраций за сегодня"""
    try:
        async with aiosqlite.connect(db.db_name) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM users WHERE DATE(registration_date) = DATE('now')"
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        logging.error(f"Ошибка при получении регистраций за сегодня: {e}")
        return 0

async def get_today_logins() -> int:
    """Получить количество входов за сегодня"""
    try:
        async with aiosqlite.connect(db.db_name) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM users WHERE DATE(last_login) = DATE('now')"
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        logging.error(f"Ошибка при получении входов за сегодня: {e}")
        return 0

async def admin_ban_callback(callback: types.CallbackQuery):
    """Обработка бана через callback"""
    if not await check_admin_access(callback.message):
        return
    
    user_id = int(callback.data.split('_')[1])
    
    success = await ban_user(user_id)
    
    if success:
        await callback.answer("✅ Пользователь забанен!")
        # Обновляем сообщение
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            f"✅ Пользователь с ID {user_id} забанен!",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await callback.answer("❌ Ошибка при бане!")

async def admin_unban_callback(callback: types.CallbackQuery):
    """Обработка разбана через callback"""
    if not await check_admin_access(callback.message):
        return
    
    user_id = int(callback.data.split('_')[1])
    
    success = await unban_user(user_id)
    
    if success:
        await callback.answer("✅ Пользователь разбанен!")
        # Обновляем сообщение
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            f"✅ Пользователь с ID {user_id} разбанен!",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await callback.answer("❌ Ошибка при разбане!")

async def admin_tournaments(callback: types.CallbackQuery):
    """Управление турнирами из админ-панели"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    tournaments = await db.get_all_tournaments()
    
    if not tournaments:
        await callback.message.edit_text(
            "🛠 *Управление турнирами*\n\n"
            "На данный момент нет активных турниров для управления.\n\n"
            "Вы можете добавить новый турнир:",
            parse_mode="Markdown"
        )
    else:
        tournaments_text = "🛠 *Управление турнирами*\n\n"
        tournaments_text += "📋 *Список турниров:*\n\n"
        
        for i, tournament in enumerate(tournaments, 1):
            tournaments_text += (
                f"{i}. *{tournament['name']}*\n"
                f"   📝 {tournament.get('description', 'Описание отсутствует')}\n"
                f"   👤 Создал: {tournament.get('created_by_username', 'Админ')}\n"
                f"   📅 {tournament['created_date'][:10]}\n\n"
            )
        
        await callback.message.edit_text(
            tournaments_text,
            parse_mode="Markdown"
        )
    
    # Создаем клавиатуру для управления турнирами
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    add_btn = InlineKeyboardButton('➕ Добавить турнир', callback_data='tournament_add')
    manage_btn = InlineKeyboardButton('🛠 Управление турнирами', callback_data='tournaments_manage')
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data='admin_back')
    
    keyboard.add(add_btn, manage_btn)
    keyboard.add(back_btn)
    
    # Если сообщение уже было отредактировано, отправляем новое
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except:
        await callback.message.answer("Выберите действие:", reply_markup=keyboard)
    
    await callback.answer()

# Добавим обработчик для управления матчами
async def admin_matches(callback: types.CallbackQuery):
    """Управление матчами из админ-панели"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав!")
        return
    
    tournaments = await db.get_all_tournaments()
    
    if not tournaments:
        await callback.message.edit_text(
            "⚽ *Управление матчами*\n\n"
            "На данный момент нет активных турниров.\n"
            "Сначала создайте турнир для добавления матчей.",
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            "⚽ *Управление матчами*\n\n"
            "Выберите действие:",
            parse_mode="Markdown"
        )
    
    # Создаем клавиатуру для управления матчами
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    add_match_btn = InlineKeyboardButton('➕ Добавить матч', callback_data='admin_add_match')
    view_matches_btn = InlineKeyboardButton('📋 Просмотр матчей', callback_data='admin_view_matches')
    back_btn = InlineKeyboardButton('🔙 Назад', callback_data='admin_back')
    
    keyboard.add(add_match_btn, view_matches_btn)
    keyboard.add(back_btn)
    
    # Если сообщение уже было отредактировано, отправляем новое
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except:
        await callback.message.answer("Выберите действие:", reply_markup=keyboard)
    
    await callback.answer()

# Добавим обработчики для новых кнопок
async def admin_add_match(callback: types.CallbackQuery, state: FSMContext):
    """Добавление матча через админ-панель"""
    from handlers.matches import start_add_match
    await start_add_match(callback, state)

async def admin_view_matches(callback: types.CallbackQuery):
    """Просмотр матчей через админ-панель"""
    from handlers.tournaments import show_tournaments
    await show_tournaments(callback.message)
    await callback.answer()

async def admin_back(callback: types.CallbackQuery):
    """Возврат в главное меню админ-панели"""
    if not await check_admin_access(callback.message):
        return
    
    await cmd_admin(callback.message)
    await callback.answer()

def register_handlers_admin(dp: Dispatcher):
    """Регистрация обработчиков админ-панели"""
    # Команда админ-панели
    dp.register_message_handler(cmd_admin, Command("admin"), state="*")
    
    # Обработчики callback-кнопок
    dp.register_callback_query_handler(admin_users_list, lambda c: c.data == 'admin_users_list')
    dp.register_callback_query_handler(admin_search_user, lambda c: c.data == 'admin_search_user')
    dp.register_callback_query_handler(admin_ban_user, lambda c: c.data == 'admin_ban_user')
    dp.register_callback_query_handler(admin_unban_user, lambda c: c.data == 'admin_unban_user')
    dp.register_callback_query_handler(admin_tournaments, lambda c: c.data == 'admin_tournaments')
    dp.register_callback_query_handler(admin_matches, lambda c: c.data == 'admin_matches')  # Новый обработчик
    dp.register_callback_query_handler(admin_add_match, lambda c: c.data == 'admin_add_match')  # Новый обработчик
    dp.register_callback_query_handler(admin_view_matches, lambda c: c.data == 'admin_view_matches')  # Новый обработчик
    dp.register_callback_query_handler(admin_stats, lambda c: c.data == 'admin_stats')
    dp.register_callback_query_handler(admin_back, lambda c: c.data == 'admin_back')
    dp.register_callback_query_handler(admin_ban_callback, lambda c: c.data.startswith('ban_'))
    dp.register_callback_query_handler(admin_unban_callback, lambda c: c.data.startswith('unban_'))
    
    # Обработчики состояний
    dp.register_message_handler(process_user_search, state=AdminStates.waiting_for_user_search)
    dp.register_message_handler(process_ban_user, state=AdminStates.waiting_for_ban_user)
    dp.register_message_handler(process_unban_user, state=AdminStates.waiting_for_unban_user)