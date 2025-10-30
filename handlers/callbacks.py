from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.exceptions import MessageNotModified
from database.db_handler import DatabaseHandler
from keyboards.menu import (
    get_main_inline_keyboard, 
    get_profile_inline_keyboard, 
    get_user_tournaments_keyboard,
    get_user_tournament_matches_keyboard,
    get_available_matches_keyboard,
    get_user_bets_tournaments_keyboard,
    get_user_tournament_bets_keyboard,
    get_back_keyboard
)
from states.user_states import ProfileStates, UserBetStates
from utils.validators import validate_username, validate_full_name, validate_score

async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup=None):
    """
    Безопасное редактирование сообщения с обработкой ошибки MessageNotModified
    """
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    except MessageNotModified:
        pass

async def navigation_handler(callback: CallbackQuery, state: FSMContext, section: str):
    """
    Универсальный обработчик навигации по основным разделам
    """
    if state:
        await state.finish()
    
    navigation_config = {
        'main_menu': {
            'text': "Выберите действие:",
            'keyboard': get_main_inline_keyboard
        },
        'profile': {
            'text': "👤 Личный кабинет. Выберите действие:",
            'keyboard': get_profile_inline_keyboard
        },
        'tournaments': {
            'text': "🏆 Доступные турниры:\n\nЗдесь вы можете:\n• Просмотреть матчи турниров\n• Сделать ставки на матчи\n• Отслеживать свои прогнозы\n\nВыберите турнир:",
            'keyboard': lambda: get_user_tournaments_keyboard(DatabaseHandler('users.db').get_all_tournaments())
        },
        'my_bets': {
            'text': "📋 Мои ставки",
            'keyboard': lambda: get_user_bets_tournaments_keyboard(
                DatabaseHandler('users.db').get_user_tournaments_with_bets(callback.from_user.id)
            )
        },
        'help': {
            'text': """
🤖 **Помощь по боту:**

📱 **Регистрация:** Для регистрации требуется номер телефона в формате +7
👤 **Личный кабинет:** Позволяет изменить логин, ФИО и просмотреть ставки
🏆 **Турниры:** Просмотр доступных турниров, матчей и ввод ставок
📋 **Мои ставки:** Просмотр всех ваших ставок по турнирам

📝 **Как сделать ставку:**
1. Перейдите в раздел "🏆 Турниры"
2. Выберите интересующий турнир  
3. Выберите матч из списка
4. Введите счет в формате X-Y (например: 2-1)
            """,
            'keyboard': lambda: get_back_keyboard()
        },
        'about': {
            'text': """
📞 **О нас**

Мы - современная платформа для организации и проведения турниров. 

🎯 **Наша миссия:** Сделать участие в турнирах простым и доступным для всех.

🏆 **Турниры:** Регулярно проводим различные соревнования и чемпионаты.

⚽ **Ставки:** Участвуйте в прогнозировании результатов матчей.

Следите за нашими обновлениями!
            """,
            'keyboard': lambda: get_back_keyboard()
        }
    }
    
    if section in navigation_config:
        config = navigation_config[section]
        keyboard = config['keyboard']() if callable(config['keyboard']) else config['keyboard']
        await safe_edit_message(callback, config['text'], keyboard)

# Функции-обертки для навигации
async def main_menu_handler(callback: CallbackQuery, state: FSMContext = None):
    await navigation_handler(callback, state, 'main_menu')

async def profile_handler(callback: CallbackQuery, state: FSMContext = None):
    await navigation_handler(callback, state, 'profile')

async def tournaments_handler(callback: CallbackQuery, state: FSMContext = None):
    await navigation_handler(callback, state, 'tournaments')

async def my_bets_handler(callback: CallbackQuery, state: FSMContext = None):
    await navigation_handler(callback, state, 'my_bets')

async def help_handler(callback: CallbackQuery, state: FSMContext = None):
    await navigation_handler(callback, state, 'help')

async def about_handler(callback: CallbackQuery, state: FSMContext = None):
    await navigation_handler(callback, state, 'about')

async def my_profile_callback(callback: CallbackQuery, state: FSMContext):
    """Показать профиль пользователя"""
    await state.finish()
    
    db = DatabaseHandler('users.db')
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if user:
        user_bets = db.get_user_bets(user_id)
        profile_text = f"""
👤 **Ваш профиль:**

📱 **Телефон:** {user.phone_number}
👤 **Логин:** {user.username or 'Не установлен'}
📛 **ФИО:** {user.full_name or 'Не установлено'}
📅 **Дата регистрации:** {user.registration_date}
⚽ **Количество ставок:** {len(user_bets)}
        """
        await safe_edit_message(callback, profile_text, get_profile_inline_keyboard())
    else:
        await callback.answer("❌ Профиль не найден.", show_alert=True)

