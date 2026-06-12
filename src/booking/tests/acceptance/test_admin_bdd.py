import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from booking.models import Room, Reservation
from booking.services import ReservationService
from django.contrib.auth import get_user_model
from datetime import date, time, timedelta

User = get_user_model()

pytestmark = pytest.mark.django_db

scenarios('features/admin.feature')

@pytest.fixture
def context():
    return {}

@given(parsers.parse('istnieje dostępna sala "{name}"'))
def create_room(name):
    # This step was missing in this file but present in others.
    # Ideally steps should be shared (conftest.py), but duplication is fine for now.
    Room.objects.get_or_create(name=name, status=Room.RoomStatus.AVAILABLE)

@given(parsers.parse('istnieje użytkownik "{username}"'))
def create_regular_user(username):
    User.objects.get_or_create(username=username, defaults={'password': 'password'})

@given(parsers.parse('zalogowany jest administrator "{username}"'))
def create_logged_in_admin(context, username):
    admin = User.objects.create_superuser(username=username, password='password')
    context['admin'] = admin
    # In real web flow we'd log in, here we just have the user object for permission checks if needed
    # Logic in Service/Views typically checks `request.user.is_superuser`

@given(parsers.parse('sala "{room_name}" ma już rezerwację na jutro od "{start}" do "{end}" utworzoną przez "{username}"'))
def create_reservation_for_delete(context, room_name, start, end, username):
    room = Room.objects.get(name=room_name)
    user, _ = User.objects.get_or_create(username=username, defaults={'password': 'password'})

    tomorrow = date.today() + timedelta(days=1)
    h_start, m_start = map(int, start.split(':'))
    h_end, m_end = map(int, end.split(':'))

    reservation = ReservationService.create_reservation(user, room, tomorrow, time(h_start, m_start), time(h_end, m_end))
    context['reservation_to_delete'] = reservation

@when(parsers.parse('administrator zmienia status sali "{room_name}" na "{new_status}"'))
def change_room_status(room_name, new_status):
    room = Room.objects.get(name=room_name)
    # Using Model or dedicated Service method if exists.
    # Usually admin uses Django Admin which simply saves the model.
    room.status = new_status
    room.save()

@then(parsers.parse('status sali "{room_name}" powinien być "{expected_status}"'))
def check_room_status(room_name, expected_status):
    room = Room.objects.get(name=room_name)
    assert room.status == expected_status

@then(parsers.parse('sala o nazwie "{room_name}" powinna być niedostępna dla rezerwacji'))
def check_room_unavailable(room_name):
    room = Room.objects.get(name=room_name)
    assert not room.is_available()

@when(parsers.parse('administrator usuwa rezerwację sali "{room_name}" z jutra z godziny "{start}"'))
def delete_reservation(context, room_name, start):
    # Admin deletion typically means Model.delete() via Django Admin or custom view
    # BDD tests the outcome.
    reservation = context['reservation_to_delete']
    reservation.delete()
    # or ReservationService.cancel_reservation if soft delete logic, but Requirement says "Usuwa rezerwację"

@then('rezerwacja powinna zostać usunięta')
def check_reservation_deleted(context):
    res_id = context['reservation_to_delete'].id
    assert not Reservation.objects.filter(id=res_id).exists()

@then(parsers.parse('sala "{room_name}" powinna być wolna jutro od "{start}" do "{end}"'))
def check_room_free(room_name, start, end):
    room = Room.objects.get(name=room_name)
    tomorrow = date.today() + timedelta(days=1)
    h_start, m_start = map(int, start.split(':'))
    h_end, m_end = map(int, end.split(':'))

    is_conflict = ReservationService.check_conflicts(room, tomorrow, time(h_start, m_start), time(h_end, m_end))
    assert not is_conflict
