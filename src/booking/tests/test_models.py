from datetime import date, time

import pytest
from django.contrib.auth.models import User

from booking.models import Room, Reservation


@pytest.mark.django_db
def test_room_str():
    room = Room.objects.create(name="Sala A")

    assert str(room) == "Sala A"


@pytest.mark.django_db
def test_reservation_str():
    user = User.objects.create_user(username="jan", password="test")
    room = Room.objects.create(name="Sala A")

    reservation = Reservation.objects.create(
        room=room,
        date=date(2026, 1, 1),
        start_time=time(10, 0),
        end_time=time(11, 0),
        created_by=user,
    )

    assert "Sala A" in str(reservation)
