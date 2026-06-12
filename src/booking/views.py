from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from booking.models import Room, Reservation
from booking.services import ReservationService


@login_required
def new_reservation(request):
    if request.method != "POST":
        return redirect("/")

    room_id = request.POST.get("room")
    date = request.POST.get("date")
    time_from = request.POST.get("time_from")
    time_to = request.POST.get("time_to")

    room = get_object_or_404(Room, id=room_id)

    try:
        ReservationService.create_reservation(
            user=request.user,
            room=room,
            date=date,
            time_from=time_from,
            time_to=time_to
        )
        messages.success(request, "Rezerwacja została utworzona.")
    except Exception as e:
        messages.error(request, str(e))

    return redirect("/")


@login_required
def edit_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    # Użydtkownik może edytować TYLKO własne rezerwacje
    if reservation.created_by != request.user and not request.user.is_superuser:
        messages.error(request, "Nie masz uprawnień do edytowania tej rezerwacji.")
        return redirect("/")

    # Tylko aktywne rezerwacje można edytować
    if reservation.status != Reservation.ReservationStatus.ACTIVE:
        messages.error(request, "Można edytować tylko aktywne rezerwacje.")
        return redirect("/")

    if request.method == "GET":
        # Wyświetl formularz edycji
        rooms = ReservationService.get_available_rooms()
        hours = ReservationService.generate_time_slots()
        
        # Pobierz rezerwacje dla wszystkich sal (wykluczając edytowaną)
        rooms_with_availability = []
        for room in rooms:
            room_reservations = Reservation.objects.filter(
                room=room,
                status=Reservation.ReservationStatus.ACTIVE
            ).exclude(id=reservation_id).values('date', 'time_from', 'time_to')
            
            rooms_with_availability.append({
                'room': room,
                'reservations': list(room_reservations)
            })
        
        return render(request, "edit_reservation.html", {
            "reservation": reservation,
            "rooms_with_availability": rooms_with_availability,
            "hours": hours,
        })
    
    elif request.method == "POST":
        # Zapisz zmiany
        room_id = request.POST.get("room")
        date = request.POST.get("date")
        time_from = request.POST.get("time_from")
        time_to = request.POST.get("time_to")

        room = get_object_or_404(Room, id=room_id)

        try:
            # Jeśli zmieniono salę, zaktualizuj ją
            if reservation.room.id != int(room_id):
                reservation.room = room
            
            ReservationService.modify_reservation(
                reservation=reservation,
                date=date,
                time_from=time_from,
                time_to=time_to,
                user=request.user
            )
            messages.success(request, "Rezerwacja została zaktualizowana.")
        except Exception as e:
            messages.error(request, str(e))

        return redirect("/")


@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    # Użytkownik może anulować TYLKO własne rezerwacje
    if reservation.created_by != request.user and not request.user.is_superuser:
        messages.error(request, "Nie masz uprawnień do anulowania tej rezerwacji.")
        return redirect("/")

    reservation.status = Reservation.ReservationStatus.CANCELLED
    reservation.save()

    messages.success(request, "Rezerwacja została anulowana.")
    return redirect("/")