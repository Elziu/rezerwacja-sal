Feature: Zarządzanie rezerwacjami
    Jako pracownik firmy
    Chcę rezerwować sale konferencyjne
    Aby móc przeprowadzać spotkania

    Scenario: Pomyślna rezerwacja sali
        Given istnieje dostępna sala "Sala Konferencyjna A"
        And istnieje użytkownik "Jan Kowalski"
        When użytkownik rezerwuje salę "Sala Konferencyjna A" na jutro od "10:00" do "12:00"
        Then rezerwacja powinna zostać utworzona pomyślnie
        And status rezerwacji powinien być "ACTIVE"

    Scenario: Próba rezerwacji zajętej sali
        Given istnieje dostępna sala "Sala Mała"
        And istnieje użytkownik "Anna Nowak"
        And sala "Sala Mała" ma już rezerwację na jutro od "10:00" do "12:00"
        When użytkownik rezerwuje salę "Sala Mała" na jutro od "11:00" do "13:00"
        Then rezerwacja powinna się nie udać
        And powinien wystąpić błąd o treści "Sala jest zajęta w wybranym przedziale czasu."

    Scenario: Edycja rezerwacji
        Given istnieje dostępna sala "Sala Edytowana"
        And istnieje użytkownik "Marek Edytor"
        And użytkownik "Marek Edytor" posiada rezerwację sali "Sala Edytowana" na jutro od "14:00" do "16:00"
        When użytkownik zmienia swoją rezerwację na jutro od "15:00" do "17:00"
        Then rezerwacja powinna zostać zaktualizowana
        And godziny rezerwacji powinny wynosić od "15:00" do "17:00"

    Scenario: Anulowanie rezerwacji
        Given istnieje dostępna sala "Sala Anulowana"
        And istnieje użytkownik "Piotr Anulujący"
        And użytkownik "Piotr Anulujący" posiada rezerwację sali "Sala Anulowana" na jutro od "10:00" do "11:00"
        When użytkownik anuluje swoją rezerwację
        Then status rezerwacji powinien być "CANCELLED"
