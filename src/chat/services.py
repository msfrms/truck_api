from typing import Dict, List
from datetime import datetime
from fastapi import HTTPException, WebSocket, WebSocketDisconnect, status
from starlette.websockets import WebSocketState

from sqlalchemy.orm import Session

import chat.models as models
import chat.schemas as schemas
import chat.queries as queries

import auth.schemas as auth_schemas


from core.errors import Error


import order.queries as order_queries

import json


class ChatService:
    def __init__(self, db: Session) -> None:
        self.__db = db

    def try_exception_if_chat_not_available(self, order_id: int):
        hasChatQuery = order_queries.OrderHasChatQuery(db=self.__db)
        if not hasChatQuery(order_id=order_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Error.NOT_ALLOW_OPERATION,
            )

    def create_chat(self, master_id: int, customer_id: int) -> models.Chat:
        chat = models.Chat()
        chat.master_id = master_id
        chat.customer_id = customer_id
        chat.created_at = datetime.utcnow()

        self.__db.add(chat)
        self.__db.flush()

        return chat

    def get_all_messages(self, order_id: int, user_id: int) -> List[schemas.Message]:
        user_has_access_to_order = order_queries.UserHasAccessToOrderQuery(db=self.__db)

        if not user_has_access_to_order(order_id=order_id, user_id=user_id):
            return []

        all_messages_query = queries.AllMessagesByOrderIdQuery(db=self.__db)
        return all_messages_query(order_id=order_id).as_schemas()

    def add_message(self, message: schemas.Message):
        db_message = models.Message()
        db_message.text = message.text
        db_message.chat_id = message.chat_id
        db_message.from_user_id = message.from_user_id
        db_message.to_user_id = message.to_user_id
        db_message.created_at = datetime.utcnow()
        db_message.from_user_type = message.from_user_type

        self.__db.add(db_message)
        self.__db.commit()
        self.__db.refresh(db_message)


class UserConnectionsService:
    def __init__(self) -> None:
        self.__master_connections: Dict[int, WebSocket] = {}
        self.__customer_connections: Dict[int, WebSocket] = {}

    def set_session(self, db: Session):
        self.__db = db

    async def connect(
        self, user_type: auth_schemas.UserType, user_id: int, websocket: WebSocket
    ) -> None:
        if user_type == auth_schemas.UserType.MASTER:
            self.__master_connections[user_id] = websocket
        else:
            self.__customer_connections[user_id] = websocket

        await websocket.accept()

        try:
            while True:
                message_json = await websocket.receive_text()
                message_dict = json.loads(message_json)
                message = schemas.Message(**message_dict)
                await self.send_message(message=message)

        except WebSocketDisconnect:
            await self.disconnect(user_type=user_type, user_id=user_id)

    async def send_message(self, message: schemas.Message):
        chatContains = queries.ChatContainsUserQuery(
            db=self.__db, chat_id=message.chat_id
        )
        from_user_id = message.from_user_id
        to_user_id = message.to_user_id

        if chatContains(user_id=to_user_id) and chatContains(user_id=from_user_id):
            if message.from_user_type == auth_schemas.UserType.CUSTOMER:
                websocket = self.__master_connections.get(message.to_user_id)
            else:
                websocket = self.__customer_connections.get(message.to_user_id)

            chat_service = ChatService(db=self.__db)
            chat_service.add_message(message=message)

            if websocket is not None:
                await websocket.send_text(message.model_dump_json(by_alias=True))

    async def close(self, websocket: WebSocket):
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()

    async def disconnect(self, user_type: auth_schemas.UserType, user_id: int) -> None:
        if user_type == auth_schemas.UserType.MASTER:
            connections = self.__master_connections
        else:
            connections = self.__customer_connections

        websocket = connections.get(user_id)

        if websocket is not None:
            await self.close(websocket=websocket)
            del connections[user_id]
