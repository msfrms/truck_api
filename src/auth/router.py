from fastapi import APIRouter, Depends

import auth.schemas as schemas

from sqlalchemy.orm import Session

from fastapi_jwt.jwt import JwtAccess

from auth.services.auth_service import AuthService

from app.database import get_db

from auth.dependency import get_security_access


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register/master/", response_model=schemas.Token)
async def master_register(
    user: schemas.CreateMaster,
    db: Session = Depends(get_db),
    access: JwtAccess = Depends(get_security_access),
):
    auth_service = AuthService(db=db, authorize=access)
    token = auth_service.register_master(user)
    return token


@router.post("/register/customer/", response_model=schemas.Token)
async def customer_register(
    user: schemas.CreateCustomer,
    db: Session = Depends(get_db),
    access: JwtAccess = Depends(get_security_access),
):
    auth_service = AuthService(db=db, authorize=access)
    token = auth_service.register_customer(user)
    return token


@router.post("/login/master/", response_model=schemas.Token)
async def master_login(
    user: schemas.Login,
    db: Session = Depends(get_db),
    access: JwtAccess = Depends(get_security_access),
):
    auth_service = AuthService(db=db, authorize=access)
    token = auth_service.login_master(user)
    return token


@router.post("/login/customer/", response_model=schemas.Token)
async def customer_login(
    user: schemas.Login,
    db: Session = Depends(get_db),
    access: JwtAccess = Depends(get_security_access),
):
    auth_service = AuthService(db=db, authorize=access)
    token = auth_service.login_customer(user)
    return token
