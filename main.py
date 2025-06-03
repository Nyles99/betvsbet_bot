import logging
import asyncio
from aiogram import Bot, Dispatcher, types


from aiogram.filters import CommandStart


API_TOKEN = '7634755610:AAHPl9fRym-y9DEL1haYqrLOJRjdxkh1Xe8'
ADMIN_ID = 831040832  # замените на ваш ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)

dp = Dispatcher()

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer('Это была команда старт')




async def main():
    await dp.start_polling(bot)
    
asyncio.run(main())