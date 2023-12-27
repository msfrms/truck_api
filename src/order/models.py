from typing import Dict, List, Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    UniqueConstraint,
    ForeignKey,
    DateTime,
    Float,
)
from sqlalchemy.orm import relationship

from app.database import Base

import order.schemas as schemas
from order.constants import ORDER_PRICE_ONE_JOB_CATEGORY

import auth.schemas as auth_schemas


class Job(Base):
    __tablename__ = "job"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, unique=True, index=True)


class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    agreed = Column(Boolean, unique=False, index=False)


class Transport(Base):
    __tablename__ = "transport"

    id = Column(Integer, primary_key=True, index=True)

    model = Column(String, index=True, nullable=True)
    brand = Column(String, index=True)

    type = Column(String, index=False, nullable=False)

    trailer_type = Column(String, index=False, nullable=True)

    __table_args__ = (UniqueConstraint(brand, model, type, trailer_type),)


class TransportLink(Base):
    __tablename__ = "transport_link"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(Integer, ForeignKey("order.id"), nullable=False)
    transport_id = Column(Integer, ForeignKey("transport.id"), nullable=False)
    license_number = Column(String, index=True, nullable=True)
    vin = Column(String, index=True, nullable=True)
    mileage = Column(Integer, nullable=True)

    __table_args__ = (UniqueConstraint(order_id, transport_id),)

    order = relationship("Order", back_populates="transport_links")
    transport = relationship("Transport")


class JobLink(Base):
    __tablename__ = "job_link"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("order.id"), nullable=False)
    transport_id = Column(Integer, ForeignKey("transport.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("job.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("task.id"), nullable=True)

    __table_args__ = (UniqueConstraint(order_id, job_id, task_id, transport_id),)

    order = relationship("Order", back_populates="job_links")
    job = relationship("Job")
    task = relationship("Task")
    transport = relationship("Transport")


class OrderHistory(Base):
    __tablename__ = "order_history"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(Integer, ForeignKey("order.id"), nullable=False)
    master_id = Column(Integer, ForeignKey("master.id"), nullable=True, index=True)
    status = Column(String, unique=False, index=False, nullable=True)
    created_at = Column(DateTime, unique=False, index=False)

    order = relationship("Order")
    master = relationship("Master")


class Order(Base):
    __tablename__ = "order"

    id = Column(Integer, primary_key=True, index=True)

    is_hidden = Column(Boolean, unique=False, index=False, default=False)

    driver_id = Column(Integer, ForeignKey("contact.id"), nullable=True, index=True)
    clone_order_id = Column(Integer, ForeignKey("order.id"), nullable=True, index=True)

    customer_id = Column(Integer, ForeignKey("customer.id"), index=True, nullable=True)
    master_id = Column(Integer, ForeignKey("master.id"), index=True)

    customer_contact_id = Column(
        Integer, ForeignKey("contact.id"), index=True, nullable=True
    )

    customer = relationship("Customer", back_populates="orders")
    master = relationship("Master", back_populates="orders")

    job_links = relationship("JobLink", back_populates="order")
    transport_links = relationship("TransportLink", back_populates="order")

    description = Column(String, unique=False, index=False)
    created_at = Column(DateTime, unique=False, index=False)
    updated_at = Column(DateTime, unique=False, index=False)
    status = Column(String, unique=False, index=True)
    latitude = Column(Float, unique=False, index=False, nullable=True)
    longtitude = Column(Float, unique=False, index=False, nullable=True)
    address_id = Column(Integer, ForeignKey("address.id"), nullable=False, index=True)
    address = relationship("Address")
    need_evacuator = Column(Boolean, unique=False, index=False, nullable=True)
    need_field_technician = Column(Boolean, unique=False, index=False, nullable=True)

    chat_id = Column(Integer, ForeignKey("chat.id"), index=True, nullable=True)
    chat = relationship("Chat")

    @property
    def order_number(self) -> str:
        number = self.created_at.strftime("%Y%m%d")
        return f"{self.id} - {number}"

    def geo_location(self) -> Optional[schemas.Location]:
        if self.latitude is not None and self.longtitude is not None:
            return schemas.Location(latitude=self.latitude, longtitude=self.longtitude)
        else:
            return None

    def get_cost(self) -> int:
        cost = 0

        for transport in self.get_transports():
            cost += len(transport.jobs) * ORDER_PRICE_ONE_JOB_CATEGORY

        return cost

    def get_updates_for_reset_jobs(self) -> List[schemas.UpdateJob]:
        trasports = self.get_transports()

        for transport in trasports:
            for job in transport.jobs:
                job.tasks = []

        updates: List[schemas.UpdateJob] = []

        for transport in trasports:
            updates.append(
                schemas.UpdateJob(transport_id=transport.id, jobs=transport.jobs)
            )

        return updates

    def get_transports(self) -> List[schemas.Transport]:
        jobs_by_transport: Dict[int, List[int]] = {}
        tasks_by_job: Dict[int, List[schemas.Task]] = {}

        for link in self.job_links:
            jobs: List[int] = jobs_by_transport.get(link.transport_id)
            tasks = tasks_by_job.get(link.job.category_id)

            if jobs is None:
                jobs = list()

            if tasks is None:
                tasks = list()

            if link.task is not None:
                tasks.append(schemas.Task(name=link.task.name, agreed=link.task.agreed))

            tasks_by_job[link.job.category_id] = tasks

            if link.job.category_id not in jobs:
                jobs.append(link.job.category_id)

            jobs_by_transport[link.transport_id] = jobs

        transports: List[schemas.Transport] = []

        for link in self.transport_links:
            job_ids = jobs_by_transport.get(link.transport.id)

            if job_ids is None:
                job_ids = []

            jobs: List[schemas.Job] = []

            for job_id in job_ids:
                tasks = tasks_by_job.get(job_id)

                if tasks is None:
                    tasks = []

                jobs.append(schemas.Job(category_id=job_id, tasks=tasks))

            transports.append(
                schemas.Transport(
                    id=link.transport.id,
                    model=link.transport.model,
                    brand=link.transport.brand,
                    trailer_type=link.transport.trailer_type,
                    jobs=jobs,
                    type=link.transport.type,
                    license_number=link.license_number,
                    vin=link.vin,
                    mileage=link.mileage,
                )
            )

        return transports

    def get_available_statuses_by_user(
        self,
    ) -> Dict[auth_schemas.UserType, List[schemas.Status]]:
        return {
            auth_schemas.UserType.CUSTOMER: [
                schemas.Status.CREATED,
                schemas.Status.CUSTOMER_APPROVAL,
                schemas.Status.COMPLETED,
            ],
            auth_schemas.UserType.MASTER: [
                schemas.Status.IN_PROGRESS,
                schemas.Status.ACCEPTED_ON_MAINTENANCE,
                schemas.Status.PROBLEM_DIAGNOSIS_BY_CONTRACTOR,
            ],
        }
