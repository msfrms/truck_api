#!/bin/bash

python create_tables.py
# alembic upgrade head
uvicorn main:app --reload --log-level debug --ssl-certfile=certs/localhost.crt --ssl-keyfile=certs/localhost.key