async def user_tournament_detail_callback(callback: CallbackQuery, state: FSMContext):
    """Детальная информация о турнире для пользователя"""
    await state.finish()
    
    tournament_id = int(callback.data.split('_')[2])
    user_id = callback.from_user.id
    
    db = DatabaseHandler('users.db')
    tournament = db.get_tournament(tournament_id)
    all_matches = db.get_tournament_matches(tournament_id)
    
    # Фильтруем матчи - оставляем только те, на которые пользователь еще не делал ставку
    available_matches = []
    for match in all_matches:
        user_bet = db.get_user_bet(user_id, match[0])
        if not user_bet:
            available_matches.append(match)
    
    if tournament:
        if available_matches:
            text = f"🏆 Матчи турнира: {tournament[1]}\n\n"
            if tournament[2]:
                text += f"📝 {tournament[2]}\n\n"
            text += "Выберите матч для ввода счета:\n\n"
            
            for match in available_matches:
                text += f"📅 {match[2]} {match[3]} - {match[4]} vs {match[5]}\n\n"
        else:
            text = f"🏆 Турнир: {tournament[1]}\n\n"
            if tournament[2]:
                text += f"📝 {tournament[2]}\n\n"
            
            if all_matches:
                text += "✅ Вы уже сделали ставки на все матчи этого турнира!\n\n"
                text += "Просмотреть свои ставки можно в разделе '📋 Мои ставки' личного кабинета."
            else:
                text += "В этом турнире пока нет матчей.\n\nСледите за обновлениями!"
        
        await safe_edit_message(
            callback,
            text,
            get_user_tournament_matches_keyboard(tournament_id, available_matches)
        )
    else:
        await callback.answer("❌ Турнир не найден.", show_alert=True)

async def user_match_detail_callback(callback: CallbackQuery, state: FSMContext):
    """Детальная информация о матче для пользователя с возможностью ввода счета"""
    await state.finish()
    
    match_id = int(callback.data.split('_')[2])
    user_id = callback.from_user.id
    
    db = DatabaseHandler('users.db')
    match = db.get_match(match_id)
    
    if match:
        tournament = db.get_tournament(match[1])
        user_bet = db.get_user_bet(user_id, match_id)
        
        if user_bet:
            text = f"""
⚽ Информация о матче:

🏆 Турнир: {tournament[1]}
📅 Дата: {match[2]}
⏰ Время: {match[3]}
⚔️ Матч: {match[4]} vs {match[5]}
🔰 Статус: Запланирован

✅ Ваш счет: {user_bet[3]}
📅 Дата ставки: {user_bet[4]}
            """
            await safe_edit_message(
                callback,
                text,
                get_back_keyboard(f"user_tournament_{match[1]}", "🔙 Назад к турниру")
            )
        else:
            text = f"""
⚽ Ввод счета для матча:

🏆 Турнир: {tournament[1]}
📅 Дата: {match[2]}
⏰ Время: {match[3]}
⚔️ Матч: {match[4]} vs {match[5]}

📝 Введите счет матча в формате X-Y (например: 2-1) и нажмите отправить:
            """
            
            async with state.proxy() as data:
                data['match_id'] = match_id
                data['match_info'] = f"{match[4]} vs {match[5]}"
                data['tournament_id'] = match[1]
            
            await safe_edit_message(
                callback,
                text,
                get_back_keyboard(f"user_tournament_{match[1]}", "🔙 Назад к турниру")
            )
            await UserBetStates.waiting_for_score.set()
    else:
        await callback.answer("❌ Матч не найден.", show_alert=True)

async def bets_tournament_detail_callback(callback: CallbackQuery, state: FSMContext):
    """Детали ставок в турнире"""
    await state.finish()
    
    tournament_id = int(callback.data.split('_')[2])
    
    db = DatabaseHandler('users.db')
    user_id = callback.from_user.id
    tournament = db.get_tournament(tournament_id)
    bets = db.get_tournament_bets_by_user(user_id, tournament_id)
    
    if tournament and bets:
        text = f"📋 Ваши ставки в турнире: {tournament[1]}\n\n"
        
        for bet in bets:
            text += f"📅 {bet[5]} | {bet[6]} | {bet[7]} vs {bet[8]} | Счет: {bet[3]}\n\n"
        
        await safe_edit_message(
            callback,
            text,
            get_user_tournament_bets_keyboard(tournament_id, bets)
        )
    else:
        await callback.answer("❌ Ставки не найдены.", show_alert=True)

