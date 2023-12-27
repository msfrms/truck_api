from fastapi import Security

from app.config import settings

from fastapi_jwt import JwtAccessBearer

from datetime import timedelta


# Dependency
def get_credentials() -> Security:
    return Security(get_security_access())


def get_security_access():
    return JwtAccessBearer(
        secret_key=settings.JWT_PRIVATE_KEY,
        auto_error=True,
        access_expires_delta=timedelta(weeks=settings.ACCESS_TOKEN_EXPIRES_IN),
        refresh_expires_delta=timedelta(weeks=settings.REFRESH_TOKEN_EXPIRES_IN),
    )
