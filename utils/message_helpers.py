from aiogram.types import Message, CallbackQuery
from aiogram.utils.exceptions import MessageNotModified

async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup=None):
    """
    Безопасное редактирование сообщения с обработкой ошибки MessageNotModified
    """
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except MessageNotModified:
        # Игнорируем ошибку, если сообщение не изменилось
        pass