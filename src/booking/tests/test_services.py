

from datetime import date, time

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from booking.models import Room, Reservation
from booking.services import ReservationService


@pytest.fixture
def user():
    return User.objects.create_user(username="jan", password="test")


@pytest.fixture
def room():
    return Room.objects.create(name="Sala A")


@pytest.mark.django_db
def test_create_reservation(user, room):
    reservation = ReservationService.create_reservation(
        room=room,
        date=date(2026, 1, 1),
        start_time=time(10, 0),
        end_time=time(11, 0),
        user=user,
    )

    assert reservation.id is not None
    assert reservation.room == room
    assert reservation.created_by == user


@pytest.mark.django_db
def test_create_reservation_invalid_time(user, room):
    with pytest.raises(ValidationError):
        ReservationService.create_reservation(
            room=room,
            date=date(2026, 1, 1),
            start_time=time(11, 0),
            end_time=time(10, 0),
            user=user,
        )


@pytest.mark.django_db
def test_create_reservation_conflict(user, room):
    ReservationService.create_reservation(
        room=room,
        date=date(2026, 1, 1),
        start_time=time(10, 0),
        end_time=time(11, 0),
        user=user,
    )

    with pytest.raises(ValidationError):
        ReservationService.create_reservation(
            room=room,
            date=date(2026, 1, 1),
            start_time=time(10, 30),
            end_time=time(11, 30),
            user=user,
        )


@pytest.mark.django_db
def test_cancel_reservation(user, room):
    reservation = ReservationService.create_reservation(
        room=room,
        date=date(2026, 1, 1),
        start_time=time(10, 0),
        end_time=time(11, 0),
        user=user,
    )

    ReservationService.cancel_reservation(reservation)

    reservation.refresh_from_db()

    assert reservation.status == Reservation.Status.CANCELLED
