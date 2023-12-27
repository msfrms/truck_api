from typing import List

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials

from order.services.order_service import OrderService, to_order
from order.services.transport_service import TransportService
import order.schemas as schemas

from order.tasks.tasks import schedule_tg_order_new_notify

from sqlalchemy.orm import Session

from app.database import get_db

from auth.dependency import get_credentials
from order.services.new_order_notifier import NewOrderNotifier


router = APIRouter(prefix="/order", tags=["Order"])


@router.post("/", response_model=schemas.OrderCreated)
async def create_order(
    order: schemas.PostOrder,
    credentials: HTTPAuthorizationCredentials = get_credentials(),
    db: Session = Depends(get_db),
):
    id: int = credentials["id"]
    order = OrderService.create_order(order=order, customer_id=id, db=db)
    schedule_tg_order_new_notify.delay(order.id)

    return schemas.OrderCreated(order_number=order.order_number, order_id=order.id)


@router.post("/anonymous", response_model=schemas.OrderCreated)
async def create_order(
    order: schemas.PostOrder,
    db: Session = Depends(get_db),
):
    order = OrderService.create_order_without_register(order=order, db=db)
    schedule_tg_order_new_notify.delay(order.id)
    return schemas.OrderCreated(order_number=order.order_number, order_id=order.id)


@router.get("/my", response_model=List[schemas.GetOrderList])
async def get_my_orders(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = get_credentials(),
    page: int = 0,
    limit: int = 20,
):
    user_type = credentials["user_type"]
    user_id = credentials["id"]
    order_service = OrderService(db=db)

    return order_service.get_my_list(
        user_id=user_id, user_type=user_type, offset=page, limit=min(20, limit)
    )


@router.get("/all", response_model=List[schemas.GetOrderList])
async def get_all_orders(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = get_credentials(),
    page: int = 0,
    limit: int = 20,
):
    user_type = credentials["user_type"]
    user_id = credentials["id"]
    order_service = OrderService(db=db)

    return order_service.get_all_orders(
        user_id=user_id, user_type=user_type, offset=page, limit=min(limit, 20)
    )


@router.post(
    "/{order_id}/transport/{transport_id}",
    response_model=schemas.Order,
)
async def set_extra_values(
    order_id: int,
    transport_id: int,
    extra_values: schemas.UpdateTransportExtraValues,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = get_credentials(),
):
    order_service = OrderService(db=db)

    user_type = credentials["user_type"]
    user_id = credentials["id"]

    order_service.check_access_user_to_order(
        order_id=order_id, user_id=user_id, user_type=user_type
    )

    transport_service = TransportService(db=db)
    transport_service.setExtraValues(
        order_id=order_id, transport_id=transport_id, values=extra_values
    )

    return OrderService(db=db).order_by_id(
        id=order_id, user_type=user_type, user_id=user_id
    )


@router.get("/{order_id}", response_model=schemas.Order)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = get_credentials(),
):
    user_type = credentials["user_type"]
    user_id = credentials["id"]
    order = OrderService(db=db).order_by_id(
        id=order_id, user_type=user_type, user_id=user_id
    )
    return order


@router.get("/{order_id}/anonymous", response_model=schemas.Order)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    order = OrderService(db=db).anonymous_order_by_id(id=order_id)
    return order


@router.put("/{order_id}/cancel", response_model=schemas.Order)
async def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = get_credentials(),
):
    user_type = credentials["user_type"]
    user_id = credentials["id"]
    order = OrderService(db=db).cancel_order(
        id=order_id, user_type=user_type, user_id=user_id
    )

    return order


@router.post(
    "/{order_id}/status/",
    response_model=schemas.Order,
    description="Update status for order_id",
)
async def set_status(
    order_id: int,
    order: schemas.SetStatus,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = get_credentials(),
):
    order_service = OrderService(db=db)
    user_type = credentials["user_type"]
    user_id = credentials["id"]

    new_order = order_service.set_status(
        order_status=order.status,
        order_id=order_id,
        user_type=user_type,
        user_id=user_id,
    )

    return to_order(new_order, user_type=user_type, db=db)


@router.post(
    "/{order_id}/jobs/",
    description="Update jobs for order_id",
    response_model=schemas.Order,
)
async def update_jobs(
    order_id: int,
    transports: List[schemas.UpdateJob],
    credentials: HTTPAuthorizationCredentials = get_credentials(),
    db: Session = Depends(get_db),
):
    user_type = credentials["user_type"]
    user_id = credentials["id"]

    order_service = OrderService(db=db)
    order = order_service.update_jobs(
        transports=transports, order_id=order_id, user_id=user_id
    )

    return to_order(order, user_type=user_type, db=db)
