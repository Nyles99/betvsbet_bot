from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
from database.db_handler import DatabaseHandler
from keyboards.menu import get_cancel_login_keyboard, get_main_inline_keyboard
from states.user_states import AuthStates
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

async def start_login(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🚪 Вход\n\nВведите логин:", reply_markup=get_cancel_login_keyboard())
    await AuthStates.waiting_for_username.set()

async def process_username_login(message: Message, state: FSMContext):
    username = message.text.strip()
    db = DatabaseHandler('users.db')
    user = db.get_user_by_username(username)
    
    if not user:
        await message.answer("❌ Пользователь не найден. Попробуйте еще раз:", reply_markup=get_cancel_login_keyboard())
        return
    
    async with state.proxy() as data:
        data['user_id'] = user.user_id
    
    await message.answer("✅ Логин принят!\n\nВведите пароль:", reply_markup=get_cancel_login_keyboard())
    await AuthStates.waiting_for_password.set()

async def process_password_login(message: Message, state: FSMContext):
    password = message.text.strip()
    
    async with state.proxy() as data:
        user_id = data['user_id']
    
    db = DatabaseHandler('users.db')
    if db.verify_password(user_id, hash_password(password)):
        db.update_last_login(user_id)
        await message.answer("✅ Вход выполнен!", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("Выберите действие:", reply_markup=get_main_inline_keyboard())
    else:
        await message.answer("❌ Неверный пароль. Попробуйте еще раз:", reply_markup=get_cancel_login_keyboard())
        return
    
    await state.finish()

async def cancel_login(callback: CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.edit_text("❌ Вход отменен.", reply_markup=types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("🔙 Назад", callback_data="start")
    ))

def register_login_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(start_login, lambda c: c.data == "login", state="*")
    dp.register_message_handler(process_username_login, state=AuthStates.waiting_for_username)
    dp.register_message_handler(process_password_login, state=AuthStates.waiting_for_password)
    dp.register_callback_query_handler(cancel_login, lambda c: c.data == "start", state=AuthStates.all_states)