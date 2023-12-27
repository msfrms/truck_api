from app.database import engine, Base
import order.models
import auth.models
import core.models
import chat.models

Base.metadata.create_all(bind=engine, checkfirst=True)
