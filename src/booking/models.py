from django.db import models
from django.contrib.auth.models import User


class Room(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        UNAVAILABLE = "UNAVAILABLE", "Unavailable"

    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )

    def __str__(self):
        return self.name


class Reservation(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        CANCELLED = "CANCELLED", "Cancelled"

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.room.name} - {self.date} {self.start_time}-{self.end_time}"