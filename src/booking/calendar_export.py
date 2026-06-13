from datetime import datetime, timedelta
from icalendar import Calendar, Event
from django.contrib.auth import get_user_model
from booking.models import Reservation

User = get_user_model()


class CalendarExporter:
    """Exporter for reservations to iCalendar format"""

    @staticmethod
    def create_event_from_reservation(reservation: Reservation) -> Event:
        """Create an iCalendar event from a reservation"""
        event = Event()

        # Combine date and time
        start_datetime = datetime.combine(reservation.date, reservation.time_from)
        end_datetime = datetime.combine(reservation.date, reservation.time_to)

        event.add("summary", f"Rezerwacja: {reservation.room.name}")
        event.add(
            "description",
            f"Sala: {reservation.room.name}\nZarezerwowana przez: {reservation.created_by.get_full_name() or reservation.created_by.username}",
        )
        event.add("dtstart", start_datetime)
        event.add("dtend", end_datetime)
        event.add("dtstamp", datetime.now())
        event.add("uid", f"reservation-{reservation.id}@booking-system")
        event.add("location", reservation.room.name)
        event.add(
            "status",
            (
                "CONFIRMED"
                if reservation.status == Reservation.ReservationStatus.ACTIVE
                else "CANCELLED"
            ),
        )

        return event

    @staticmethod
    def export_user_reservations(user: User, filename: str = None) -> str:
        """Export all active reservations for a user to iCalendar format"""
        cal = Calendar()
        cal.add("prodid", "-//Booking System//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("method", "PUBLISH")
        cal.add(
            "x-wr-calname", f"Moje rezerwacje - {user.get_full_name() or user.username}"
        )
        cal.add("x-wr-timezone", "Europe/Warsaw")

        # Get all active reservations for the user
        reservations = Reservation.objects.filter(
            created_by=user, status=Reservation.ReservationStatus.ACTIVE
        ).order_by("date", "time_from")

        for reservation in reservations:
            event = CalendarExporter.create_event_from_reservation(reservation)
            cal.add_component(event)

        return cal.to_ical().decode("utf-8")

    @staticmethod
    def export_room_reservations(room, filename: str = None) -> str:
        """Export all active reservations for a room to iCalendar format"""
        cal = Calendar()
        cal.add("prodid", "-//Booking System//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("method", "PUBLISH")
        cal.add("x-wr-calname", f"Rezerwacje - {room.name}")
        cal.add("x-wr-timezone", "Europe/Warsaw")

        # Get all active reservations for the room
        reservations = Reservation.objects.filter(
            room=room, status=Reservation.ReservationStatus.ACTIVE
        ).order_by("date", "time_from")

        for reservation in reservations:
            event = CalendarExporter.create_event_from_reservation(reservation)
            cal.add_component(event)

        return cal.to_ical().decode("utf-8")

    @staticmethod
    def export_all_reservations() -> str:
        """Export all active reservations to iCalendar format (admin only)"""
        cal = Calendar()
        cal.add("prodid", "-//Booking System//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("method", "PUBLISH")
        cal.add("x-wr-calname", "Wszystkie rezerwacje")
        cal.add("x-wr-timezone", "Europe/Warsaw")

        # Get all active reservations
        reservations = Reservation.objects.filter(
            status=Reservation.ReservationStatus.ACTIVE
        ).order_by("date", "time_from")

        for reservation in reservations:
            event = CalendarExporter.create_event_from_reservation(reservation)
            cal.add_component(event)

        return cal.to_ical().decode("utf-8")

    @staticmethod
    def export_single_reservation(reservation: Reservation) -> str:
        """Export a single reservation to iCalendar format"""
        cal = Calendar()
        cal.add("prodid", "-//Booking System//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("method", "PUBLISH")
        cal.add("x-wr-calname", f"Rezerwacja: {reservation.room.name}")
        cal.add("x-wr-timezone", "Europe/Warsaw")

        event = CalendarExporter.create_event_from_reservation(reservation)
        cal.add_component(event)

        return cal.to_ical().decode("utf-8")
