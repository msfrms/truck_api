from fastapi import APIRouter, Depends, Query, WebSocket
from fastapi.security import HTTPAuthorizationCredentials

from sqlalchemy.orm import Session

from auth.dependency import get_credentials, get_security_access

from app.database import get_db

from chat.services import ChatService, UserConnectionsService


router = APIRouter(prefix="/chat", tags=["Chat"])

connections_service = UserConnectionsService()


@router.get("/order/{order_id}/messages")
async def get_all_messages(
    order_id: int,
    credentials: HTTPAuthorizationCredentials = get_credentials(),
    db: Session = Depends(get_db),
):
    user_id = credentials["id"]
    chat_service = ChatService(db=db)
    return chat_service.get_all_messages(order_id=order_id, user_id=user_id)


@router.websocket("/order/{order_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    order_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    brearer = get_security_access()
    params = brearer._decode(token=token)

    subject = params["subject"]
    user_id = subject["id"]
    user_type = subject["user_type"]

    connections_service.set_session(db=db)

    await connections_service.connect(
        user_id=user_id, user_type=user_type, websocket=websocket
    )
