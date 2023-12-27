from core.schemas import CamelModel

from order.schemas import PostOrder

from auth.schemas import CreateCustomer, Token, Login


class CreateCustomerWithOrder(CamelModel):
    customer: CreateCustomer
    order: PostOrder


class LoginCustomerWithOrder(CamelModel):
    login: Login
    order: PostOrder


class OrderCreated(CamelModel):
    order_number: str
    order_id: int
    token: Token
