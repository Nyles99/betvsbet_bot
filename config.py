import os
from dataclasses import dataclass

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')
    DATABASE_NAME: str = 'users.db'
    ADMIN_IDS: list = None

    def __post_init__(self):
        if self.ADMIN_IDS is None:
            self.ADMIN_IDS = [831040832]  # Замените на ваш ID

config = Config()