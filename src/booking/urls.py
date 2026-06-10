from django.urls import path

from .views import create_reservation

urlpatterns = [
    path("create/", create_reservation, name="create_reservation"),
]
