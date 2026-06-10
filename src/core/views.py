from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from booking.models import Reservation
from booking.services import ReservationService


@login_required
def index(request):
    rooms = ReservationService.get_available_rooms()
    user_reservations = ReservationService.get_user_reservations(request.user)
    time_slots = ReservationService.get_time_slots()

    all_reservations = Reservation.objects.filter(
        status=Reservation.Status.ACTIVE,
    ).select_related("room")

    return render(
        request,
        "index.html",
        {
            "rooms": rooms,
            "user_reservations": user_reservations,
            "time_slots": time_slots,
            "all_reservations": all_reservations,
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("index")

    error = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)
            return redirect("index")

        error = "Invalid username or password."

    return render(request, "login.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("login")
