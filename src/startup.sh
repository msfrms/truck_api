#!/bin/bash

python create_tables.py

# gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000 --certfile=certs/truck_backend.crt --keyfile=certs/truck_backend.key
gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000