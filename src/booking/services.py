from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from booking.models import Room, Reservation, ReservationParticipant

User = get_user_model()


class ReservationService:
    """Serwis zarządzający logiką biznesową rezerwacji sal."""

    @staticmethod
    def _validate_time_range(time_from, time_to):
        """Waliduje poprawność przedziału czasowego."""
        if time_from >= time_to:
            raise ValidationError("Godzina zakończenia musi być późniejsza niż godzina rozpoczęcia.")

    @staticmethod
    def _validate_room_availability(room):
        """Sprawdza czy sala jest dostępna."""
        if not room.is_available():
            raise ValidationError("Sala jest niedostępna.")

    @staticmethod
    def _check_time_conflict(room, date, time_from, time_to, exclude_reservation_id=None):
        """Sprawdza czy istnieje konflikt czasowy dla danej sali."""
        query = Reservation.objects.filter(
            room=room,
            date=date,
            time_from__lt=time_to,
            time_to__gt=time_from,
            status=Reservation.ReservationStatus.ACTIVE
        )
        
        if exclude_reservation_id:
            query = query.exclude(id=exclude_reservation_id)
        
        return query.exists()

    @staticmethod
    def check_conflicts(room, date, time_from, time_to):
        """Publiczna metoda sprawdzająca konflikty (backward compatibility)."""
        return ReservationService._check_time_conflict(room, date, time_from, time_to)

    @staticmethod
    def create_reservation(user, room, date, time_from, time_to, participant_ids=None):
        """Tworzy nową rezerwację z pełną walidacją."""
        # 1. Walidacja przedziału czasowego
        ReservationService._validate_time_range(time_from, time_to)

        # 2. Walidacja dostępności sali
        ReservationService._validate_room_availability(room)

        # 3. Sprawdzenie konfliktu zajętości
        if ReservationService._check_time_conflict(room, date, time_from, time_to):
            raise ValidationError("Sala jest zajęta w wybranym przedziale czasu.")

        # 4. Utworzenie rezerwacji
        reservation = Reservation.objects.create(
            room=room,
            date=date,
            time_from=time_from,
            time_to=time_to,
            created_by=user
        )
        ReservationService.update_reservation_participants(
            reservation=reservation,
            participant_ids=participant_ids,
            organizer=user,
        )
        return reservation

    @staticmethod
    def modify_reservation(reservation, date, time_from, time_to, user):
        """Modyfikuje istniejącą rezerwację z pełną walidacją."""
        room = reservation.room

        # 1. Walidacja przedziału czasowego
        ReservationService._validate_time_range(time_from, time_to)

        # 2. Walidacja dostępności sali
        ReservationService._validate_room_availability(room)

        # 3. Sprawdzenie konfliktu (wykluczając aktualnie edytowaną rezerwację)
        if ReservationService._check_time_conflict(room, date, time_from, time_to, reservation.id):
            raise ValidationError("Sala jest zajęta w wybranym przedziale czasu.")

        # 4. Aktualizacja rezerwacji
        reservation.date = date
        reservation.time_from = time_from
        reservation.time_to = time_to
        reservation.save()
        return reservation

    @staticmethod
    def cancel_reservation(reservation, user):
        """Anuluje rezerwację."""
        if reservation.status != Reservation.ReservationStatus.ACTIVE:
            raise ValidationError("Rezerwacja już anulowana.")

        reservation.status = Reservation.ReservationStatus.CANCELLED
        reservation.save()
        return reservation

    @staticmethod
    def get_selectable_participants(current_user):
        """Pobiera użytkowników, których można dodać jako uczestników."""
        return User.objects.exclude(id=current_user.id).order_by("username")

    @staticmethod
    def update_reservation_participants(reservation, participant_ids, organizer):
        """Aktualizuje listę uczestników rezerwacji."""
        participant_ids = participant_ids or []
        selected_ids = {
            int(participant_id)
            for participant_id in participant_ids
            if str(participant_id).isdigit()
        }
        selected_ids.discard(organizer.id)

        selected_users = User.objects.filter(id__in=selected_ids)
        participants = ReservationParticipant.objects.filter(reservation=reservation)

        participants.exclude(user__in=selected_users).delete()

        for user in selected_users:
            ReservationParticipant.objects.get_or_create(
                reservation=reservation,
                user=user,
            )

    @staticmethod
    def get_user_invitations(user):
        """Pobiera zaproszenia użytkownika do aktywnych rezerwacji."""
        return (
            ReservationParticipant.objects.select_related(
                "reservation",
                "reservation__room",
                "reservation__created_by",
            )
            .filter(
                user=user,
                reservation__status=Reservation.ReservationStatus.ACTIVE,
            )
            .order_by("reservation__date", "reservation__time_from")
        )

    @staticmethod
    def respond_to_invitation(participant, status):
        """Zapisuje odpowiedź uczestnika."""
        participant.status = status
        participant.responded_at = timezone.now()
        participant.save(update_fields=["status", "responded_at"])
        return participant

    @staticmethod
    def get_user_reservations(user, include_cancelled=False):
        """Pobiera rezerwacje użytkownika."""
        query = Reservation.objects.filter(created_by=user).prefetch_related("participants__user")
        
        if not include_cancelled:
            query = query.filter(status=Reservation.ReservationStatus.ACTIVE)
        
        return query.order_by('-date', '-time_from')

    @staticmethod
    def get_available_rooms(date=None, time_from=None, time_to=None):
        """Pobiera listę dostępnych sal."""
        # Podstawowe filtrowanie - tylko sale ze statusem AVAILABLE
        rooms = Room.objects.filter(status=Room.RoomStatus.AVAILABLE)
        
        # Jeśli podano datę i godziny, odfiltruj zajęte sale
        if date and time_from and time_to:
            reserved_room_ids = Reservation.objects.filter(
                date=date,
                time_from__lt=time_to,
                time_to__gt=time_from,
                status=Reservation.ReservationStatus.ACTIVE
            ).values_list('room_id', flat=True)
            
            rooms = rooms.exclude(id__in=reserved_room_ids)
        
        return rooms

    @staticmethod
    def get_room_reservations(room, active_only=True):
        """Pobiera rezerwacje dla konkretnej sali."""
        query = Reservation.objects.filter(room=room)
        
        if active_only:
            query = query.filter(status=Reservation.ReservationStatus.ACTIVE)
        
        return query.values('date', 'time_from', 'time_to')

    @staticmethod
    def get_rooms_with_availability():
        """Pobiera wszystkie dostępne sale wraz z ich rezerwacjami."""
        rooms = ReservationService.get_available_rooms()
        rooms_with_availability = []
        
        for room in rooms:
            reservations = ReservationService.get_room_reservations(room)
            rooms_with_availability.append({
                'room': room,
                'reservations': list(reservations)
            })
        
        return rooms_with_availability

    @staticmethod
    def generate_time_slots(start_hour=8, end_hour=16, interval_minutes=15):
        """Generuje listę dostępnych godzin rezerwacji."""
        hours = []
        for h in range(start_hour, end_hour + 1):
            for m in range(0, 60, interval_minutes):
                if h == end_hour and m > 0:
                    break
                hours.append(f"{h:02d}:{m:02d}")
        return hours
