import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import aiosqlite

API_TOKEN = '7907836937:AAFDINYLw3dMRaZ5Hhy7TA-n-Ua410QeyiU'
ADMIN_ID = 831040832  # замените на ваш ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

DB_PATH = 'users.db'

# Инициализация базы данных
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                login TEXT UNIQUE,
                name TEXT,
                password TEXT,
                is_admin INTEGER DEFAULT 0
            )
        ''')
        await db.commit()

# Вспомогательные функции для работы с БД

async def add_user(user_id, login, name, password, is_admin=0):
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                'INSERT INTO users (user_id, login, name, password, is_admin) VALUES (?, ?, ?, ?, ?)',
                (user_id, login, name, password, is_admin)
            )
            await db.commit()
            return True
        except Exception as e:
            print(f"Ошибка добавления пользователя: {e}")
            return False

async def get_user_by_id(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT user_id, login, name, password, is_admin FROM users WHERE user_id=?', (user_id,))
        row = await cursor.fetchone()
        if row:
            return {
                'user_id': row[0],
                'login': row[1],
                'name': row[2],
                'password': row[3],
                'is_admin': row[4]
            }
        return None

async def get_user_by_login(login):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT user_id, login, name, password, is_admin FROM users WHERE login=?', (login,))
        row = await cursor.fetchone()
        if row:
            return {
                'user_id': row[0],
                'login': row[1],
                'name': row[2],
                'password': row[3],
                'is_admin': row[4]
            }
        return None

async def get_all_users():
    users = []
    async with aiosqlite.connect(DB_PATH) as db:
        async for row in db.execute('SELECT user_id, login, name FROM users'):
            users.append({'user_id': row[0], 'login': row[1], 'name': row[2]})
    return users

# Стейты для регистрации и входа
class Registration(StatesGroup):
    login = State()
    name = State()
    password = State()

class Login(StatesGroup):
    login = State()
    password = State()

# Обработчики команд и логика регистрации/входа остаются похожими,
# только теперь используют базу данных.

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_data = await get_user_by_id(message.from_user.id)
    if user_data:
        # Пользователь зарегистрирован — показываем профиль
        profile_text = (
            f"Личный кабинет:\n"
            f"Логин: {user_data['login']}\n"
            f"Имя: {user_data['name']}\n"
            f"ID пользователя: {message.from_user.id}"
        )
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("/logout", "/admin")
        await message.answer(profile_text, reply_markup=keyboard)
    else:
        # Не зарегистрирован — предлагаем регистрацию или вход
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("/register", "/login")
        await message.answer("Добро пожаловать! Пожалуйста, зарегистрируйтесь или войдите.", reply_markup=keyboard)

@dp.message_handler(commands=['register'])
async def register_start(message: types.Message):
    await Registration.login.set()
    await message.answer("Введите логин:")

@dp.message_handler(state=Registration.login)
async def register_login(message: types.Message, state: FSMContext):
    existing_user = await get_user_by_login(message.text.strip())
    if existing_user:
        await message.answer("Этот логин уже занят. Попробуйте другой.")
        return
    await state.update_data(login=message.text.strip())
    await Registration.next()
    await message.answer("Введите ваше имя:")

@dp.message_handler(state=Registration.name)
async def register_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await Registration.next()
    await message.answer("Введите пароль:")

@dp.message_handler(state=Registration.password)
async def register_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    login = data['login']
    name = data['name']
    password = message.text.strip()
    
    success = await add_user(
        user_id=message.from_user.id,
        login=login,
        name=name,
        password=password,
        is_admin=0  # по умолчанию не админ
    )
    
    if success:
        await message.answer("Регистрация прошла успешно!", reply_markup=types.ReplyKeyboardRemove())
        
        # После регистрации показываем профиль
        profile_text=f"Личный кабинет:\nЛогин: {login}\nИмя: {name}\nID пользователя: {message.from_user.id}"
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("/logout", "/admin")
        
        await message.answer(profile_text, reply_markup=keyboard)
        
    else:
        await message.answer("Ошибка при регистрации. Попробуйте снова.")
    
    await state.finish()

@dp.message_handler(commands=['login'])
async def login_start(message: types.Message):
    await Login.login.set()
    await message.answer("Введите логин:")

@dp.message_handler(state=Login.login)
async def login_login(message: types.Message, state: FSMContext):
    login_input=message.text.strip()
    
    user_record=await get_user_by_login(login_input)
    
    if not user_record:
        await message.answer("Пользователь с таким логином не найден. Попробуйте снова.")
        return
    
    # Запрос пароля
    await state.update_data(user_id=user_record['user_id'])
    await Login.next()
    await message.answer("Введите пароль:")

@dp.message_handler(state=Login.password)
async def login_password(message: types.Message, state: FSMContext):
    data_state=await state.get_data()
    
    user_record=await get_user_by_login(await get_user_by_id(data_state['user_id'])['login'])
    
    # Или проще — получаем по ID из состояния.
    
    # Лучше так:
    
@dp.message_handler(state=Login.password)
async def verify_password(message: types.Message, state:FSMContext):
     data_state=await state.get_data()
     user_record=await get_user_by_id(data_state['user_id'])
     if not user_record:
         await message.answer("Ошибка авторизации.")
         return
    
     if user_record['password']==message.text.strip():
         # Успешный вход
         active_sessions[user_record['user_id']] = True
         
         profile_text=f"Личный кабинет:\nЛогин:{user_record['login']}\nИмя:{user_record['name']}\nID:{user_record['user_id']}"
         
         keyboard=types.ReplyKeyboardMarkup(resize_keyboard=True)
         keyboard.add("/logout", "/admin")
         
         await message.answer("Вы успешно вошли!", reply_markup=keyboard)
         
     else:
         await message.answer("Неверный пароль. Попробуйте снова.")
     
     await state.finish()

# Остальные обработчики — аналогично предыдущему примеру — используют базу данных для получения информации.

# Важное дополнение — запуск и инициализация базы данных при старте:

if __name__ == '__main__':
	asyncio.run(init_db())
	from aiogram import executor
	
	executor.start_polling(dp)