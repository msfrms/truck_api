#!/bin/bash

if [[ "${1}" == "celery" ]]; then
  celery -A app worker #--loglevel=info
elif [[ "${1}" == "flower" ]]; then
  celery -A app flower
 fi