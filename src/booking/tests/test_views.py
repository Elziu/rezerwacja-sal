import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from booking.models import Room, Reservation, ReservationParticipant
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

    def test_new_reservation_creates_participant_invitation(self, client, user1, user2, room):
        client.force_login(user1)

        response = client.post(reverse("new_reservation"), {
            "room": room.id,
            "date": "2026-04-02",
            "time_from": "10:00",
            "time_to": "12:00",
            "participants": [user2.id],
        })

        assert response.status_code == 302
        reservation = Reservation.objects.get(created_by=user1)
        invitation = ReservationParticipant.objects.get(
            reservation=reservation,
            user=user2,
        )
        assert invitation.status == ReservationParticipant.PresenceStatus.PENDING

    def test_index_shows_invitation_for_participant(self, client, user1, user2, room):
        res = Reservation.objects.create(
            room=room,
            created_by=user1,
            date=date(2026, 4, 1),
            time_from=time(10, 0),
            time_to=time(12, 0),
        )
        ReservationParticipant.objects.create(
            reservation=res,
            user=user2,
        )
        client.force_login(user2)

        response = client.get(reverse("index"))

        assert response.status_code == 200
        assert "Zaproszenia do rezerwacji" in response.content.decode()
        assert "Potwierdź" in response.content.decode()

    def test_edit_reservation_admin_access(self, client, user1, admin_user, room):
        res = Reservation.objects.create(
            room=room, created_by=user1,
            date=date(2026, 4, 1), time_from=time(10,0), time_to=time(12,0)
        )
        client.force_login(admin_user)

        url = reverse('edit_reservation', args=[res.id])
        response = client.get(url)
        assert response.status_code == 200 # Admin allows access

    def test_confirm_presence_success(self, client, user1, user2, room):
        res = Reservation.objects.create(
            room=room,
            created_by=user1,
            date=date(2026, 4, 1),
            time_from=time(10, 0),
            time_to=time(12, 0),
        )
        invitation = ReservationParticipant.objects.create(
            reservation=res,
            user=user2,
        )
        client.force_login(user2)

        response = client.post(reverse("confirm_presence", args=[invitation.id]))

        assert response.status_code == 302
        invitation.refresh_from_db()
        assert invitation.status == ReservationParticipant.PresenceStatus.CONFIRMED
        assert invitation.responded_at is not None

    def test_decline_presence_success(self, client, user1, user2, room):
        res = Reservation.objects.create(
            room=room,
            created_by=user1,
            date=date(2026, 4, 1),
            time_from=time(10, 0),
            time_to=time(12, 0),
        )
        invitation = ReservationParticipant.objects.create(
            reservation=res,
            user=user2,
        )
        client.force_login(user2)

        response = client.post(reverse("decline_presence", args=[invitation.id]))

        assert response.status_code == 302
        invitation.refresh_from_db()
        assert invitation.status == ReservationParticipant.PresenceStatus.DECLINED
        assert invitation.responded_at is not None

    def test_confirm_presence_denied_for_other_user(self, client, user1, user2, room):
        res = Reservation.objects.create(
            room=room,
            created_by=user1,
            date=date(2026, 4, 1),
            time_from=time(10, 0),
            time_to=time(12, 0),
        )
        invitation = ReservationParticipant.objects.create(
            reservation=res,
            user=user2,
        )
        client.force_login(user1)

        response = client.post(reverse("confirm_presence", args=[invitation.id]))

        assert response.status_code == 404
        invitation.refresh_from_db()
        assert invitation.status == ReservationParticipant.PresenceStatus.PENDING
