from django.urls import path
from booking.views import (
    new_reservation,
    edit_reservation,
    cancel_reservation,
    confirm_presence,
    decline_presence,
    export_my_reservations,
    export_reservation,
    export_room_reservations,
    export_all_reservations,
)

urlpatterns = [
    path("new/", new_reservation, name="new_reservation"),
    path("<int:reservation_id>/edit/", edit_reservation, name="edit_reservation"),
    path("<int:reservation_id>/cancel/", cancel_reservation, name="cancel_reservation"),
    path(
        "participants/<int:participant_id>/confirm/",
        confirm_presence,
        name="confirm_presence",
    ),
    path(
        "participants/<int:participant_id>/decline/",
        decline_presence,
        name="decline_presence",
    ),
    path("export/my/", export_my_reservations, name="export_my_reservations"),
    path("<int:reservation_id>/export/", export_reservation, name="export_reservation"),
    path(
        "export/room/<int:room_id>/",
        export_room_reservations,
        name="export_room_reservations",
    ),
    path("export/all/", export_all_reservations, name="export_all_reservations"),
]
