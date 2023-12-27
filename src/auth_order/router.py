from fastapi import APIRouter, Depends

import auth_order.schemas as schemas

from auth.services.auth_service import AuthService
from auth.dependency import get_security_access

from app.database import get_db

from sqlalchemy.orm import Session

from fastapi_jwt.jwt import JwtAccess

from order.services.order_service import OrderService

from auth_order.schemas import OrderCreated


router = APIRouter(prefix="/auth/order", tags=["Auth"])


@router.post(
    "/register/customer/",
    response_model=OrderCreated,
    summary="Register customer with order",
)
async def customer_register_with_order(
    user: schemas.CreateCustomerWithOrder,
    db: Session = Depends(get_db),
    access: JwtAccess = Depends(get_security_access),
):
    auth_service = AuthService(db=db, authorize=access)
    token = auth_service.register_customer(user.customer)
    order = OrderService.create_order(user.order, customer_id=token.user_id, db=db)
    return OrderCreated(order_number=order.order_number, token=token, order_id=order.id)


@router.post(
    "/login/customer/",
    response_model=OrderCreated,
    summary="Login customer with order",
)
async def customer_login_with_order(
    data: schemas.LoginCustomerWithOrder,
    db: Session = Depends(get_db),
    access: JwtAccess = Depends(get_security_access),
):
    auth_service = AuthService(db=db, authorize=access)
    token = auth_service.login_customer(customer=data.login)
    order = OrderService.create_order(data.order, customer_id=token.user_id, db=db)
    return OrderCreated(order_number=order.order_number, token=token, order_id=order.id)
