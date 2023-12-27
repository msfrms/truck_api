from typing import List, Optional

from sqlalchemy.orm import Session

import order.schemas as schemas
import order.models as models

from fastapi import HTTPException, status

from core.errors import Error


class TransportService:
    def __init__(self, db: Session) -> None:
        self.__db = db

    def create_transports(
        self, transports: List[schemas.Transport], order: models.Order
    ):
        transport_service = TransportService(db=self.__db)

        for transport in transports:
            link = transport_service.__create_transport_link(transport)
            link.order = order
            if link.id is None:
                self.__db.add(link)
                self.__db.flush()
                transport_service.__create_job_links(
                    jobs=transport.jobs,
                    order_id=order.id,
                    transport_id=link.transport_id,
                )

    def setExtraValues(
        self,
        order_id: int,
        transport_id: int,
        values: schemas.UpdateTransportExtraValues,
    ):
        transport_link: models.TransportLink = (
            self.__db.query(models.TransportLink)
            .filter_by(order_id=order_id, transport_id=transport_id)
            .with_for_update()
            .first()
        )

        if values.license_number is not None and values.license_number != "":
            transport_link.license_number = values.license_number

        if values.vin is not None:
            vin_links = (
                self.__db.query(models.TransportLink)
                .filter_by(order_id=order_id, vin=values.vin)
                .all()
            )
            if len(vin_links) == 0:
                transport_link.vin = values.vin
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=Error.VIN_ALREADY_EXISTS_IN_ORDER,
                )

        if values.mileage is not None:
            transport_link.mileage = values.mileage

        self.__db.commit()

    def update_jobs_in(self, transports: List[schemas.UpdateJob], order_id: int):
        for transport in transports:
            self.__prepare_to_update_jobs(
                order_id=order_id, transport_id=transport.transport_id
            )
            for job in transport.jobs:
                db_job = self.__get_or_create_job(job=job)
                self.__db.flush()
                if len(job.tasks) == 0:
                    link = models.JobLink(
                        order_id=order_id,
                        job=db_job,
                        transport_id=transport.transport_id,
                    )
                    self.__db.add(link)
                else:
                    for task in job.tasks:
                        db_task = self.__get_or_create_task(task=task)
                        link = models.JobLink(
                            order_id=order_id,
                            job=db_job,
                            task=db_task,
                            transport_id=transport.transport_id,
                        )
                        self.__db.add(link)

    def __get_or_create_transport(
        self, transport: schemas.Transport
    ) -> Optional[models.Transport]:
        db_transport = (
            self.__db.query(models.Transport)
            .filter_by(
                model=transport.model,
                brand=transport.brand,
                type=transport.type,
                trailer_type=transport.trailer_type,
            )
            .first()
        )

        if db_transport is None:
            db_transport = models.Transport()
            db_transport.brand = transport.brand
            db_transport.model = transport.model
            db_transport.type = transport.type
            db_transport.trailer_type = transport.trailer_type

        return db_transport

    def __create_transport_link(
        self, transport: schemas.Transport
    ) -> models.TransportLink:
        transport_link = models.TransportLink()
        transport_link.transport = self.__get_or_create_transport(transport)

        if transport.license_number is not None:
            transport_link.license_number = transport.license_number

        if transport.vin is not None:
            transport_link.vin = transport.vin

        if transport.mileage is not None:
            transport_link.mileage = transport.mileage

        return transport_link

    def __get_or_create_job(self, job: schemas.Job) -> models.Job:
        db_job = (
            self.__db.query(models.Job)
            .filter(models.Job.category_id == job.category_id)
            .first()
        )

        if db_job is None:
            return models.Job(category_id=job.category_id)
        else:
            return db_job

    def __get_or_create_task(self, task: schemas.Task) -> models.Task:
        db_task = (
            self.__db.query(models.Task).filter(models.Task.name == task.name).first()
        )

        if db_task is None:
            return models.Task(name=task.name, agreed=task.agreed)
        else:
            return db_task

    def __create_job_links(
        self, jobs: List[schemas.Job], order_id: int, transport_id: int
    ) -> models.TransportLink:
        for job in jobs:
            job_link: models.JobLink = models.JobLink()
            job_link.order_id = order_id
            job_link.transport_id = transport_id
            job_link.job = self.__get_or_create_job(job=job)
            self.__db.add(job_link)

    def __prepare_to_update_jobs(self, order_id: int, transport_id):
        db_links = (
            self.__db.query(models.JobLink)
            .filter_by(order_id=order_id, transport_id=transport_id)
            .all()
        )

        for db_link in db_links:
            self.__db.delete(db_link)
