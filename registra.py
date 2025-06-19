import logging
from aiogram import Bot, Dispatcher, executor, types
import markups as nav
from db import Database

TOKEN = '7634755610:AAHPl9fRym-y9DEL1haYqrLOJRjdxkh1Xe8'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)





if __name__ == '__main__':
    executor.start_polling(dp, skip_updates = True)