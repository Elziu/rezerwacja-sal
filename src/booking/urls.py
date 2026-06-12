from django.urls import path
from booking.views import new_reservation, edit_reservation, cancel_reservation

urlpatterns = [
    path("new/", new_reservation, name="new_reservation"),
    path("<int:reservation_id>/edit/", edit_reservation, name="edit_reservation"),
    path("<int:reservation_id>/cancel/", cancel_reservation, name="cancel_reservation"),
]