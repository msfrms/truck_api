from typing import Optional
from sqlalchemy.orm import Session

import core.models as models

import core.schemas as schemas


class ContactService:
    def __init__(self, db: Session) -> None:
        self.__db = db

    def get_by_id(self, id: int) -> Optional[models.Contact]:
        return self.__db.query(models.Contact).filter_by(id=id).first()

    def get_or_create(self, contact: schemas.Contact) -> models.Contact:
        if db_contact := (
            self.__db.query(models.Contact).filter_by(phone=contact.phone).first()
        ):
            return db_contact
        else:
            return models.Contact(name=contact.name, phone=contact.phone)

    def get_or_create_address(
        self, address: Optional[str], region: Optional[str], city: Optional[str]
    ) -> models.Address:
        if db_address := (
            self.__db.query(models.Address)
            .filter_by(address=address, region=region, city=city)
            .first()
        ):
            return db_address
        else:
            return models.Address(address=address, region=region, city=city)
