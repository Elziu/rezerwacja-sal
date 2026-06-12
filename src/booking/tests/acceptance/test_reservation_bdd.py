import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from booking.models import Room, Reservation
from booking.services import ReservationService
from django.contrib.auth import get_user_model
from datetime import date, time, timedelta
from django.core.exceptions import ValidationError

User = get_user_model()

pytestmark = pytest.mark.django_db

scenarios('features/reservation.feature')

@pytest.fixture
def context():
    return {}

@given(parsers.parse('istnieje dostępna sala "{name}"'))
def create_room(name):
    Room.objects.create(name=name, status=Room.RoomStatus.AVAILABLE)

@given(parsers.parse('istnieje użytkownik "{username}"'))
def create_user(context, username):
    user, _ = User.objects.get_or_create(username=username, defaults={'password': 'password'})
    context['user'] = user

@given(parsers.parse('sala "{room_name}" ma już rezerwację na jutro od "{start}" do "{end}"'))
def create_existing_reservation(room_name, start, end):
    room = Room.objects.get(name=room_name)

    owner, _ = User.objects.get_or_create(username="owner", defaults={'password': 'password'})

    tomorrow = date.today() + timedelta(days=1)

    # Obsługa formatu HH:MM
    h_start, m_start = map(int, start.split(':'))
    h_end, m_end = map(int, end.split(':'))
    t_start = time(h_start, m_start)
    t_end = time(h_end, m_end)

    ReservationService.create_reservation(owner, room, tomorrow, t_start, t_end)

@when(parsers.parse('użytkownik rezerwuje salę "{room_name}" na jutro od "{start}" do "{end}"'))
def attempt_reservation(context, room_name, start, end):
    room = Room.objects.get(name=room_name)
    user = context.get('user') or User.objects.first()

    tomorrow = date.today() + timedelta(days=1)

    h_start, m_start = map(int, start.split(':'))
    h_end, m_end = map(int, end.split(':'))
    t_start = time(h_start, m_start)
    t_end = time(h_end, m_end)

    try:
        reservation = ReservationService.create_reservation(user, room, tomorrow, t_start, t_end)
        context['reservation'] = reservation
        context['error'] = None
    except ValidationError as e:
        context['reservation'] = None
        context['error'] = e


@given(parsers.parse('użytkownik "{username}" posiada rezerwację sali "{room_name}" na jutro od "{start}" do "{end}"'))
def create_reservation_for_edit(context, username, room_name, start, end):
    room = Room.objects.get(name=room_name)
    user, _ = User.objects.get_or_create(username=username, defaults={'password': 'password'})
    context['user'] = user

    tomorrow = date.today() + timedelta(days=1)

    h_start, m_start = map(int, start.split(':'))
    h_end, m_end = map(int, end.split(':'))
    t_start = time(h_start, m_start)
    t_end = time(h_end, m_end)

    reservation = ReservationService.create_reservation(user, room, tomorrow, t_start, t_end)
    context['reservation'] = reservation

@when(parsers.parse('użytkownik zmienia swoją rezerwację na jutro od "{start}" do "{end}"'))
def edit_reservation(context, start, end):
    reservation = context['reservation']
    user = context['user']
    tomorrow = date.today() + timedelta(days=1)

    h_start, m_start = map(int, start.split(':'))
    h_end, m_end = map(int, end.split(':'))
    t_start = time(h_start, m_start)
    t_end = time(h_end, m_end)

    try:
        updated_res = ReservationService.modify_reservation(reservation, tomorrow, t_start, t_end, user)
        context['reservation'] = updated_res
        context['error'] = None
    except ValidationError as e:
        context['error'] = e

@then('rezerwacja powinna zostać zaktualizowana')
def check_reservation_updated(context):
    assert context['reservation'] is not None
    assert context['error'] is None

@then(parsers.parse('godziny rezerwacji powinny wynosić od "{start}" do "{end}"'))
def check_reservation_times(context, start, end):
    r = context['reservation']

    h_start, m_start = map(int, start.split(':'))
    h_end, m_end = map(int, end.split(':'))
    expected_start = time(h_start, m_start)
    expected_end = time(h_end, m_end)

    assert r.time_from == expected_start
    assert r.time_to == expected_end

# ----------------- NOWE KROKI DLA SCENARIUSZA ANULOWANIA -----------------

@when('użytkownik anuluje swoją rezerwację')
def cancel_reservation(context):
    reservation = context['reservation']
    user = context['user']
    try:
        ReservationService.cancel_reservation(reservation, user)
        reservation.refresh_from_db()
        context['reservation'] = reservation
    except ValidationError as e:
        context['error'] = e

@then('rezerwacja powinna zostać utworzona pomyślnie')
def check_reservation_created(context):
    assert context['reservation'] is not None, f"Oczekiwano sukcesu, ale wystąpił błąd: {context.get('error')}"
    assert context['error'] is None

@then(parsers.parse('status rezerwacji powinien być "{status}"'))
def check_reservation_status(context, status):
    assert context['reservation'].status == status

@then('rezerwacja powinna się nie udać')
def check_reservation_failed(context):
    assert context['reservation'] is None
    assert context['error'] is not None

@then(parsers.parse('powinien wystąpić błąd o treści "{message}"'))
def check_error_message(context, message):
    err = context['error']
    # ValidationError może zawierać listę wiadomości
    if hasattr(err, 'messages'):
        assert message in err.messages
    else:
        assert message in str(err)
