from aiogram import Bot
from aiogram.types import Message
from keyboards.register_kb import register_keyboard


async def get_start(message: Message, bot: Bot):
    await bot.send_message(message.from_user.id, f' Привет, {message.from_user.first_name}, ты в тотализаторе Винкома, регайся', reply_markup=register_keyboard)