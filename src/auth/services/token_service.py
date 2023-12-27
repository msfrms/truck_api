from fastapi import HTTPException, status

import auth.schemas as schemas
from auth.services.encryption_service import EncryptionService

from core.errors import Error

from fastapi_jwt import JwtAccessBearer

from datetime import timedelta

from app.config import settings


class TokenService:
    def __init__(self, authorize: JwtAccessBearer) -> None:
        self.__encryption_service = EncryptionService()
        self.__authorize = authorize

    def create_token(self, user_id: int, user_type: schemas.UserType) -> schemas.Token:
        payload = schemas.User(id=user_id, user_type=user_type)

        access_token = self.__authorize.create_access_token(
            subject=payload.model_dump(),
            expires_delta=timedelta(weeks=settings.ACCESS_TOKEN_EXPIRES_IN),
        )
        refresh_token = self.__authorize.create_access_token(
            subject=payload.model_dump(),
            expires_delta=timedelta(weeks=settings.REFRESH_TOKEN_EXPIRES_IN),
        )

        return schemas.Token(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user_id,
        )

    def check_user_for_login(self, user, password: str):
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Error.INCORRECT_EMAIL_OR_PASSOWRD,
            )

        is_verify_password = self.__encryption_service.verify_password(
            password, hashed_password=user.password_hashed
        )

        if not is_verify_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Error.INCORRECT_EMAIL_OR_PASSOWRD,
            )
