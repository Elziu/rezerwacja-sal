Feature: Administracja systemem
    Jako administrator
    Chcę zarządzać salami i rezerwacjami
    Aby utrzymać porządek w systemie

    Scenario: Zmiana statusu sali
        Given istnieje dostępna sala "Sala Remontowana"
        And zalogowany jest administrator "admin_master"
        When administrator zmienia status sali "Sala Remontowana" na "UNAVAILABLE"
        Then status sali "Sala Remontowana" powinien być "UNAVAILABLE"
        And sala o nazwie "Sala Remontowana" powinna być niedostępna dla rezerwacji

    Scenario: Admin usuwa istniejącą rezerwację
        Given istnieje dostępna sala "Sala Spotkań"
        And istnieje użytkownik "Jan Kowalski"
        And sala "Sala Spotkań" ma już rezerwację na jutro od "12:00" do "14:00" utworzoną przez "Jan Kowalski"
        And zalogowany jest administrator "admin_deleter"
        When administrator usuwa rezerwację sali "Sala Spotkań" z jutra z godziny "12:00"
        Then rezerwacja powinna zostać usunięta
        And sala "Sala Spotkań" powinna być wolna jutro od "12:00" do "14:00"
