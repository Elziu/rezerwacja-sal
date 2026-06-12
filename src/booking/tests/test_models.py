import pytest
from booking.models import Room

@pytest.mark.django_db
class TestRoomModel:
    def test_room_str(self):
        room = Room.objects.create(name="Conference Room A", status=Room.RoomStatus.AVAILABLE)
        assert str(room) == "Conference Room A (AVAILABLE)"

    def test_room_is_available(self):
        room = Room.objects.create(name="Room B", status=Room.RoomStatus.AVAILABLE)
        assert room.is_available() is True

        room.status = Room.RoomStatus.UNAVAILABLE
        room.save()
        assert room.is_available() is False
