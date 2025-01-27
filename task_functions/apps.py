from django.apps import AppConfig
from django.conf import settings
import logging
logger = logging.getLogger(__name__)

class TaskFunctionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'task_functions'

    def ready(self):

        logger.info("started task_functions")

        # from django.contrib.auth.models import User        
        # if not User.objects.filter(username="admin").exists():
        #     User.objects.create_superuser(
        #         "admin", "admin@example.com", "password"
        #     )
        #     logger.info("ADMIN user created")