from __future__ import annotations

import math

from enum import Enum

from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field

from core.schemas import CamelModel, Contact

import chat.schemas as chat_schemas


class Task(CamelModel):
    name: str
    agreed: bool


class Job(CamelModel):
    category_id: int
    tasks: List[Task]


class TransportType(str, Enum):
    TRUCK = "truck"
    TRAILER = "trailer"


class Status(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    ACCEPTED_ON_MAINTENANCE = "accepted_on_maintenance"
    PROBLEM_DIAGNOSIS_BY_CONTRACTOR = "problem_diagnosis_by_contractor"
    CUSTOMER_APPROVAL = "customer_approval"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Transport(CamelModel):
    id: Optional[int] = None
    model: Optional[str] = None
    brand: str
    type: TransportType
    jobs: List[Job]
    license_number: Optional[str] = None
    vin: Optional[str] = None
    mileage: Optional[int] = None
    trailer_type: Optional[str] = None

    def job_names(self) -> List[str]:
        job_truck_names_by_id = {
            1: "Двигатель, Система охлаждения",
            2: "Топливная система",
            3: "Система выпуска",
            4: "КПП, Сцепление",
            5: "Рулевое управление",
            6: "Тормозная система. Колеса",
            7: "Шасси, Кузов",
            8: "Электрика",
            9: "ТО",
            10: "Шиномонтаж",
            11: "ТНВД / Форсунки",
            12: "Кондиционер / Печка",
            50: "Другое",
        }
        job_trailer_names_by_id = {
            52: "Тормоза",
            53: "Оси / Колеса",
            54: "Подвеска",
            55: "Электрика",
            56: "Пневматика",
            57: "Рама / Пол",
            58: "Кузов",
            59: "Реф",
            89: "Другое",
        }

        if self.type == TransportType.TRUCK:
            return [job_truck_names_by_id[job.category_id] for job in self.jobs]
        else:
            return [job_trailer_names_by_id[job.category_id] for job in self.jobs]


class Order(CamelModel):
    id: int
    status: Status
    order_number: str
    transports: List[Transport]
    update_at: datetime
    region: str
    city: str | None = None
    description: str | None = None
    customer: Contact | None = None
    master: Contact | None = None
    balance: int | None = None
    chat: chat_schemas.Chat | None = None


class PostOrder(CamelModel):
    transports: List[Transport]
    description: str
    region: str
    city: Optional[str] = None
    driver: Optional[Contact] = None
    latitude: Optional[float] = None
    longtitude: Optional[float] = None
    address: Optional[str] = None
    need_evacuator: Optional[bool] = None
    need_field_technician: Optional[bool] = None
    customer_contact: Optional[Contact] = None


class UpdateJob(CamelModel):
    transport_id: int
    jobs: List[Job]

    def total_tasks(self) -> int:
        count: int = 0

        for job in self.jobs:
            count += len(job.tasks)

        return count


class UpdateTransportExtraValues(CamelModel):
    license_number: str | None = None
    vin: str | None = Field(None, min_length=17, max_length=17)
    mileage: int | None = None


class GetTransportList(CamelModel):
    model: Optional[str] = None
    brand: str
    jobs: List[Job]
    type: TransportType


class GetOrderList(CamelModel):
    id: int
    status: Status
    order_number: str
    transports: List[GetTransportList]
    update_at: datetime
    region: str
    city: str | None = None


class SetStatus(BaseModel):
    status: Status


class OrderCreated(CamelModel):
    order_number: str
    order_id: int


class Location(CamelModel):
    latitude: float
    longtitude: float

    def in_radians(self) -> Location:
        return Location(
            latitude=math.radians(self.latitude), longtitude=math.radians(self.latitude)
        )

    def distance(self, to: Location) -> float:
        from_location = self.in_radians()
        to_location = to.in_radians()

        # Haversine formula
        # https://www.geeksforgeeks.org/program-distance-two-points-earth/

        distance_lon = to.longtitude - from_location.longtitude
        distance_lat = to.latitude - from_location.latitude

        a = (
            math.sin(distance_lat / 2) ** 2
            + math.cos(from_location.latitude)
            * math.cos(to_location.latitude)
            * math.sin(distance_lon / 2) ** 2
        )

        c = 2 * math.asin(math.sqrt(a))

        radius_earth_km = 6371

        return c * radius_earth_km
