from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class Chat(Base):
    __tablename__ = "chat"

    id = Column(Integer, primary_key=True, index=True)

    created_at = Column(DateTime, nullable=False)

    messages = relationship("Message", back_populates="chat")

    master_id = Column(Integer, ForeignKey("master.id"), nullable=False)
    master = relationship("Master")

    customer_id = Column(Integer, ForeignKey("customer.id"), nullable=False)
    customer = relationship("Customer")


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, index=True)

    chat_id = Column(Integer, ForeignKey("chat.id"), nullable=False)
    chat = relationship("Chat")

    text = Column(String, nullable=False)

    from_user_type = Column(String, nullable=False)
    from_user_id = Column(Integer, nullable=False)
    to_user_id = Column(Integer, nullable=False)

    created_at = Column(DateTime, nullable=False)
