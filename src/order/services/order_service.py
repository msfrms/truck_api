from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status

from sqlalchemy.orm import Session

import order.schemas as schemas
import order.models as models
import order.utils as utils
from order.services.transport_service import TransportService
from order.constants import ORDER_PRICE_ONE_JOB_CATEGORY
from order.services.transition_order_status import TrasitionOrderStatus

from core.errors import Error
import core.models as core_models
from core.services.contact_service import ContactService

from auth.services.customer_service import CustomerService
from auth.services.master_service import MasterService
import auth.schemas as auth_schemas
import auth.models as auth_models


import chat.schemas as chat_schemas
import chat.models as chat_models


def to_order(
    order: models.Order, user_type: auth_schemas.UserType, db: Session
) -> schemas.Order:
    driver: Optional[schemas.Contact] = None
    new_order: Optional[schemas.Order] = None

    if driver is not None:
        driver = schemas.Contact(name=order.driver.name, phone=order.driver.phone)

    if (
        order.status == schemas.Status.CREATED
        or order.status == schemas.Status.CANCELLED
    ) and user_type == auth_schemas.UserType.MASTER:
        new_order = schemas.Order(
            id=order.id,
            status=order.status,
            order_number=order.order_number,
            region=order.address.region,
            city=order.address.city,
            transports=order.get_transports(),
            update_at=order.updated_at,
            description=None,
            customer=None,
            master=None,
            chat=None,
        )
    else:
        customer: Optional[schemas.Contact] = None
        master: Optional[schemas.Contact] = None

        if order.customer is not None:
            customer = schemas.Contact(
                name=order.customer.contact.name, phone=order.customer.contact.phone
            )

        if order.customer_contact_id is not None:
            contact = ContactService(db=db).get_by_id(id=order.customer_contact_id)
            customer = schemas.Contact(name=contact.name, phone=contact.phone)

        if order.master is not None:
            master = schemas.Contact(
                name=order.master.contact.name, phone=order.master.contact.phone
            )

        new_order = schemas.Order(
            id=order.id,
            status=order.status,
            order_number=order.order_number,
            region=order.address.region,
            city=order.address.city,
            transports=order.get_transports(),
            update_at=order.updated_at,
            description=order.description,
            customer=customer,
            master=master,
            chat=None,
        )

        if user_type == auth_schemas.UserType.MASTER and order.master is not None:
            new_order.balance = order.master.account.balance

    if order.status != schemas.Status.CREATED and order.chat is not None:
        chat: chat_models.Chat = order.chat
        new_order.chat = chat_schemas.Chat(
            id=chat.id,
            customer_id=chat.customer_id,
            master_id=chat.master_id,
        )

    return new_order


