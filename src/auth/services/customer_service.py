from typing import Optional
from datetime import datetime

import auth.models as models
import auth.schemas as schemas

from core.services.contact_service import ContactService

from .encryption_service import EncryptionService

from sqlalchemy.orm import Session


class CustomerService:
    def __init__(self, db: Session) -> None:
        self.__db = db
        self.__contact_service = ContactService(db=db)
        self.__encryption_service = EncryptionService()

    def get_customer_by(self, email: str) -> Optional[models.Customer]:
        if customer := self.__db.query(models.Customer).filter_by(login=email).first():
            return customer
        else:
            return None

    def get_customer_by_id(self, id: int) -> Optional[models.Customer]:
        if customer := self.__db.query(models.Customer).filter_by(id=id).first():
            return customer
        else:
            return None

    def create_customer(self, customer: schemas.CreateCustomer) -> models.Customer:
        db_customer = models.Customer()
        db_customer.name = customer.name
        db_customer.inn = customer.inn
        db_customer.address = ContactService(db=self.__db).get_or_create_address(
            address=None, region=customer.region, city=customer.city
        )
        db_customer.login = customer.email
        db_customer.password_hashed = self.__encryption_service.create_password_hash(
            customer.password
        )
        db_customer.created_at = datetime.utcnow()

        db_contact = self.__contact_service.get_or_create(contact=customer.contact)
        db_customer.contact = db_contact

        is_new_contact = db_contact.id is None

        if is_new_contact:
            db_customer.contact = db_contact

        self.__db.add(db_customer)
        self.__db.flush()

        if not is_new_contact:
            from order.services.order_service import OrderService

            db_customer.contact = db_contact
            order_service = OrderService(db=self.__db)
            order_service.link_orders(
                with_contact_id=db_contact.id, to_customer_id=db_customer.id
            )

        self.__db.commit()

        return db_customer
