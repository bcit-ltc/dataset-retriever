#!/bin/sh

set -e
# if [ -z "${DJANGO_SECRET_KEY}" ];then
#   echo DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY >> .env
# fi

python manage.py makemigrations
python manage.py migrate --fake

>&2 echo "Start Celery workers"
celery -A dataset_retriever worker --beat -l DEBUG -s /home/celerybeat-schedule --detach worker_hijack_root_logger=False worker_redirect_stdouts=True worker_redirect_stdouts_level=DEBUG
celery -A dataset_retriever worker --loglevel=DEBUG --concurrency=1 -n worker1@%h --detach worker_hijack_root_logger=False worker_redirect_stdouts=True worker_redirect_stdouts_level=DEBUG


>&2 echo "Starting dataset retriever ..."
exec "$@"
