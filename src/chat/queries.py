from typing import List, Self

from sqlalchemy.orm import Session, load_only

import chat.models as models
import chat.schemas as schemas

from order.queries import ChatIdByOrderIdQuery


class AllMessagesByChatIdQuery:
    def __init__(self, db: Session):
        self.__db = db
        self.__messages: List[models.Message] = []

    def as_models(self) -> List[models.Message]:
        return self.__messages

    def as_schemas(self) -> List[schemas.Message]:
        return [schemas.Message(**m.__dict__) for m in self.__messages]

    def __call__(self, chat_id: int) -> Self:
        self.__messages = (
            self.__db.query(models.Message)
            .filter(models.Message.chat_id == chat_id)
            .all()
        )
        return self


class AllMessagesByOrderIdQuery:
    def __init__(self, db: Session):
        self.__db = db
        self.__messages: List[models.Message] = []

    def as_models(self) -> List[models.Message]:
        return self.__messages

    def as_schemas(self) -> List[schemas.Message]:
        return [schemas.Message(**m.__dict__) for m in self.__messages]

    def __call__(self, order_id: int) -> Self:
        chat_id = ChatIdByOrderIdQuery(db=self.__db)(order_id=order_id)

        if chat_id is None:
            return self

        all_messages_query = AllMessagesByChatIdQuery(db=self.__db)
        self.__messages = all_messages_query(chat_id=chat_id).as_models()

        return self


class ChatContainsUserQuery:
    def __init__(self, db: Session, chat_id: int):
        self.__db = db
        self.__chat_id = chat_id

    def __call__(self, user_id: int) -> bool:
        chat: models.Chat = (
            self.__db.query(models.Chat)
            .options(load_only(models.Chat.master_id, models.Chat.customer_id))
            .filter(models.Chat.id == self.__chat_id)
            .first()
        )
        members: [int] = [chat.master_id, chat.customer_id]
        return user_id in members
