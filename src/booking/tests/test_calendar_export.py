import pytest
from datetime import date, time
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from booking.models import Room, Reservation
from booking.calendar_export import CalendarExporter

User = get_user_model()


class CalendarExporterTestCase(TestCase):
    """Tests for calendar export functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
        )

        self.room = Room.objects.create(
            name="Conference Room A", status=Room.RoomStatus.AVAILABLE
        )

        self.reservation = Reservation.objects.create(
            room=self.room,
            date=date(2026, 6, 15),
            time_from=time(10, 0),
            time_to=time(11, 30),
            created_by=self.user,
        )

        self.client = Client()

    def test_export_single_reservation(self):
        """Test exporting a single reservation"""
        ical_content = CalendarExporter.export_single_reservation(self.reservation)

        assert isinstance(ical_content, str)
        assert "BEGIN:VCALENDAR" in ical_content
        assert "END:VCALENDAR" in ical_content
        assert "Conference Room A" in ical_content
        assert "DTSTART" in ical_content
        assert "DTEND" in ical_content

    def test_export_user_reservations(self):
        """Test exporting all user's reservations"""
        # Create another reservation
        Reservation.objects.create(
            room=self.room,
            date=date(2026, 6, 16),
            time_from=time(14, 0),
            time_to=time(15, 0),
            created_by=self.user,
        )

        ical_content = CalendarExporter.export_user_reservations(self.user)

        assert isinstance(ical_content, str)
        assert "BEGIN:VCALENDAR" in ical_content
        assert "END:VCALENDAR" in ical_content
        assert ical_content.count("BEGIN:VEVENT") == 2

    def test_export_room_reservations(self):
        """Test exporting all reservations for a room"""
        user2 = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpass123"
        )

        Reservation.objects.create(
            room=self.room,
            date=date(2026, 6, 16),
            time_from=time(14, 0),
            time_to=time(15, 0),
            created_by=user2,
        )

        ical_content = CalendarExporter.export_room_reservations(self.room)

        assert isinstance(ical_content, str)
        assert "BEGIN:VCALENDAR" in ical_content
        assert ical_content.count("BEGIN:VEVENT") == 2

    def test_export_all_reservations(self):
        """Test exporting all reservations"""
        ical_content = CalendarExporter.export_all_reservations()

        assert isinstance(ical_content, str)
        assert "BEGIN:VCALENDAR" in ical_content
        assert "BEGIN:VEVENT" in ical_content

    def test_export_my_reservations_view(self):
        """Test the export_my_reservations view"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("export_my_reservations"))

        assert response.status_code == 200
        assert response["Content-Type"] == "text/calendar"
        assert "moje-rezerwacje.ics" in response["Content-Disposition"]

    def test_export_reservation_view(self):
        """Test the export_reservation view"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse(
                "export_reservation", kwargs={"reservation_id": self.reservation.id}
            )
        )

        assert response.status_code == 200
        assert response["Content-Type"] == "text/calendar"
        assert "rezerwacja-" in response["Content-Disposition"]

    def test_export_reservation_unauthorized(self):
        """Test exporting someone else's reservation without permission"""
        user2 = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpass123"
        )

        self.client.login(username="testuser2", password="testpass123")
        response = self.client.get(
            reverse(
                "export_reservation", kwargs={"reservation_id": self.reservation.id}
            )
        )

        assert response.status_code == 302  # Redirect

    def test_export_requires_login(self):
        """Test that export requires login"""
        response = self.client.get(reverse("export_my_reservations"))
        assert response.status_code == 302  # Redirect to login

    def test_cancelled_reservation_in_export(self):
        """Test that cancelled reservations are marked as CANCELLED in ical"""
        self.reservation.status = Reservation.ReservationStatus.CANCELLED
        self.reservation.save()

        ical_content = CalendarExporter.export_single_reservation(self.reservation)

        assert "STATUS:CANCELLED" in ical_content
