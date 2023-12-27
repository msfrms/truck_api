from sqlalchemy.orm import Session


from auth.services.master_service import MasterService

from app.config import settings


class NewOrderNotifier:
    def __init__(self, db: Session) -> None:
        self.__db = db

    def notify(self, order_id: int):
        from order.services.order_service import OrderService
        from order.tasks.tasks import tg_new_order_notify

        order = OrderService(db=self.__db).anonymous_order_by_id(id=order_id)

        if order is None:
            return

        master_service = MasterService(db=self.__db)
        masters = master_service.all_masters_by_region(
            region=order.region, city=order.city
        )

        for master in masters:
            brand = order.transports[0].brand
            model = order.transports[0].model
            error_text = ", ".join(order.transports[0].job_names())
            city: str = f"({order.city})" if order.city is not None else ""
            message = (
                f"В регионе: {order.region} {city} доступна заявка № {order.order_number}\n"
                f"Транспортое средство: {brand} {model if model is not None else ''}\n"
                f"Неисправность: {error_text}\n"
                f"{settings.CLIENT_ORIGIN}/master/order/{order.id}"
            )

            tg_new_order_notify.delay(chat_id=master.tg_chat_id, message=message)
