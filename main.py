from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
import asyncio
import os
from aiogram.filters import Command

from utils.commands import set_commands
from handlers.start import get_start
from state.register import RegisterState
from handlers.register import start_register, register_name, register_phone


bot = Bot(token='7634755610:AAHPl9fRym-y9DEL1haYqrLOJRjdxkh1Xe8')
admin_id = '831040832'

dp = Dispatcher()



async def start_bot(bot: Bot):
    await bot.send_message(admin_id, text="привет")
    
dp.startup.register(start_bot)
dp.message.register(get_start, Command(commands='start'))

#Ругистриуем хендлеры регистрации
dp.message.register(start_register, F.text=='Зарегистрироваться на сайте')
dp.message.register(register_name, RegisterState.regName)
dp.message.register(register_phone, RegisterState.regPhone)
   
async def start():
    await set_commands(bot)
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()
    
if __name__ == "__main__":
    asyncio.run(start())