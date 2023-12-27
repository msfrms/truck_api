from typing import Optional
from pydantic import BaseModel
from humps import camelize


class CamelModel(BaseModel):
    class Config:
        alias_generator = camelize
        populate_by_name = True
        use_enum_values = True


class Contact(CamelModel):
    name: str
    phone: str
