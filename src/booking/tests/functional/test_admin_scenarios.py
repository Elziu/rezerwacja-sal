import pytest
import asyncio
from datetime import date, timedelta, time
from pyppeteer import launch
from django.contrib.auth import get_user_model
from booking.models import Room, Reservation
from asgiref.sync import sync_to_async
import nest_asyncio

nest_asyncio.apply()

User = get_user_model()

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_admin_flow(live_server):
    """
    Testuje scenariusze Administratora:
    UC-2: Logowanie administratora
    UC-4: Wylogowanie administratora
    UC-10: Zmiana statusu sali
    UC-11: Przegląd wszystkich rezerwacji
    UC-12: Usunięcie rezerwacji
    """
    # SETUP
    admin = await sync_to_async(User.objects.create_superuser)(username="admin", password="password", email="admin@test.com")
    user = await sync_to_async(User.objects.create_user)(username="employee_for_admin", password="password")
    room = await sync_to_async(Room.objects.create)(name="Konferencyjna Admin", status=Room.RoomStatus.AVAILABLE)
    room_id = room.id

    # Tworzymy rezerwację, którą admin usunie
    tomorrow = date.today() + timedelta(days=1)
    await sync_to_async(Reservation.objects.create)(
        room=room,
        date=tomorrow,
        time_from=time(14, 0),
        time_to=time(15, 0),
        created_by=user,
        status="ACTIVE"
    )

    browser = await launch(
        headless=False,
        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
    )
    page = await browser.newPage()
    await page.setViewport({'width': 1920, 'height': 1080})

    try:
        # UC-2: Logowanie jako Admin (do aplikacji, potem przejście do panelu)
        await page.goto(f"{live_server.url}/login/")
        await asyncio.sleep(1.0)
        await page.type('input[name="username"]', "admin")
        await asyncio.sleep(0.5)
        await page.type('input[name="password"]', "password")
        await asyncio.sleep(0.5)
        await asyncio.gather(page.waitForNavigation(), page.click('button'))
        await asyncio.sleep(1.0)
        assert "Wyloguj" in await page.content()

        # Przejście do panelu administratora
        await page.goto(f"{live_server.url}/admin/booking/room/")
        await asyncio.sleep(1.0)

        # Jeśli Django wymaga ponownego logowania do /admin/ (zależnie od cookies), logujemy się
        title = await page.title()
        if "Log in" in title:
             await page.type('input[name="username"]', "admin")
             await page.type('input[name="password"]', "password")
             await asyncio.gather(page.waitForNavigation(), page.click('input[type="submit"]'))
             await asyncio.sleep(1.0)

        # UC-10: Zmiana statusu sali
        # Wybieramy salę z listy
        await asyncio.gather(page.waitForNavigation(), page.click(f'a[href*="/booking/room/{room_id}/change/"]'))
        await asyncio.sleep(1.0)

        # Zmieniamy status na UNAVAILABLE
        await page.select('select[name="status"]', 'UNAVAILABLE')
        await asyncio.sleep(0.5)
        await asyncio.gather(page.waitForNavigation(), page.click('input[name="_save"]'))
        await asyncio.sleep(1.0)

        content = await page.content()
        assert "was changed successfully" in content

        # UC-11: Przegląd listy rezerwacji
        await asyncio.gather(page.waitForNavigation(), page.click('a[href="/admin/booking/reservation/"]'))
        await asyncio.sleep(1.0)

        # Sprawdzenie obecności tabeli/listy (np. nagłówek "Select reservation to change")
        content = await page.content()
        assert "Select reservation to change" in content

        # UC-12: Usunięcie rezerwacji
        # Zaznaczamy pierwszy checkbox przy rezerwacji
        await page.click('.action-select')
        await asyncio.sleep(0.5)
        # Wybieramy akcję "Delete selected reservations"
        await page.select('select[name="action"]', 'delete_selected')
        await asyncio.sleep(0.5)
        # Klikamy "Go"
        await asyncio.gather(page.waitForNavigation(), page.click('button[name="index"]'))
        await asyncio.sleep(1.0)

        # Potwierdzenie usunięcia
        content = await page.content()
        # Django admin page title for deletion is "Delete multiple objects"
        assert "Delete multiple objects" in content
        await asyncio.gather(page.waitForNavigation(), page.click('input[type="submit"]'))
        await asyncio.sleep(1.0)

        content = await page.content()
        assert "Successfully deleted" in content

        # UC-4: Wylogowanie administratora (z panelu admina)
        # Django 5+ uses POST for logout, so looking for a submit button in logout form
        try:
             # Try finding button by text or form
             logout_btn = await page.xpath("//button[contains(., 'Log out')]")
             if logout_btn:
                 await asyncio.gather(page.waitForNavigation(), logout_btn[0].click())
             else:
                 # Fallback to form submit selector
                 await asyncio.gather(page.waitForNavigation(), page.click('form[action*="/logout/"] button'))
        except Exception:
             # If exact selector fails, try generic /admin/logout/ link just in case (older django)
             await asyncio.gather(page.waitForNavigation(), page.click('a[href="/admin/logout/"]'))

        await asyncio.sleep(1.0)
        content = await page.content()
        assert "Logged out" in content

    finally:
        await browser.close()
