import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import date, time
from booking.models import Room, Reservation
from booking.services import ReservationService

User = get_user_model()

@pytest.mark.django_db
class TestReservationService:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(username="testuser", password="password")

    @pytest.fixture
    def room(self):
        return Room.objects.create(name="Service Test Room", status=Room.RoomStatus.AVAILABLE)

    def test_create_reservation_success(self, user, room):
        r_date = date(2026, 1, 30)
        t_start = time(10, 0)
        t_end = time(12, 0)

        reservation = ReservationService.create_reservation(user, room, r_date, t_start, t_end)

        assert reservation.pk is not None
        assert reservation.room == room
        assert reservation.created_by == user
        assert reservation.status == Reservation.ReservationStatus.ACTIVE

    def test_create_reservation_invalid_time_range(self, user, room):
        r_date = date(2026, 1, 30)
        t_start = time(12, 0)
        t_end = time(10, 0)

        with pytest.raises(ValidationError) as excinfo:
            ReservationService.create_reservation(user, room, r_date, t_start, t_end)

        assert "Godzina zakończenia musi być późniejsza" in str(excinfo.value)

    def test_create_reservation_room_unavailable(self, user, room):
        room.status = Room.RoomStatus.UNAVAILABLE
        room.save()

        r_date = date(2026, 1, 30)
        t_start = time(10, 0)
        t_end = time(12, 0)

        with pytest.raises(ValidationError) as excinfo:
            ReservationService.create_reservation(user, room, r_date, t_start, t_end)

        assert "Sala jest niedostępna" in str(excinfo.value)

    def test_create_reservation_conflict(self, user, room):
        r_date = date(2026, 1, 30)
        t_start = time(10, 0)
        t_end = time(12, 0)

        # Create initial reservation
        ReservationService.create_reservation(user, room, r_date, t_start, t_end)

        # Try to overlap
        with pytest.raises(ValidationError) as excinfo:
            ReservationService.create_reservation(user, room, r_date, time(11, 0), time(13, 0))

        assert "Sala jest zajęta" in str(excinfo.value)

    def test_cancel_reservation(self, user, room):
        r_date = date(2026, 1, 30)
        t_start = time(10, 0)
        t_end = time(12, 0)

        reservation = ReservationService.create_reservation(user, room, r_date, t_start, t_end)

        ReservationService.cancel_reservation(reservation, user)

        reservation.refresh_from_db()
        assert reservation.status == Reservation.ReservationStatus.CANCELLED

    def test_get_available_rooms(self, user, room):
        # Create another room
        room2 = Room.objects.create(name="Room 2", status=Room.RoomStatus.AVAILABLE)

        r_date = date(2026, 2, 1)
        t_start = time(10, 0)
        t_end = time(12, 0)

        # Reserve room 1
        ReservationService.create_reservation(user, room, r_date, t_start, t_end)

        available = ReservationService.get_available_rooms(r_date, t_start, t_end)

        assert room not in available
        assert room2 in available

    def test_modify_reservation_success(self, user, room):
        r_date = date(2026, 3, 1)
        t_start = time(10, 0)
        t_end = time(12, 0)
        reservation = ReservationService.create_reservation(user, room, r_date, t_start, t_end)

        new_t_start = time(11, 0)
        new_t_end = time(13, 0)

        updated = ReservationService.modify_reservation(reservation, r_date, new_t_start, new_t_end, user)

        updated.refresh_from_db()
        assert updated.time_from == new_t_start
        assert updated.time_to == new_t_end

    def test_modify_reservation_conflict(self, user, room):
        r_date = date(2026, 3, 1)
        # Res 1: 10-12
        res1 = ReservationService.create_reservation(user, room, r_date, time(10, 0), time(12, 0))
        # Res 2: 13-15
        res2 = ReservationService.create_reservation(user, room, r_date, time(13, 0), time(15, 0))

        # Try to move Res 2 to overlap with Res 1 (11-13)
        with pytest.raises(ValidationError) as excinfo:
            ReservationService.modify_reservation(res2, r_date, time(11, 0), time(13, 0), user)

        assert "Sala jest zajęta" in str(excinfo.value)

    def test_modify_reservation_self_overlap_allowed(self, user, room):
        # Allow extending own reservation
        r_date = date(2026, 3, 1)
        res1 = ReservationService.create_reservation(user, room, r_date, time(10, 0), time(12, 0))

        # Change to 09:00 - 13:00 (overlaps with old self)
        ReservationService.modify_reservation(res1, r_date, time(9, 0), time(13, 0), user)

        res1.refresh_from_db()
        assert res1.time_from == time(9, 0)
        assert res1.time_to == time(13, 0)

    def test_get_user_reservations(self, user, room):
        r_date = date(2026, 3, 1)
        t_start = time(10, 0)
        t_end = time(12, 0)

        res1 = ReservationService.create_reservation(user, room, r_date, t_start, t_end)

        # Create cancelled
        res2 = Reservation.objects.create(
            room=room,
            created_by=user,
            date=r_date,
            time_from=time(14,0),
            time_to=time(15,0),
            status=Reservation.ReservationStatus.CANCELLED
        )

        user_active_res = ReservationService.get_user_reservations(user, include_cancelled=False)
        assert res1 in user_active_res
        assert res2 not in user_active_res

        user_all_res = ReservationService.get_user_reservations(user, include_cancelled=True)
        assert res1 in user_all_res
        assert res2 in user_all_res
