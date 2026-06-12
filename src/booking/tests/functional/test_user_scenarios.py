import pytest
import asyncio
from datetime import date, timedelta
from pyppeteer import launch
from django.contrib.auth import get_user_model
from booking.models import Room, Reservation
from asgiref.sync import sync_to_async
import nest_asyncio

nest_asyncio.apply()

User = get_user_model()

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_user_flow(live_server):
    """
    Testuje scenariusze pracownika biurowego:
    UC-1: Logowanie
    UC-3: Wylogowanie
    UC-5: Przeglądanie sal
    UC-6: Utworzenie rezerwacji
    UC-7: Edycja rezerwacji
    UC-8: Anulowanie rezerwacji
    UC-9: Przegląd rezerwacji
    """
    # SETUP
    await sync_to_async(User.objects.create_user)(username="employee", password="password", email="emp@test.com")
    room = await sync_to_async(Room.objects.create)(name="Konferencyjna User", status=Room.RoomStatus.AVAILABLE)
    room_id = room.id

    tomorrow = date.today() + timedelta(days=1)
    if tomorrow.weekday() >= 5:
        tomorrow += timedelta(days=2)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")
    tomorrow_day = tomorrow.day

    browser = await launch(
        headless=False,

        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--start-fullscreen']
    )
    page = await browser.newPage()
    await page.setViewport({'width': 1920, 'height': 1080})

    try:
        # UC-1: Logowanie użytkownika
        await page.goto(f"{live_server.url}/login/")
        await asyncio.sleep(1.0) # Delay for visual verification
        await page.type('input[name="username"]', "employee")
        await asyncio.sleep(0.5)
        await page.type('input[name="password"]', "password")
        await asyncio.sleep(0.5)
        await asyncio.gather(page.waitForNavigation(), page.click('button'))
        await asyncio.sleep(1.0)

        content = await page.content()
        assert "Wyloguj" in content
        assert "Twoje rezerwacje" in content

        # UC-9: Panel rezerwacji (początkowo pusty lub nagłówek)
        assert "Brak rezerwacji" in content or "Twoje rezerwacje" in content

        # UC-5 & UC-6: Wybór daty i utworzenie rezerwacji
        await asyncio.sleep(1.0)
        # Using evaluate to set value directly to avoid UI flakiness with Pikaday in test
        await page.evaluate(f"document.getElementById('reservation-datepicker').value = '{tomorrow_str}'")
        await page.evaluate("""
            const input = document.getElementById('reservation-datepicker');
            input.dispatchEvent(new Event('change', { bubbles: true }));
        """)
        await asyncio.sleep(1.0)

        await page.select('#time-from', '10:00')
        await asyncio.sleep(0.5)
        await page.select('#time-to', '12:00')
        await asyncio.sleep(1.0)

        # Czekamy na przefiltrowanie sal i klikamy w kartę sali
        room_card_selector = f'.room-card[data-room-id="{room_id}"]'

        # Wait for card to be available (ensure it does not have opacity-50 class which means unavailable)
        await page.waitForSelector(f'{room_card_selector}:not(.opacity-50)', {'visible': True})
        await asyncio.sleep(0.5)

        # Click the room card to select it
        await page.click(room_card_selector)
        await asyncio.sleep(1.0)

        # Verify hidden input is set
        hidden_val = await page.evaluate("document.getElementById('selected-room-id').value")

        if hidden_val != str(room_id):
            # Fallback: force click via JS if standard click failed
            await page.evaluate(f"document.querySelector('{room_card_selector}').click()")
            await asyncio.sleep(1.0)

            # Re-verify
            hidden_val = await page.evaluate("document.getElementById('selected-room-id').value")
            assert hidden_val == str(room_id), "Room selection failed - card click did not set hidden input"

        # Zatwierdzenie formularza
        # Handle potential alert if validation fails to avoid stuck test
        page.on('dialog', lambda dialog: asyncio.ensure_future(dialog.dismiss()))

        await asyncio.gather(page.waitForNavigation(), page.click('#reservation-form button'))
        await asyncio.sleep(2.0)

        content = await page.content()
        assert "Rezerwacja została utworzona" in content
        assert "Konferencyjna User" in content
        assert "10:00 – 12:00" in content

        # UC-7: Edycja rezerwacji
        await asyncio.sleep(1.0)
        await asyncio.gather(page.waitForNavigation(), page.click(f'a[href*="/edit/"]'))
        await asyncio.sleep(1.0)
        await page.select('#time-to', '13:00')
        await asyncio.sleep(1.0)
        await asyncio.gather(page.waitForNavigation(), page.click('button'))
        await asyncio.sleep(2.0)

        content = await page.content()
        assert "Rezerwacja została zaktualizowana" in content
        assert "10:00 – 13:00" in content

        # UC-8: Anulowanie rezerwacji
        await asyncio.sleep(1.0)
        await asyncio.gather(page.waitForNavigation(), page.click(f'a[href*="/cancel/"]'))
        await asyncio.sleep(2.0)
        content = await page.content()
        # UC-8: Usunięcie rezerwacji ze stronie głównej -> powinno być pusto lub brak tej rezerwacji
        # Since it was the only reservation, we expect "Brak rezerwacji"
        if "Brak rezerwacji" not in content:
             # Fallback if logic changes: ensure "Anulowana" is NOT active or just ensure the ACTIVE one is gone
             assert "10:00 – 13:00" not in content

        # UC-3: Wylogowanie
        await asyncio.sleep(1.0)
        await asyncio.gather(page.waitForNavigation(), page.click('a[href="/logout/"]'))
        await asyncio.sleep(1.0)
        content = await page.content()
        assert "Zaloguj się" in content

        # UC-1 A1: Błędne logowanie
        await asyncio.sleep(1.0)
        await page.goto(f"{live_server.url}/login/")
        await asyncio.sleep(0.5)
        await page.type('input[name="username"]', "employee")
        await page.type('input[name="password"]', "wrongpassword")
        await asyncio.sleep(0.5)
        await asyncio.gather(page.waitForNavigation(), page.click('button'))
        await asyncio.sleep(1.0)
        content = await page.content()
        assert "Niepoprawna nazwa użytkownika lub hasło" in content

    finally:
        await browser.close()