class OrderService:
    def __init__(self, db: Session) -> None:
        self.__db = db
        self.__transport_service = TransportService(db=db)

    @staticmethod
    def __get_driver(
        from_order: schemas.PostOrder, db: Session
    ) -> Optional[core_models.Contact]:
        if from_order.driver is None:
            return None

        return ContactService(db=db).get_or_create(contact=from_order.driver)

    def link_orders(self, with_contact_id: int, to_customer_id: int):
        orders = (
            self.__db.query(models.Order)
            .filter_by(customer_contact_id=with_contact_id)
            .all()
        )

        for order in orders:
            order.customer_id = to_customer_id

    @staticmethod
    def create_order(
        order: schemas.PostOrder, customer_id: int, db: Session
    ) -> models.Order:
        customer = CustomerService(db=db).get_customer_by_id(customer_id)

        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Error.USER_NOT_EXISTS,
            )

        driver: Optional[core_models.Contact] = OrderService.__get_driver(
            from_order=order, db=db
        )

        if driver is not None and driver.id is None:
            db.add(driver)
            db.flush()

        new_order = models.Order(
            customer=customer,
            description=order.description,
            driver_id=driver.id if driver is not None else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            status=schemas.Status.CREATED,
            latitude=order.latitude,
            longtitude=order.longtitude,
            address=ContactService(db=db).get_or_create_address(
                address=order.address, region=order.region, city=order.city
            ),
            need_evacuator=order.need_evacuator,
            need_field_technician=order.need_field_technician,
        )

        db.add(new_order)
        db.flush()

        TransportService(db=db).create_transports(
            transports=order.transports, order=new_order
        )

        db.commit()

        return new_order

    @staticmethod
    def create_order_without_register(
        order: schemas.PostOrder, db: Session
    ) -> models.Order:
        customer_contact = ContactService(db=db).get_or_create(
            contact=order.customer_contact
        )

        if customer_contact.id is None:
            db.add(customer_contact)
            db.flush()

        driver: Optional[core_models.Contact] = OrderService.__get_driver(
            from_order=order, db=db
        )

        if driver is not None and driver.id is None:
            db.add(driver)
            db.flush()

        new_order = models.Order(
            description=order.description,
            driver_id=driver.id if driver is not None else None,
            customer_contact_id=customer_contact.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            status=schemas.Status.CREATED,
            latitude=order.latitude,
            longtitude=order.longtitude,
            address=ContactService(db=db).get_or_create_address(
                address=order.address, region=order.region, city=order.city
            ),
            need_evacuator=order.need_evacuator,
            need_field_technician=order.need_field_technician,
        )

        db.add(new_order)
        db.flush()

        TransportService(db=db).create_transports(
            transports=order.transports, order=new_order
        )

        db.commit()

        return new_order

    def clone(self, from_order: models.Order) -> models.Order:
        new_order = models.Order(
            description=from_order.description,
            driver_id=from_order.driver_id,
            customer_contact_id=from_order.customer_contact_id,
            created_at=from_order.created_at,
            updated_at=datetime.utcnow(),
            status=schemas.Status.CREATED,
            latitude=from_order.latitude,
            longtitude=from_order.longtitude,
            address_id=from_order.address_id,
            need_evacuator=from_order.need_evacuator,
            need_field_technician=from_order.need_field_technician,
            master_id=from_order.master_id,
            customer_id=from_order.customer_id,
            clone_order_id=from_order.id,
            chat_id=from_order.chat_id,
        )

        self.__db.flush()

        transports = from_order.get_transports()

        TransportService(db=self.__db).create_transports(
            transports=transports, order=new_order
        )

        return new_order

    def order_by(self, id: int, for_update: bool = False) -> Optional[models.Order]:
        if not for_update:
            return self.__db.query(models.Order).filter_by(id=id).first()
        else:
            return (
                self.__db.query(models.Order).filter_by(id=id).with_for_update().first()
            )

    def order_by_id(
        self,
        id: int,
        user_type: auth_schemas.UserType,
        user_id: int,
        for_update: bool = False,
    ) -> Optional[schemas.Order]:
        order = self.order_by(id=id, for_update=for_update)

        if (
            user_type == auth_schemas.UserType.MASTER
            and order.status == schemas.Status.IN_PROGRESS
            and order.master_id != user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=Error.ACCESS_DENIED
            )

        new_order = to_order(order=order, user_type=user_type, db=self.__db)

        if user_type == auth_schemas.UserType.MASTER and new_order.balance is None:
            master = MasterService(db=self.__db).get_master_by_id(id=user_id)
            new_order.balance = master.account.balance

        return new_order

    def anonymous_order_by_id(
        self,
        id: int,
        for_update: bool = False,
    ) -> Optional[schemas.Order]:
        order = self.order_by(id=id, for_update=for_update)

        new_order = to_order(
            order=order, user_type=auth_schemas.UserType.CUSTOMER, db=self.__db
        )

        if order.status != schemas.Status.CREATED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=Error.ACCESS_DENIED
            )

        return new_order

    def check_access_user_to_order(
        self, order_id: int, user_id: int, user_type: auth_schemas.UserType
    ):
        order = self.order_by(id=order_id)

        if order is None:
            return

        if (
            user_type == auth_schemas.UserType.MASTER
            and order.master_id != user_id
            or user_type == auth_schemas.UserType.CUSTOMER
            and order.customer_id != user_id
            or order.status == schemas.Status.CANCELLED
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=Error.ACCESS_DENIED
            )

    def cancel_order(
        self, id: int, user_id: int, user_type: auth_schemas.UserType
    ) -> Optional[schemas.Order]:
        order = self.order_by(id=id, for_update=True)

        if order is None:
            return None

        if (
            user_type == auth_schemas.UserType.MASTER
            or user_type == auth_schemas.UserType.CUSTOMER
            and order.customer_id != user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=Error.ACCESS_DENIED
            )

        if order.status == schemas.Status.CREATED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Error.CANCEL_ORDER_NOT_ALLOWED,
            )

        cloned_order = self.clone(from_order=order)
        cloned_order.status = schemas.Status.CANCELLED
        self.__db.add(cloned_order)

        order_history = models.OrderHistory()
        order_history.order_id = order.id
        order_history.status = schemas.Status.CANCELLED
        order_history.created_at = datetime.utcnow()
        order_history.master_id = order.master_id
        self.__db.add(order_history)

        updates = order.get_updates_for_reset_jobs()

        self.__update_jobs_in_order(order=order, transports=updates)

        order.status = schemas.Status.CREATED
        order.updated_at = datetime.utcnow()
        order.master_id = None
        order.chat_id = None

        self.__db.commit()

        return to_order(order=order, user_type=user_type, db=self.__db)

    def __update_jobs_in_order(
        self, order: models.Order, transports: List[schemas.UpdateJob]
    ):
        if order is None:
            return None

        self.__transport_service.update_jobs_in(
            transports=transports, order_id=order.id
        )

    def update_jobs(
        self, transports: List[schemas.UpdateJob], order_id: int, user_id: int
    ) -> Optional[models.Order]:
        order = self.order_by(id=order_id, for_update=True)

        if order.master_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Error.ACCESS_DENIED,
            )

        self.__update_jobs_in_order(order=order, transports=transports)

        order.status = schemas.Status.PROBLEM_DIAGNOSIS_BY_CONTRACTOR
        order.updated_at = datetime.utcnow()

        self.__db.commit()

        return order

    def buy_slots(self, jobs: List[schemas.UpdateJob], user_id: int) -> int:
        master_service = MasterService(db=self.__db)

        total_tasks = 0

        for job in jobs:
            total_tasks += job.total_tasks()

        cost = ORDER_PRICE_ONE_JOB_CATEGORY * total_tasks
        account = master_service.decrease_balance(value=cost, user_id=user_id)

        return account.balance

    def set_status(
        self,
        order_status: str,
        order_id: int,
        user_id: int,
        user_type: auth_schemas.UserType,
    ) -> Optional[models.Order]:
        order = self.order_by(id=order_id, for_update=True)

        if order is None:
            return None

        transition_order_status = TrasitionOrderStatus(order=order, db=self.__db)

        transition_order_status.try_change_status(
            status=order_status, user_type=user_type, user_id=user_id
        )

        self.__db.commit()
        self.__db.refresh(order)

        return order

    def get_all_orders(
        self,
        user_id: int,
        user_type: auth_schemas.UserType,
        offset: int,
        limit: int = 20,
    ) -> List[schemas.GetTransportList]:
        if user_type == auth_schemas.UserType.CUSTOMER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Error.NOT_ALLOW_OPERATION,
            )
        else:
            master_service = MasterService(db=self.__db)
            master: auth_models.Master = master_service.get_master_by_id(user_id)
            master_address: core_models.Address = master.address

            orders_query = (
                self.__db.query(models.Order)
                .join(
                    core_models.Address,
                    models.Order.address_id == core_models.Address.id,
                )
                .filter(models.Order.is_hidden == False)
                .filter(models.Order.status == schemas.Status.CREATED)
                .filter(core_models.Address.region == master_address.region)
            )

            db_orders: List[models.Order] = (
                orders_query.offset(offset).limit(limit).all()
            )
            return utils.map_orders_models_to_orders_schemas(orders=db_orders)

    def get_my_list(
        self,
        user_id: int,
        user_type: auth_schemas.UserType,
        offset: int,
        limit: int = 20,
    ) -> List[schemas.GetOrderList]:
        if user_type == auth_schemas.UserType.CUSTOMER:
            db_orders: List[models.Order] = (
                self.__db.query(models.Order)
                .filter(models.Order.customer_id == user_id)
                .filter(models.Order.status != schemas.Status.CANCELLED)
                .filter(models.Order.is_hidden == False)
                .offset(offset)
                .limit(limit)
                .all()
            )

            return utils.map_orders_models_to_orders_schemas(orders=db_orders)
        elif user_type == auth_schemas.UserType.MASTER:
            db_orders: List[models.Order] = (
                self.__db.query(models.Order)
                .filter_by(master_id=user_id)
                .filter(models.Order.is_hidden == False)
                .offset(offset)
                .limit(limit)
                .all()
            )

            return utils.map_orders_models_to_orders_schemas(orders=db_orders)

        return []
