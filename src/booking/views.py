from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect

from .models import Room, Reservation
from .services import ReservationService


@login_required
def create_reservation(request):
    if request.method != "POST":
        return redirect("index")

    room_id = request.POST.get("room")
    date_value = request.POST.get("date")
    start_time_value = request.POST.get("start_time")
    end_time_value = request.POST.get("end_time")

    room = get_object_or_404(Room, id=room_id)

    date = datetime.strptime(date_value, "%Y-%m-%d").date()
    start_time = datetime.strptime(start_time_value, "%H:%M").time()
    end_time = datetime.strptime(end_time_value, "%H:%M").time()

    try:
        ReservationService.create_reservation(
            room=room,
            date=date,
            start_time=start_time,
            end_time=end_time,
            user=request.user,
        )
        messages.success(request, "Reservation created successfully.")
    except ValidationError as error:
        messages.error(request, error.message)

    return redirect("index")
