from django.urls import include, path, re_path
from django.conf import settings
from .views import OAuth2LoginView, OAuth2CallbackView
from django.http import HttpResponse

urlpatterns = [
    path('auth/callback/', OAuth2CallbackView.as_view(), name='callback'),
    path('auth/login/', OAuth2LoginView.as_view(), name='login'),
    path('', lambda request: HttpResponse('dataset-retriever'), name='home'), #landing page
]