import os
import logging
from celery import Celery, Signature
from celery.schedules import crontab
from celery.signals import setup_logging
from datetime import datetime

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

# Get the current time
# current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

app.conf.beat_schedule = {
    # 'task1-schedule': 
    # {
    #     'task': 'task1',
    #     # 'schedule': crontab(), # runs every minute
    #     # 'schedule': crontab(minute='*/5'), # runs every 5 minutes
    #     'schedule': crontab(minute='*/30'), # runs every half hour
    #     'args': ([10])
    # },
    'schedule_sequential_tasks': {
        'task': 'execute_sequential_tasks',
        'schedule': crontab(minute=0, hour=3),
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
    # 'renew_token_schedule': {
    #     'task': 'renew_token',
    #     'schedule': crontab(hour='*/19'),  # 19 hours interval
    #     'args': (current_time),  # Pass any required arguments here
    # }
}