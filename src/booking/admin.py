from django.contrib import admin
from .models import Room, Reservation


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "status",)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("room", "date", "time_from", "time_to", "created_by", "status")