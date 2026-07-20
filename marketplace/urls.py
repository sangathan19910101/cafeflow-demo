from django.urls import path
from .views import marketplace_home

urlpatterns = [
    path("", marketplace_home, name="marketplace_home"),
]
