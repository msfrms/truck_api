from sqlalchemy import Column, Integer, String, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Contact(Base):
    __tablename__ = "contact"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, unique=False, index=True)
    phone = Column(String, unique=True, index=True)

    is_active = Column(Boolean)
    is_verified = Column(Boolean)

    __table_args__ = (UniqueConstraint(phone),)

    customer = relationship("Customer", back_populates="contact", uselist=False)
    master = relationship("Master", back_populates="contact", uselist=False)


class Address(Base):
    __tablename__ = "address"

    id = Column(Integer, primary_key=True, index=True)
    # адрес (улица, проспект итд)
    address = Column(String, index=False, unique=False, nullable=True)
    # город (населенный пункт)
    city = Column(String, index=True, unique=False, nullable=True)
    # область
    region = Column(String, index=True, unique=False, nullable=True)

    __table_args__ = (UniqueConstraint(city, region, address),)
