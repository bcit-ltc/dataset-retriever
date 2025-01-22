from django.shortcuts import render
import requests
from django.http import JsonResponse
from django.views import View
from django.shortcuts import redirect
from django.conf import settings



class OAuth2LoginView(View):
    """
    A Django view to redirect users to the OAuth2 provider's authorization page.
    """

    def get(self, request):

        return JsonResponse({"message": "Hello, World!"})
