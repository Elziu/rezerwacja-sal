from django.contrib import admin

from .models import Room, Reservation


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status")
    list_filter = ("status",)
    search_fields = ("name",)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "room",
        "date",
        "start_time",
        "end_time",
        "status",
        "created_by",
    )
    list_filter = ("status", "date", "room")
    search_fields = ("room__name", "created_by__username")