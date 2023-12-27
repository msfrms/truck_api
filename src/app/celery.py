from celery import Celery
from app.config import settings

celery = Celery("app")
celery.conf.update(broker_url=settings.CELERY_BROKER_URL)
celery.autodiscover_tasks()

from order.tasks.tasks import *
