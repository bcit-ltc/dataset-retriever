from django.apps import AppConfig
import logging
logger = logging.getLogger(__name__)

class OauthConnectorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'oauth_connector'

    def ready(self):

        logger.info("started oauth_connector")