from django.apps import AppConfig
from django.conf import settings
import logging
logger = logging.getLogger(__name__)

class TaskFunctionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'task_functions'

    def ready(self):

        logger.info("started task_functions")