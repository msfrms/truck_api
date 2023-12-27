from fastapi import HTTPException, status
from fastapi_jwt import JwtAccessBearer

from sqlalchemy.orm import Session

import auth.schemas as schemas
from auth.services.customer_service import CustomerService
from auth.services.master_service import MasterService
from auth.services.token_service import TokenService

from core.errors import Error


class AuthService:
    def __init__(self, db: Session, authorize: JwtAccessBearer) -> None:
        self.__customer_service = CustomerService(db=db)
        self.__master_service = MasterService(db=db)
        self.__token_service = TokenService(authorize=authorize)

    def register_customer(self, customer: schemas.CreateCustomer) -> schemas.Token:
        db_customer = self.__customer_service.get_customer_by(email=customer.email)

        if db_customer is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Error.USER_ALREADY_EXISTS,
            )

        customer = self.__customer_service.create_customer(customer)

        return self.__token_service.create_token(
            user_id=customer.id, user_type=schemas.UserType.CUSTOMER
        )

    def login_customer(self, customer: schemas.Login) -> schemas.Token:
        db_customer = self.__customer_service.get_customer_by(email=customer.email)

        self.__token_service.check_user_for_login(
            user=db_customer, password=customer.password
        )

        return self.__token_service.create_token(
            user_id=db_customer.id, user_type=schemas.UserType.CUSTOMER
        )

    def register_master(self, master: schemas.CreateMaster) -> schemas.Token:
        db_master = self.__master_service.get_master_by(email=master.email)

        if db_master is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Error.USER_ALREADY_EXISTS,
            )

        master = self.__master_service.create_master(master)

        return self.__token_service.create_token(
            user_id=master.id, user_type=schemas.UserType.MASTER
        )

    def login_master(self, master: schemas.Login) -> schemas.Token:
        db_master = self.__master_service.get_master_by(email=master.email)

        self.__token_service.check_user_for_login(
            user=db_master, password=master.password
        )

        return self.__token_service.create_token(
            user_id=db_master.id, user_type=schemas.UserType.MASTER
        )
