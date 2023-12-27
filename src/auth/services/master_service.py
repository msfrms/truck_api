from datetime import datetime

from typing import List, Optional

from fastapi import HTTPException, status

import auth.models as models
import auth.schemas as schemas

from .encryption_service import EncryptionService

from sqlalchemy.orm import Session
from sqlalchemy import func

from core.services.contact_service import ContactService
from core.errors import Error
import core.models as core_models


class MasterService:
    def __init__(self, db: Session) -> None:
        self.__db = db
        self.__contact_service = ContactService(db=db)
        self.__encryption_service = EncryptionService()

    def get_master_by(
        self, email: str, for_update: bool = False
    ) -> models.Master | None:
        if for_update:
            return (
                self.__db.query(models.Master)
                .filter(func.lower(models.Master.login) == func.lower(email))
                .with_for_update()
                .first()
            )
        else:
            return (
                self.__db.query(models.Master)
                .filter(func.lower(models.Master.login) == func.lower(email))
                .first()
            )

    def get_master_by_id(self, id: int) -> Optional[models.Master]:
        if master := self.__db.query(models.Master).filter_by(id=id).first():
            return master
        else:
            return None

    def decrease_balance(self, value: int, user_id: int) -> models.Account:
        master = self.get_master_by_id(user_id)
        account: models.Account = (
            self.__db.query(models.Account)
            .filter_by(id=master.account_id)
            .with_for_update()
            .first()
        )

        if account.balance >= value:
            account.balance -= value
            self.__db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Error.NOT_ENOUGH_MONEY,
            )

        return account

    def create_master(self, master: schemas.CreateMaster) -> models.Master:
        db_master = models.Master()
        db_master.address = ContactService(db=self.__db).get_or_create_address(
            address=master.address, region=master.region, city=master.city
        )
        db_master.inn = master.inn
        db_master.name = master.name
        db_master.trip_radius = master.trip_radius
        db_master.login = master.email
        db_master.account = models.Account(balance=10_000)
        db_master.password_hashed = self.__encryption_service.create_password_hash(
            master.password
        )
        db_master.created_at = datetime.utcnow()

        db_contact = self.__contact_service.get_or_create(contact=master.contact)

        if db_contact.id is None:
            db_master.contact = db_contact
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Error.USER_ALREADY_EXISTS,
            )

        self.__db.add(db_master)
        self.__db.commit()
        self.__db.refresh(db_master)

        return db_master

    def update_chat_id(self, email: str, chat_id: int) -> bool:
        master = self.get_master_by(email=email, for_update=True)

        if master is None:
            return False

        master.tg_chat_id = chat_id
        self.__db.commit()

        return True

    def all_masters_by_region(
        self, region: str, city: str | None = None
    ) -> List[models.Master]:
        masters = []
        if region == "Московская область":
            masters = (
                self.__db.query(models.Master)
                .join(core_models.Address)
                .filter_by(region=region, city=city)
                .all()
            )
        else:
            masters = (
                self.__db.query(models.Master)
                .join(core_models.Address)
                .filter_by(region=region)
                .all()
            )
        return masters
