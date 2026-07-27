import swisseph as swe
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import os

# Tworzy ścieżkę absolutną do folderu 'ephe' w Twoim projekcie
SCIEZKA_EPHE = os.path.join(os.getcwd(), 'eph_data')

# Informujesz pyswisseph, gdzie leżą pliki
swe.set_ephe_path(SCIEZKA_EPHE)

# Teraz przy obliczeniach wywołujesz domyślną flagę silnika:
flagi = swe.FLG_SWIEPH

def jd_do_datetime_lokalnego(jd, strefa_czasowa):
    """
    Konwertuje czas Julian Date (UT) ze Swiss Ephemeris na obiekt datetime
    w konkretnej, lokalnej strefie czasowej (np. Europe/Warsaw).
    """
    # swe.revjul zwraca (rok, miesiąc, dzień, godziny_w_formacie_zmiennoprzecinkowym)
    rok, miesiac, dzien, godzina_float = swe.revjul(jd, swe.GREG_CAL)

    godzina = int(godzina_float)
    minuta = int((godzina_float - godzina) * 60)
    sekunda = int((((godzina_float - godzina) * 60) - minuta) * 60)

    # Tworzymy czas w UTC i nakładamy strefę docelową
    dt_utc = datetime(rok, miesiac, dzien, godzina, minuta, sekunda, tzinfo=timezone.utc)
    return dt_utc.astimezone(strefa_czasowa)


def wyznacz_wschod_zachod(data_start_utc, obiekt_swe, lon, lat, wysokosc_npm=0.0):
    """
    Wylicza najbliższy wschód i zachód podanego obiektu od zadanego czasu.
    """
    jd_start = swe.julday(
        data_start_utc.year,
        data_start_utc.month,
        data_start_utc.day,
        data_start_utc.hour + data_start_utc.minute / 60.0,
        swe.GREG_CAL
    )

    pozycja = (lon, lat, wysokosc_npm)
    cisnienie = 1013.25
    temperatura = 15.0
    flagi_obliczeniowe = swe.FLG_SWIEPH

    # Zmieniony układ argumentów:
    # (jd_start, body, typ_zjawiska, pozycja, cisnienie, temperatura, flagi)

    wynik_wschod = swe.rise_trans(
        jd_start,  # 1. Czas startowy
        obiekt_swe,  # 2. Obiekt (np. swe.CERES lub 'Sirius')
        swe.CALC_RISE | swe.BIT_DISC_CENTER,  # 3. Flaga zjawiska (Wschód)
        pozycja,  # 4. (lon, lat, wysokosc)
        cisnienie,  # 5. Ciśnienie
        temperatura,  # 6. Temperatura
        flagi_obliczeniowe  # 7. Flagi ephemeryd
    )

    wynik_zachod = swe.rise_trans(
        jd_start,
        obiekt_swe,
        swe.CALC_SET | swe.BIT_DISC_CENTER,  # Flaga zjawiska (Zachód)
        pozycja,
        cisnienie,
        temperatura,
        flagi_obliczeniowe
    )

    # Zwracana struktura to krotka: (uzyte_flagi, (JD_event, val2, val3...))
    # Dlatego wyciągamy element [1][0]
    return wynik_wschod[1][0], wynik_zachod[1][0]


# ==========================================
# Użycie funkcji w praktyce
# ==========================================
if __name__ == "__main__":
    # Opcjonalne: Ustawienie ścieżki do plików, w tym Twojego DE440.
    # Jeśli zakomentujesz, użyje wbudowanego Moshiera/DE431.
    # swe.set_ephe_path('sciezka/do/plikow')

    strefa_polska = ZoneInfo("Europe/Warsaw")

    # Szukamy zjawisk od północy 27 lipca 2026 czasu uniwersalnego
    czas_start = datetime(2026, 7, 27, 0, 0, 0, tzinfo=timezone.utc)

    # Zastąpiliśmy twardy kod na Greenwich Twoimi współrzędnymi z Olsztyna
    olsztyn_lon = 20.4801
    olsztyn_lat = 53.7784

    # Wywołanie z obiektem Ceres (swe.CERES)
    # Możesz tu wstawić swe.JUPITER, swe.MOON, itp.
    jd_wschod, jd_zachod = wyznacz_wschod_zachod(
        czas_start,
        swe.MERCURY,
        olsztyn_lon,
        olsztyn_lat
    )

    # Konwersja surowych Julian Date na przyjazny czas dla użytkownika
    wschod_lokalny = jd_do_datetime_lokalnego(jd_wschod, strefa_polska)
    zachod_lokalny = jd_do_datetime_lokalnego(jd_zachod, strefa_polska)

    print("-" * 40)
    print("Dane dla: merkury (Olsztyn)")
    print(f"Wschód (czas lokalny): {wschod_lokalny.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Zachód (czas lokalny): {zachod_lokalny.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("-" * 40)

    swe.close()  # Zwalnia pamięć (dobra praktyka po zakończeniu obliczeń)