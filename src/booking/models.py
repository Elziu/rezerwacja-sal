from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Room(models.Model):
    class RoomStatus(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Dostępna"
        UNAVAILABLE = "UNAVAILABLE", "Niedostępna"

    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=RoomStatus.choices, default=RoomStatus.AVAILABLE)

    def __str__(self):
        return f"{self.name} ({self.status})"
    

    def is_available(self):
        return self.status == self.RoomStatus.AVAILABLE
    

class Reservation(models.Model):

    class ReservationStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Aktywna"
        CANCELLED = "CANCELLED", "Anulowana"

    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    date = models.DateField()
    time_from = models.TimeField()
    time_to = models.TimeField()
    status = models.CharField(max_length=20, choices=ReservationStatus.choices, default=ReservationStatus.ACTIVE)

    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="reservations")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ReservationParticipant(models.Model):
    class PresenceStatus(models.TextChoices):
        PENDING = "PENDING", "Oczekuje"
        CONFIRMED = "CONFIRMED", "Potwierdzona"
        DECLINED = "DECLINED", "Odmówiona"

    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reservation_invitations",
    )
    status = models.CharField(
        max_length=20,
        choices=PresenceStatus.choices,
        default=PresenceStatus.PENDING,
    )
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["reservation", "user"],
                name="unique_reservation_participant",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.reservation} ({self.status})"

