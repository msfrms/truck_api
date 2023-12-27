from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Boolean,
    Float,
    DateTime,
    BigInteger,
)
from sqlalchemy.orm import relationship

import order.schemas as order_schemas

from app.database import Base


class Account(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Integer, unique=False)


class Customer(Base):
    __tablename__ = "customer"

    id = Column(Integer, primary_key=True, index=True)

    account_id = Column(Integer, ForeignKey("account.id"), nullable=True)
    account = relationship("Account")

    contact_id = Column(Integer, ForeignKey("contact.id"), nullable=False)
    contact = relationship("Contact", back_populates="customer")

    login = Column(String, unique=True, index=True)

    # Название организации (опционально для юр лиц)
    name = Column(String, unique=False, index=True, nullable=True)
    # ИНН (опционально для юр лиц)
    inn = Column(String, unique=True, index=True, nullable=True)

    address_id = Column(Integer, ForeignKey("address.id"), nullable=False)
    address = relationship("Address")
    latitude = Column(Float, unique=True, index=False, nullable=True)
    longtitude = Column(Float, unique=True, index=False, nullable=True)

    is_active = Column(Boolean, index=True)
    is_verified = Column(Boolean, index=True)

    password_hashed = Column(String, index=True)

    created_at = Column(DateTime, unique=False, index=False)

    orders = relationship("Order", back_populates="customer")


class Master(Base):
    __tablename__ = "master"

    id = Column(Integer, primary_key=True, index=True)

    tg_chat_id = Column(BigInteger, unique=True, index=True, nullable=True)
    contact_id = Column(Integer, ForeignKey("contact.id"), nullable=False)
    contact = relationship("Contact", back_populates="master")

    login = Column(String, unique=True, index=True)

    # Фирменное Название (СТО или выездной бригады)
    name = Column(String, unique=False, index=True, nullable=False)
    inn = Column(String, unique=True, index=True, nullable=True)

    # допустимый радиус от местонахождения до выезда к месту поломки заказчика (СТО или выездной бригады)
    trip_radius = Column(Float, unique=False, nullable=True)

    account_id = Column(Integer, ForeignKey("account.id"), nullable=False)
    account = relationship("Account")

    # Адрес местонахождения
    address_id = Column(Integer, ForeignKey("address.id"), nullable=False)
    address = relationship("Address")
    latitude = Column(Float, unique=False, index=True, nullable=True)
    longtitude = Column(Float, unique=False, index=True, nullable=True)

    is_active = Column(Boolean, index=True)
    is_verified = Column(Boolean, index=True)
    is_paid = Column(Boolean, index=True)

    password_hashed = Column(String, index=True)

    created_at = Column(DateTime, unique=False, index=False)

    orders = relationship("Order", back_populates="master")

    def geo_location(self) -> Optional[order_schemas.Location]:
        if self.latitude is not None and self.longtitude is not None:
            return order_schemas.Location(
                latitude=self.latitude, longtitude=self.longtitude
            )
        else:
            return None
