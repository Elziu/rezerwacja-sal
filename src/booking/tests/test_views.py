

from datetime import date, time

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from booking.models import Room, Reservation


@pytest.fixture
def user():
    return User.objects.create_user(username="jan", password="test")


@pytest.fixture
def other_user():
    return User.objects.create_user(username="anna", password="test")


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        username="admin",
        password="test",
        email="admin@example.com",
    )


@pytest.fixture
def room():
    return Room.objects.create(name="Sala A")


@pytest.fixture
def reservation(user, room):
    return Reservation.objects.create(
        room=room,
        date=date(2026, 1, 1),
        start_time=time(10, 0),
        end_time=time(11, 0),
        created_by=user,
    )


@pytest.mark.django_db
def test_index_requires_login(client):
    response = client.get(reverse("index"))

    assert response.status_code == 302


@pytest.mark.django_db
def test_logged_user_can_open_index(client, user):
    client.login(username="jan", password="test")

    response = client.get(reverse("index"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_user_can_create_reservation(client, user, room):
    client.login(username="jan", password="test")

    response = client.post(
        reverse("create_reservation"),
        {
            "room": room.id,
            "date": "2026-01-01",
            "start_time": "10:00",
            "end_time": "11:00",
        },
    )

    assert response.status_code == 302
    assert Reservation.objects.count() == 1


@pytest.mark.django_db
def test_owner_can_cancel_reservation(client, user, reservation):
    client.login(username="jan", password="test")

    response = client.post(reverse("cancel_reservation", args=[reservation.id]))

    reservation.refresh_from_db()

    assert response.status_code == 302
    assert reservation.status == Reservation.Status.CANCELLED


@pytest.mark.django_db
def test_other_user_cannot_cancel_reservation(client, other_user, reservation):
    client.login(username="anna", password="test")

    response = client.post(reverse("cancel_reservation", args=[reservation.id]))

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_cancel_reservation(client, admin_user, reservation):
    client.login(username="admin", password="test")

    response = client.post(reverse("cancel_reservation", args=[reservation.id]))

    reservation.refresh_from_db()

    assert response.status_code == 302
    assert reservation.status == Reservation.Status.CANCELLED
