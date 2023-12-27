from sqlalchemy.orm import Session, load_only

import order.models as models
import order.schemas as schemas


class ChatIdByOrderIdQuery:
    def __init__(self, db: Session):
        self.__db = db

    def __call__(self, order_id: int) -> int | None:
        return (
            self.__db.query(models.Order)
            .with_entities(models.Order.chat_id)
            .filter(models.Order.id == order_id)
            .first()[0]
        )


class OrderHasChatQuery:
    def __init__(self, db: Session):
        self.__db = db

    def __call__(self, order_id: int) -> int:
        order = (
            self.__db.query(models.Order)
            .options(load_only(models.Order.chat_id, models.Order.status))
            .filter(models.Order.id == order_id)
            .first()
        )

        return (
            order.chat_id is not None
            and order.status != schemas.Status.CANCELLED
            and order.status != schemas.Status.CREATED
        )


class UserHasAccessToOrderQuery:
    def __init__(self, db: Session):
        self.__db = db

    def __call__(self, user_id: int, order_id: int) -> bool:
        order: models.Order = (
            self.__db.query(models.Order)
            .options(load_only(models.Order.master_id, models.Order.customer_id))
            .filter(models.Order.id == order_id)
            .first()
        )
        return order.master_id == user_id or order.customer_id == user_id
