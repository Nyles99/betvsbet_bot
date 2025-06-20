from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

register_keyboard = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(
            text='Зарегистрироваться на сайте'
        )
    ]    
],resize_keyboard=True, one_time_keyboard=True, input_field_placeholder='Для продолжения нажмите на кнопку ниже')