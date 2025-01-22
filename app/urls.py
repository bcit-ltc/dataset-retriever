from django.urls import include, path, re_path
from django.conf import settings
from .views import OAuth2LoginView

urlpatterns = [
    path('', OAuth2LoginView.as_view(), name='login'),
]