async def change_username_callback(callback: CallbackQuery, state: FSMContext):
    """Начало изменения логина"""
    await safe_edit_message(
        callback,
        "Введите новый логин (только латинские буквы, цифры и нижнее подчеркивание, 3-20 символов):\n\nДля отмены нажмите кнопку 'Назад'",
        get_back_keyboard()
    )
    await ProfileStates.waiting_for_username.set()

async def change_fullname_callback(callback: CallbackQuery, state: FSMContext):
    """Начало изменения ФИО"""
    await safe_edit_message(
        callback,
        "Введите ваше ФИО (только буквы, пробелы и дефисы, 2-100 символов):\n\nДля отмены нажмите кнопку 'Назад'",
        get_back_keyboard()
    )
    await ProfileStates.waiting_for_full_name.set()

async def process_score_message(message: Message, state: FSMContext):
    """Обработка сообщения с счетом из чата"""
    score = message.text.strip()
    
    if not validate_score(score):
        await message.answer(
            "❌ Неверный формат счета. Используйте формат X-Y (например: 2-1).\n\nПопробуйте еще раз:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return
    
    async with state.proxy() as data:
        match_id = data['match_id']
        match_info = data['match_info']
        tournament_id = data.get('tournament_id')
    
    db = DatabaseHandler('users.db')
    user_id = message.from_user.id
    
    if db.add_user_bet(user_id, match_id, score):
        await message.answer(
            f"✅ Счет {score} для матча {match_info} успешно сохранен!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        # Возвращаем пользователя в список матчей турнира
        tournament = db.get_tournament(tournament_id)
        all_matches = db.get_tournament_matches(tournament_id)
        
        available_matches = []
        for match in all_matches:
            user_bet = db.get_user_bet(user_id, match[0])
            if not user_bet:
                available_matches.append(match)
        
        if available_matches:
            text = f"🏆 Матчи турнира: {tournament[1]}\n\n✅ Ваша ставка сохранена!\n\nВыберите следующий матч для ввода счета:\n\n"
            for match in available_matches:
                text += f"📅 {match[2]} {match[3]} - {match[4]} vs {match[5]}\n\n"
        else:
            text = f"🏆 Турнир: {tournament[1]}\n\n✅ Поздравляем! Вы сделали ставки на все матчи этого турнира!\n\nПросмотреть все свои ставки можно в разделе '📋 Мои ставки' личного кабинета."
        
        await message.answer(
            text,
            reply_markup=get_user_tournament_matches_keyboard(tournament_id, available_matches)
        )
    else:
        await message.answer(
            "❌ Ошибка при сохранении ставки. Попробуйте еще раз.",
            reply_markup=get_back_keyboard(f"user_tournament_{tournament_id}", "🔙 Назад к турниру")
        )
    
    await state.finish()

def register_callback_handlers(dp: Dispatcher):
    """Регистрация обработчиков колбэков"""
    # Основная навигация
    dp.register_callback_query_handler(main_menu_handler, lambda c: c.data == "main_menu", state="*")
    dp.register_callback_query_handler(profile_handler, lambda c: c.data == "profile", state="*")
    dp.register_callback_query_handler(tournaments_handler, lambda c: c.data == "tournaments", state="*")
    dp.register_callback_query_handler(my_bets_handler, lambda c: c.data == "my_bets", state="*")
    dp.register_callback_query_handler(help_handler, lambda c: c.data == "help", state="*")
    dp.register_callback_query_handler(about_handler, lambda c: c.data == "about", state="*")
    
    # Специфические обработчики
    dp.register_callback_query_handler(my_profile_callback, lambda c: c.data == "my_profile", state="*")
    dp.register_callback_query_handler(bets_tournament_detail_callback, lambda c: c.data.startswith("bets_tournament_"), state="*")
    dp.register_callback_query_handler(change_username_callback, lambda c: c.data == "change_username", state="*")
    dp.register_callback_query_handler(change_fullname_callback, lambda c: c.data == "change_fullname", state="*")
    dp.register_callback_query_handler(user_tournament_detail_callback, lambda c: c.data.startswith("user_tournament_"), state="*")
    dp.register_callback_query_handler(user_match_detail_callback, lambda c: c.data.startswith("user_match_"), state="*")
    
    # FSM для ставок
    dp.register_message_handler(process_score_message, state=UserBetStates.waiting_for_score)