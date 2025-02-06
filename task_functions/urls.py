from django.urls import include, path, re_path
from django.conf import settings
from django.http import HttpResponse
from .views import Home

urlpatterns = [
    # path('', lambda request: HttpResponse('dataset-retriever'), name='home'), #landing page
    path('', Home.as_view(), name='home')
]