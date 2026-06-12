Feature: Logowanie i autoryzacja
    Jako użytkownik (pracownik lub administrator)
    Chcę się zalogować i wylogować
    Aby mieć dostęp do systemu zgodnie z uprawnieniami

    Scenario: Logowanie jako użytkownik
        Given istnieje użytkownik "pracownik1" z hasłem "haslo123"
        When użytkownik loguje się używając loginu "pracownik1" i hasła "haslo123"
        Then logowanie powinno się powieść
        And użytkownik powinien mieć uprawnienia zwykłego pracownika

    Scenario: Logowanie jako administrator
        Given istnieje administrator "admin1" z hasłem "admin123"
        When użytkownik loguje się używając loginu "admin1" i hasła "admin123"
        Then logowanie powinno się powieść
        And użytkownik powinien mieć uprawnienia administratora

    Scenario: Nieudane logowanie (błędne hasło)
        Given istnieje użytkownik "pracownik2" z hasłem "poprawne"
        When użytkownik loguje się używając loginu "pracownik2" i hasła "bledne"
        Then logowanie powinno się nie udać
