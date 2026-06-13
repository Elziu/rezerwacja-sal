from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from booking.services import ReservationService


@login_required
def index(request):
    # Pobierz sale z rezerwacjami przez serwis
    rooms_with_availability = ReservationService.get_rooms_with_availability()

    # Rezerwacje użytkownika
    reservations = ReservationService.get_user_reservations(request.user)

    # Generuj listę godzin
    hours = ReservationService.generate_time_slots()

    # Uczestnicy i zaproszenia
    participant_options = ReservationService.get_selectable_participants(request.user)
    invitations = ReservationService.get_user_invitations(request.user)

    return render(request, "index.html", {
        "rooms_with_availability": rooms_with_availability,
        "reservations": reservations,
        "hours": hours,
        "participant_options": participant_options,
        "invitations": invitations,
    })



def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("/")
        else:
            return render(request, "login.html", {"invalid": True})

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("/")
