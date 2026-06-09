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
        reservations = Reservation.objects.filter(
            room=room,
            date=date,
            status=Reservation.Status.ACTIVE,
            start_time__lt=end_time,
            end_time__gt=start_time,
        )

        if exclude_reservation_id is not None:
            reservations = reservations.exclude(id=exclude_reservation_id)

        return reservations.exists()
    
    @staticmethod
    def cancel_reservation(reservation):
        reservation.status = Reservation.Status.CANCELLED
        reservation.save(update_fields=["status", "updated_at"])
        return reservation

    @staticmethod
    def modify_reservation(reservation, room, date, start_time, end_time, user):
        if start_time >= end_time:
            raise ValidationError("Start time must be before end time.")

        if room.status != Room.Status.AVAILABLE:
            raise ValidationError("Room is unavailable.")

        if ReservationService.has_conflict(
            room=room,
            date=date,
            start_time=start_time,
            end_time=end_time,
            exclude_reservation_id=reservation.id,
        ):
            raise ValidationError("Room is already reserved for this time.")

        reservation.room = room
        reservation.date = date
        reservation.start_time = start_time
        reservation.end_time = end_time
        reservation.save()

        return reservation

    @staticmethod
    def get_available_rooms(date=None, start_time=None, end_time=None):
        rooms = Room.objects.filter(status=Room.Status.AVAILABLE)

        if not date or not start_time or not end_time:
            return rooms

        unavailable_room_ids = Reservation.objects.filter(
            date=date,
            status=Reservation.Status.ACTIVE,
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).values_list("room_id", flat=True)

        return rooms.exclude(id__in=unavailable_room_ids)

    @staticmethod
    def get_user_reservations(user):
        return Reservation.objects.filter(
            created_by=user,
            status=Reservation.Status.ACTIVE,
        ).order_by("date", "start_time")

    @staticmethod
    def get_time_slots():
        slots = []
        current = datetime.combine(datetime.today(), time(8, 0))
        end = datetime.combine(datetime.today(), time(16, 0))

        while current <= end:
            slots.append(current.time())
            current += timedelta(minutes=15)

        return slots



