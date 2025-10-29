from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    user_id: int
    phone_number: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    registration_date: Optional[str] = None
    last_login: Optional[str] = None