from django.urls import path

from .views import create_reservation, edit_reservation, cancel_reservation

urlpatterns = [
    path("create/", create_reservation, name="create_reservation"),
    path("<int:reservation_id>/edit/", edit_reservation, name="edit_reservation"),
    path("<int:reservation_id>/cancel/", cancel_reservation, name="cancel_reservation"),
]
