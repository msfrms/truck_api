from passlib.context import CryptContext


class EncryptionService:
    def __init__(self) -> None:
        self.__pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return self.__pwd_context.verify(password, hashed_password)

    def create_password_hash(self, password: str) -> str:
        return self.__pwd_context.hash(password)
