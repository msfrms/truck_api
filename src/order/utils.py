from typing import List, Optional

import order.schemas as schemas
import order.models as models

import auth.schemas as auth_schemas


def map_transports_to_short_transport(
    transports: List[schemas.Transport],
) -> List[schemas.GetTransportList]:
    short_transports: List[schemas.GetTransportList] = []

    for transport in transports:
        short_transports.append(schemas.GetTransportList(**transport.model_dump()))

    return short_transports


def map_orders_models_to_orders_schemas(
    orders: List[models.Order],
) -> List[schemas.GetOrderList]:
    new_orders: List[schemas.GetOrderList] = []

    for order in orders:
        transports: List[schemas.Transport] = order.get_transports()
        list_order = schemas.GetOrderList(
            id=order.id,
            status=order.status,
            order_number=order.order_number,
            transports=map_transports_to_short_transport(transports),
            update_at=order.updated_at,
            region=order.address.region,
            city=order.address.city,
        )
        new_orders.append(list_order)

    new_orders.sort(key=lambda x: x.update_at, reverse=True)

    return new_orders
