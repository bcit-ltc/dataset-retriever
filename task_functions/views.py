from django.shortcuts import render
import requests
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.shortcuts import redirect
from django.conf import settings
from django.core.cache import cache
import logging
import urllib
logger = logging.getLogger(__name__)


class Home(View):
    """
    Home page view
    """

    def get(self, request):

        log_file_path = 'page.log'
        try:
            with open(log_file_path, 'r') as log_file:
                lines = log_file.readlines()
                info_lines = [line for line in lines if 'INFO' in line]
                last_10_info_lines = info_lines[-10:]
                page = ""
                for line in last_10_info_lines:
                    page += line.strip() + "<br>"
                return HttpResponse(page)
        except FileNotFoundError:
            logger.error(f"Log file not found: {log_file_path}")
        except Exception as e:
            logger.error(f"An error occurred while reading the log file: {e}")


        
