import httpx

from app.celery import celery
from app.config import settings
from app.database import SessionLocal

from order.services.new_order_notifier import NewOrderNotifier


@celery.task
def tg_new_order_notify(chat_id: int, message: str):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    response = httpx.post(
        url,
        data={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": True,
        },
    )

    assert response.status_code == 200, "TG should return 200"


@celery.task
def schedule_tg_order_new_notify(order_id: int):
    db = SessionLocal()
    new_order = NewOrderNotifier(db=db)
    try:
        new_order.notify(order_id=order_id)
    finally:
        db.close()
