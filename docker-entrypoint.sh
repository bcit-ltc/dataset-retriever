#!/bin/sh

set -e
# if [ -z "${DJANGO_SECRET_KEY}" ];then
#   echo DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY >> .env
# fi

python manage.py makemigrations
python manage.py migrate


>&2 echo "Starting redis ..."
mkdir -p /redis-data
redis-server --daemonize yes --dbfilename redis-dump.rdb --dir /redis-data

>&2 echo "Starting Celery Worker..."
celery -A dataset_retriever worker --detach --loglevel=DEBUG \
--concurrency=1 -n worker1@%h \
worker_hijack_root_logger=False \
worker_redirect_stdouts=True \
worker_redirect_stdouts_level=DEBUG


>&2 echo "Starting Celery Beat..."
celery -A dataset_retriever beat --detach --loglevel=DEBUG \
--scheduler=django_celery_beat.schedulers.DatabaseScheduler 
worker_hijack_root_logger=False \
worker_redirect_stdouts=True \
worker_redirect_stdouts_level=DEBUG

>&2 echo "Starting dataset retriever ..."
exec "$@"
