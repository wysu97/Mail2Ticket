from django.urls import path
from .views import fetch_emails

urlpatterns = [
    path('fetch_emails/', fetch_emails,),
]