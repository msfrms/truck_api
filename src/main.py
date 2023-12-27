from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

from order.router import router as order_router

from auth.router import router as auth_router

from auth_order.router import router as auth_order_router

from chat.router import router as chat_router

import sentry_sdk

from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
instrumentator = Instrumentator().instrument(app)

origins = [settings.CLIENT_ORIGIN]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Origin",
        "Authorization",
    ],
)

app.include_router(order_router)
app.include_router(auth_router)
app.include_router(auth_order_router)
app.include_router(chat_router)


@app.on_event("startup")
async def startup_event():
    instrumentator.expose(app)
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production,
        traces_sample_rate=1.0,
    )
