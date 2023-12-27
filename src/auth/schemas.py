from enum import Enum
from typing import Optional

from pydantic import EmailStr

from core.schemas import CamelModel, Contact


class UserType(str, Enum):
    MASTER = "master"
    CUSTOMER = "customer"


class CreateMaster(CamelModel):
    email: EmailStr
    contact: Contact
    name: str
    inn: Optional[str] = None
    address: Optional[str] = None
    region: str
    city: str
    trip_radius: Optional[float] = None
    password: str


class CreateCustomer(CamelModel):
    email: EmailStr
    name: Optional[str] = None
    inn: Optional[str] = None
    city: str
    region: str
    contact: Contact
    password: str


class Login(CamelModel):
    email: EmailStr
    password: str


class User(CamelModel):
    id: int
    user_type: UserType


class Token(CamelModel):
    access_token: str
    refresh_token: str
    user_id: int
