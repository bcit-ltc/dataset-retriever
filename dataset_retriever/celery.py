import os
import logging
from celery import Celery, Signature
from celery.schedules import crontab
from celery.signals import setup_logging

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dataset_retriever.settings')

app = Celery('dataset_retriever')    

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Ensure Celery uses Django's logging configuration
# @setup_logging.connect
# def config_loggers(*args, **kwags):
#     from logging.config import dictConfig
#     from django.conf import settings
#     dictConfig(settings.LOGGING)
#     logger = logging.getLogger('celery.task')
#     logger.info('Celery logging configured')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'renew_token_schedule': {
        'task': 'renew_token',
        'schedule': [
            crontab(minute=0, hour='0-2,4-23'),  # Every hour except 3 AM
            crontab(minute=55, hour=2),          # Additional run at 2:55 AM
            crontab(minute=30, hour=3)           # Additional run at 3:30 AM
        ],
        'args': (11,),
    },
    'schedule_sequential_tasks': {
        'task': 'execute_sequential_tasks',
        'schedule': crontab(minute=0, hour=3),
        # 'schedule': crontab(minute='*/30'),  # 30 minutes interval
        'args': (20,),
        # 'options': {
        #     'queue': 'default',
        #     'link': Signature(
        #         'task3', 
        #         args=(30,),
        #         kwargs={},
        #         queue='default')
        # }
    },
}