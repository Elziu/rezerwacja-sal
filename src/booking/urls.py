from django.urls import path
from booking.views import (
    new_reservation,
    edit_reservation,
    cancel_reservation,
    export_my_reservations,
    export_reservation,
    export_room_reservations,
    export_all_reservations,
)

urlpatterns = [
    path("new/", new_reservation, name="new_reservation"),
    path("<int:reservation_id>/edit/", edit_reservation, name="edit_reservation"),
    path("<int:reservation_id>/cancel/", cancel_reservation, name="cancel_reservation"),
    path("export/my/", export_my_reservations, name="export_my_reservations"),
    path("<int:reservation_id>/export/", export_reservation, name="export_reservation"),
    path(
        "export/room/<int:room_id>/",
        export_room_reservations,
        name="export_room_reservations",
    ),
    path("export/all/", export_all_reservations, name="export_all_reservations"),
]
