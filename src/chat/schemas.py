from datetime import datetime

from core.schemas import CamelModel

import auth.schemas as auth_schemas


class Message(CamelModel):
    text: str
    from_user_type: auth_schemas.UserType
    from_user_id: int
    to_user_id: int
    chat_id: int
    created_at: datetime


class Chat(CamelModel):
    id: int
    customer_id: int
    master_id: int
