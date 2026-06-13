from django.contrib import admin
from .models import Room, Reservation, ReservationParticipant


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "status",)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("room", "date", "time_from", "time_to", "created_by", "status")


@admin.register(ReservationParticipant)
class ReservationParticipantAdmin(admin.ModelAdmin):
    list_display = ("reservation", "user", "status", "responded_at")
    list_filter = ("status",)
    search_fields = ("user__username", "reservation__room__name")
