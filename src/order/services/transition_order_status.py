from typing import Dict, List
from datetime import datetime

from fastapi import HTTPException, status

from sqlalchemy.orm import Session

import order.models as models
import order.schemas as schemas

import auth.schemas as auth_schemas
from auth.services.master_service import MasterService

from core.errors import Error

from chat.services import ChatService


class TrasitionOrderStatus:
    def __init__(self, db: Session, order: models.Order) -> None:
        self.__db = db
        self.__order = order

    def try_move_status_to_progress(self, user_id: int) -> None:
        order = self.__order

        if order.status == schemas.Status.CREATED:
            if order.master_id is None:
                order.master_id = user_id
                order.status = schemas.Status.IN_PROGRESS
                MasterService(db=self.__db).decrease_balance(
                    value=order.get_cost(), user_id=user_id
                )
                if order.customer_id is not None:
                    chat = ChatService(db=self.__db).create_chat(
                        master_id=order.master_id, customer_id=order.customer_id
                    )
                    order.chat_id = chat.id
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=Error.ORDER_ALREADY_IN_PROGRESS,
                )

    def get_available_statuses_by_user(
        self,
    ) -> Dict[auth_schemas.UserType, List[schemas.Status]]:
        return {
            auth_schemas.UserType.CUSTOMER: [
                schemas.Status.CREATED,
                schemas.Status.CUSTOMER_APPROVAL,
                schemas.Status.COMPLETED,
            ],
            auth_schemas.UserType.MASTER: [
                schemas.Status.IN_PROGRESS,
                schemas.Status.ACCEPTED_ON_MAINTENANCE,
                schemas.Status.PROBLEM_DIAGNOSIS_BY_CONTRACTOR,
            ],
        }

    def try_exception_if_not_allowed_to_change_status(
        self, status: schemas.Status, user_type: auth_schemas.UserType
    ):
        available_order_statuses = self.get_available_statuses_by_user().get(user_type)

        if status not in available_order_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Error.CHANGE_STATUS_NOT_ALLOWED,
            )

    def try_change_status(
        self, status: schemas.Status, user_type: auth_schemas.UserType, user_id: int
    ) -> None:
        order = self.__order
        self.try_exception_if_not_allowed_to_change_status(
            status=status, user_type=user_type
        )

        if status == schemas.Status.IN_PROGRESS:
            self.try_move_status_to_progress(user_id=user_id)
        else:
            order.status = status
            order.updated_at = datetime.utcnow()

        self.make_history(status=status)

    def make_history(self, status: schemas.Status) -> None:
        order_history = models.OrderHistory()
        order_history.order_id = self.__order.id
        order_history.status = status
        order_history.created_at = datetime.utcnow()
        order_history.master_id = self.__order.master_id

        self.__db.add(order_history)
