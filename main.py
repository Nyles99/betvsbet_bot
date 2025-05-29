import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.filters
import aiosqlite

API_TOKEN = '7907836937:AAFDINYLw3dMRaZ5Hhy7TA-n-Ua410QeyiU'
ADMIN_ID = 831040832  # замените на ваш ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer('Это была команда старт')




async def main():
    dp.start_polling(bot)
    
asyncio.run(main())