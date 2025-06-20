import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage 

API_TOKEN = '7634755610:AAHPl9fRym-y9DEL1haYqrLOJRjdxkh1Xe8'

# Инициализация базы данных для хранения состояний
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Создаем или подключаемся к базе данных для хранения пользователей
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Создаем таблицу пользователей, если не существует
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    login TEXT NOT NULL,
    password TEXT NOT NULL,
    phone TEXT NOT NULL
)
''')
conn.commit()

# Определение состояний регистрации
class Registration(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()
    waiting_for_phone = State()

# Команда /start
@dp.message(Command(commands=["start"]))
async def start_handler(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
    user = cursor.fetchone()
    if user:
        await message.answer("Вы уже зарегистрированы. Используйте /cabinet для просмотра данных.")
    else:
        await message.answer("Здравствуйте! Чтобы зарегистрироваться, используйте команду /register.")

# Команда /register - начинаем регистрацию
@dp.message(Command(commands=["register"]))
async def register_start(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id

    # Проверка, есть ли уже пользователь
    cursor.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
    if cursor.fetchone():
        await message.answer("Вы уже зарегистрированы.")
        return

    await message.answer("Пожалуйста, введите ваш логин:")
    await state.set_state(Registration.waiting_for_login)

# Обработка логина
@dp.message(Registration.waiting_for_login)
async def process_login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text.strip())
    await message.answer("Пожалуйста, введите ваш пароль:")
    await state.set_state(Registration.waiting_for_password)

# Обработка пароля
@dp.message(Registration.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text.strip())
    
    # Запрос номера телефона с кнопкой отправки контакта
    phone_button = types.KeyboardButton(text="Отправить номер телефона", request_contact=True)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(phone_button)
    
    await message.answer("Пожалуйста, отправьте ваш номер телефона:", reply_markup=keyboard)
    await state.set_state(Registration.waiting_for_phone)

# Обработка номера телефона
@dp.message(Registration.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    contact = message.contact
    if contact and contact.phone_number:
        phone_number = contact.phone_number
        data = await state.get_data()
        login = data['login']
        password = data['password']
        telegram_id = message.from_user.id

        # Сохраняем пользователя в базу данных
        cursor.execute(
            "INSERT INTO users (telegram_id, login, password, phone) VALUES (?, ?, ?, ?)",
            (telegram_id, login, password, phone_number)
        )
        conn.commit()

        await message.answer("Регистрация прошла успешно!", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
    else:
        # Если контакт не получен — можно повторить или отменить регистрацию
        await message.answer("Не удалось получить номер телефона. Попробуйте снова командой /register.")
        await state.clear()

# Личный кабинет /cabinet
@dp.message(Command(commands=["cabinet"]))
async def cabinet_handler(message: types.Message):
    telegram_id = message.from_user.id
    cursor.execute("SELECT login, password, phone FROM users WHERE telegram_id=?", (telegram_id,))
    user = cursor.fetchone()
    
    if not user:
        await message.answer("Вы не зарегистрированы. Используйте команду /register для регистрации.")
        return
    
    login, password, phone = user
    
    info_text = (
        f"Ваши данные:\n"
        f"Логин: {login}\n"
        f"Пароль: {password}\n"
        f"Телефон: {phone}"
    )
    
    await message.answer(info_text)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

asyncio.run(main())