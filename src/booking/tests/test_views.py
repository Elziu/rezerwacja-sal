import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from booking.models import Room, Reservation
from datetime import date, time

User = get_user_model()

@pytest.mark.django_db
class TestReservationViews:
    @pytest.fixture
    def user1(self):
        return User.objects.create_user(username="user1", password="password")

    @pytest.fixture
    def user2(self):
        return User.objects.create_user(username="user2", password="password")

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_superuser(username="admin", password="password")

    @pytest.fixture
    def room(self):
        return Room.objects.create(name="View Test Room", status=Room.RoomStatus.AVAILABLE)

    @pytest.fixture
    def client_user1(self, client, user1):
        client.force_login(user1)
        return client

    def test_edit_reservation_permission_denied(self, client, user1, user2, room):
        res = Reservation.objects.create(
            room=room, created_by=user1,
            date=date(2026, 4, 1), time_from=time(10,0), time_to=time(12,0)
        )

        client.force_login(user2)

        url = reverse('edit_reservation', args=[res.id])
        response = client.get(url)

        assert response.status_code == 302
        assert response.url == "/"

        client.post(url, {
            'room': room.id,
            'date': '2026-04-02',
            'time_from': '10:00',
            'time_to': '12:00'
        })
        res.refresh_from_db()
        assert res.date == date(2026, 4, 1) # Should not change

    def test_edit_reservation_success_owner(self, client, user1, room):
        res = Reservation.objects.create(
            room=room, created_by=user1,
            date=date(2026, 4, 1), time_from=time(10,0), time_to=time(12,0)
        )
        client.force_login(user1)

        url = reverse('edit_reservation', args=[res.id])

        response = client.post(url, {
            'room': room.id,
            'date': '2026-04-02',
            'time_from': '11:00',
            'time_to': '13:00'
        })

        assert response.status_code == 302

        res.refresh_from_db()
        assert res.date == date(2026, 4, 2)
        assert res.time_from == time(11, 0)

    def test_edit_reservation_admin_access(self, client, user1, admin_user, room):
        res = Reservation.objects.create(
            room=room, created_by=user1,
            date=date(2026, 4, 1), time_from=time(10,0), time_to=time(12,0)
        )
        client.force_login(admin_user)

        url = reverse('edit_reservation', args=[res.id])
        response = client.get(url)
        assert response.status_code == 200 # Admin allows access
