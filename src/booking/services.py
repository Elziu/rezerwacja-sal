from datetime import time, timedelta, datetime

from django.core.exceptions import ValidationError

from .models import Room, Reservation


class ReservationService:
    @staticmethod
    def create_reservation(room, date, start_time, end_time, user):
        if start_time >= end_time:
            raise ValidationError("Start time must be before end time.")

        if room.status != Room.Status.AVAILABLE:
            raise ValidationError("Room is unavailable.")

        if ReservationService.has_conflict(room, date, start_time, end_time):
            raise ValidationError("Room is already reserved for this time.")

        return Reservation.objects.create(
            room=room,
            date=date,
            start_time=start_time,
            end_time=end_time,
            created_by=user,
        )

    @staticmethod
    def has_conflict(room, date, start_time, end_time, exclude_reservation_id=None):
        return False
