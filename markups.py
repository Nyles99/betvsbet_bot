from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

btnProfile = KeyboardButton('ПРОФИЛЬ')
btnSub = KeyboardButton('ПОДПИСКА')

MainMenu = ReplyKeyboardMarkup(resize_keyboard = True)
MainMenu.add(btnProfile, btnSub)