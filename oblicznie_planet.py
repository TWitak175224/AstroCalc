import datetime
import os
from typing import Any
from zoneinfo import ZoneInfo  # Standardowa biblioteka Pythona od wersji 3.9+

import swisseph as swe


def oblicz_wysokosc(jd_utc, body_id, lon, lat, flags):
    """
    Oblicza wysokość i azymut obiektu nad horyzontem dla konkretnego czasu.

    :param jd_utc: Czas w formacie Daty Juliańskiej (UTC) dla danej godziny.
    :param body_id: ID obiektu (np. swe.SUN, swe.MOON).
    :param geopos: Krotka ze współrzędnymi (długość, szerokość, wysokość n.p.m.) - np. (20.48, 53.77, 100.0)
    :param flags: Flagi konfiguracyjne silnika (np. swe.FLG_SWIEPH)
    :return: (azymut, wysokosc_rzeczywista, wysokosc_pozorna)
    """
    # KROK 1: Pobieramy współrzędne równikowe (Rektascensja, Deklinacja, Odległość).
    # Dodajemy flagę swe.FLG_EQUATORIAL, by wymusić odpowiedni układ odniesienia
    flagi_rownikowe = flags | swe.FLG_EQUATORIAL
    coords, ret_flag = swe.calc_ut(jd_utc, body_id, flagi_rownikowe)
    geopos = (float(lon), float(lat), 0.0)
    # calc_ut zwraca krotkę 6 wartości. Do transformacji potrzebujemy pierwszych trzech:
    # coords[0] - Rektascensja (RA)
    # coords[1] - Deklinacja (Dec)
    # coords[2] - Odległość (Distance)
    pozycja_rownikowa = (coords[0], coords[1], coords[2])

    # Parametry atmosferyczne do obliczenia refrakcji (załamania światła)
    # 1013.25 to standardowe ciśnienie w hPa, 15.0 to temperatura w Celsjuszach
    cisnienie = 1013.25
    temperatura = 15.0

    # KROK 2: Transformacja na układ horyzontalny za pomocą swe.azalt
    # Flaga swe.EQU2HOR oznacza konwersję z układu równikowego (Equatorial) na horyzontalny (Horizontal)
    wynik_horyzontalny = swe.azalt(
        jd_utc,
        swe.EQU2HOR,
        geopos,
        cisnienie,
        temperatura,
        pozycja_rownikowa
    )

    # Wynik to krotka: (azymut, wysokosc_rzeczywista, wysokosc_pozorna, ...)
    azymut = wynik_horyzontalny[0]
    wysokosc_rzeczywista = wynik_horyzontalny[1]
    wysokosc_pozorna = wynik_horyzontalny[2]

    return azymut, wysokosc_rzeczywista, wysokosc_pozorna


def sprawdz_typ_efemeryd(ephe_path=None):
    """
    Sprawdza, z jakiego źródła danych korzysta silnik Swiss Ephemeris.
    """

    # Używamy dowolnej daty juliańskiej do testu (np. 1 stycznia 2026)
    jd_test = swe.julday(2026, 1, 1)

    # Żądamy użycia precyzyjnych plików Swiss Ephemeris
    wymagana_flaga = swe.FLG_SWIEPH

    try:
        # calc_ut zwraca krotkę: (współrzędne, zwrócona_flaga)
        # Wykonujemy test dla Słońca (swe.SUN)
        wynik, zwrocona_flaga = swe.calc_ut(jd_test, swe.SUN, wymagana_flaga)

        print("\n--- RAPORT DIAGNOSTYCZNY SILNIKA ---")

        # Sprawdzamy bitowo, co dokładnie kryje się w zwróconej fladze
        if zwrocona_flaga & swe.FLG_SWIEPH:
            print("[OK] Silnik korzysta z precyzyjnych plików Swiss Ephemeris (*.se1).")
        elif zwrocona_flaga & swe.FLG_MOSEPH:
            print("[OSTRZEŻENIE] Brak plików *.se1! Silnik używa wbudowanego algorytmu Moshiera.")
            print("Rozwiązanie: Sprawdź, czy pliki znajdują się w ścieżce ephe_path.")
        elif zwrocona_flaga & swe.FLG_JPLEPH:
            print("[OK] Silnik korzysta z bardzo precyzyjnych efemeryd JPL NASA.")
        else:
            print(f"[?] Silnik korzysta z nierozpoznanego algorytmu. Kod flagi: {zwrocona_flaga}")

    except Exception as e:
        print(f"[BŁĄD KRYTYCZNY] Awaria silnika podczas testu: {e}")

    finally:
        # Zawsze zwalniamy pamięć z załadowanych efemeryd
        swe.close()


def _jd_to_datetime(jd: float) -> datetime.datetime:
    """
    Prywatna metoda pomocnicza: zamienia datę juliańską (JD)
    z powrotem na natywny obiekt datetime (w UTC).
    """
    year, month, day, decimal_hour = swe.revjul(jd)

    hours = int(decimal_hour)
    minutes = int((decimal_hour - hours) * 60)
    seconds = int((((decimal_hour - hours) * 60) - minutes) * 60)

    return datetime.datetime(year, month, day, hours, minutes, seconds, tzinfo=datetime.timezone.utc)


class EphemerisEngine:
    def __init__(self, ephe_path: str):
        """
        Inicjalizacja silnika astronomicznego opartego na Swiss Ephemeris.

        :param ephe_path: Bezwzględna lub względna ścieżka do katalogu z plikami .se1
        """
        # 1. Defensywne sprawdzanie ścieżki
        if not os.path.isdir(ephe_path):
            raise FileNotFoundError(
                f"Krytyczny błąd silnika: Nie znaleziono katalogu z efemerydami pod ścieżką '{ephe_path}'. "
                f"Upewnij się, że pliki .se1 znajdują się we wskazanym miejscu."
            )

        # 2. Rejestracja ścieżki w bibliotece C
        swe.set_ephe_path(ephe_path)
        self.ephe_path = ephe_path

        # 3. Główna flaga silnika (Wymuszamy najwyższą precyzję plików .se1)
        # Dodajemy flagę FLG_SPEED za pomocą operatora bitowego OR (|),
        # na wypadek gdybyś w przyszłości potrzebował prędkości poruszania się obiektów
        self.flags = swe.FLG_SWIEPH | swe.FLG_SPEED

        # 4. Inicjalizacja wewnętrznego mappera z polskimi nazwami obiektów
        self.polish_names = {
            swe.SUN: "SŁOŃCE",
            swe.MOON: "KSIĘŻYC",
            swe.MERCURY: "MERKURY",
            swe.VENUS: "WENUS",
            swe.MARS: "MARS",
            swe.JUPITER: "JOWISZ",
            swe.SATURN: "SATURN",
            swe.URANUS: "URAN",
            swe.NEPTUNE: "NEPTUN",
            swe.PLUTO: "PLUTON",
            swe.MEAN_APOG: "Średnia Lilith",
            swe.OSCU_APOG: "Prawdziwa Lilith",
            swe.TRUE_NODE: "Prawdziwy Węzeł Północny",
            swe.MEAN_NODE: "Średni Węzeł Północny"
        }

    def get_polish_name(self, body_id: int) -> str | None | Any:
        """
        Metoda pomocnicza zwracająca polską nazwę obiektu.
        Jeśli obiektu nie ma w słowniku, próbuje pobrać oryginalną angielską nazwę z biblioteki.
        """
        return self.polish_names.get(body_id, swe.get_planet_name(body_id))

    def calculate_rise_set(self, date_utc: datetime.datetime, lat: float, lon: float, height:float, body_id: int = swe.SUN):
        """
        Oblicza czas wschodu i zachodu dla danego obiektu, biorąc pod uwagę
        standardową refrakcję atmosferyczną.
        """
        # 1. Konwersja czasu na Julian Day (UTC)
        decimal_hour = date_utc.hour + (date_utc.minute / 60.0) + (date_utc.second / 3600.0)
        jd_utc = swe.julday(date_utc.year, date_utc.month, date_utc.day, decimal_hour)
        geopos = (float(lon), float(lat), height)
        # 2. Wywołanie obliczeń - przekazujemy lon, lat, 0.0 bezpośrednio jako float!
        try:
            # Wschód
            res_rise = swe.rise_trans(jd_utc, body_id, swe.CALC_RISE, geopos, 0.0, 0.0, self.flags)
            # res_rise to krotka: (kod_powrotu, (jd_czasu, ...))
            if res_rise[0] == -2:
                # Obiekt okołobiegunowy (np. cały czas nad horyzontem lub cały czas pod nim)
                jd_rise = None
            elif res_rise[0] < 0:
                # Inny błąd obliczeniowy
                jd_rise = None
            else:
                jd_rise = res_rise[1][0]

            # Zachód
            res_set = swe.rise_trans(jd_utc, body_id, swe.CALC_SET, geopos, 0.0, 0.0, self.flags)
            if res_set[0] == -2:
                jd_set = None
            elif res_set[0] < 0:
                jd_set = None
            else:
                jd_set = res_set[1][0]

            # Górowanie (Tranzyt górny przez południk - MTRANSIT)
            res_transit = swe.rise_trans(jd_utc, body_id, swe.CALC_MTRANSIT, geopos, 0.0, 0.0, self.flags)
            jd_transit = res_transit[1][0]

        except swe.Error as e:
            raise RuntimeError(f"Błąd silnika Astrodienst: {e}")

        # 3. Konwersja wyników na format zrozumiały dla człowieka
        return {
            'wschod': jd_rise,
            'zachod': jd_set,
            "gorowanie_jd": jd_transit
        }


def oblicz_swit_zmierzch(jd_gorowanie, lon, lat, flags, tz_info):
    """
    Wykorzystuje metodę bisekcji do znalezienia momentu,
    gdy Słońce przecina wysokość -18 stopni (świt/zmierzch astronomiczny).
    """
    KACIK_CIEMNOSCI = -18.0
    TOLERANCJA = 1.0 / 1440.0  # Dokładność do 1 minuty w ułamku dnia juliańskiego

    # Określamy przybliżony czas połnocy (pół dnia przed i po górowaniu)
    jd_polnoc_przed = jd_gorowanie - 0.5
    jd_polnoc_po = jd_gorowanie + 0.5

    def wysokosc_slonca(jd):
        # Pobieramy wysokość rzeczywistą z Twojej funkcji (indeks 1)
        return oblicz_wysokosc(jd, swe.SUN, lon, lat, flags)[1]

    # ---- OBLICZANIE ŚWITU ----
    if wysokosc_slonca(jd_polnoc_przed) > KACIK_CIEMNOSCI:
        swit_str = "Białe Noce"  # Słońce w ogóle nie schodzi na -18 stopni (np. latem na północy)
    else:
        a, b = jd_polnoc_przed, jd_gorowanie
        while (b - a) > TOLERANCJA:
            mid = (a + b) / 2.0
            if wysokosc_slonca(mid) < KACIK_CIEMNOSCI:
                a = mid  # Słońce jest niżej, więc przesuwamy się bliżej górowania
            else:
                b = mid  # Słońce wyżej, cofamy się do północy
        swit_str = _jd_to_datetime((a + b) / 2.0).astimezone(tz_info).strftime('%H.%M')

    # ---- OBLICZANIE ZMIERZCHU ----
    if wysokosc_slonca(jd_polnoc_po) > KACIK_CIEMNOSCI:
        zmierzch_str = "Białe Noce"
    else:
        a, b = jd_gorowanie, jd_polnoc_po
        while (b - a) > TOLERANCJA:
            mid = (a + b) / 2.0
            if wysokosc_slonca(mid) > KACIK_CIEMNOSCI:
                a = mid  # Słońce wciąż za wysoko, idziemy w stronę północy
            else:
                b = mid
        zmierzch_str = _jd_to_datetime((a + b) / 2.0).astimezone(tz_info).strftime('%H.%M')

    return swit_str, zmierzch_str

def generuj_raport(pozycja, rok, miesiac, dzien, days):
    engine = EphemerisEngine(ephe_path='eph_data')
    sprawdz_typ_efemeryd('eph_data')

    LONGITUDE, LATITUDE, ELEV = pozycja
    warsaw_tz = ZoneInfo("Europe/Warsaw")

    # 1. Przygotowanie nagłówków dla DWÓCH osobnych tabel
    naglowki_slonce = ["Dzień", "Słońce Wsch", "Słońce Gór", "Słońce Zach", "Księżyc Wsch", "Księżyc Gór",
                       "Księżyc Zach"]

    planety = [swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO]
    naglowki_planety = ["Dzień", "Świt astr.", "Zmierzch astr."]
    for p in planety:
        # Skracamy nagłówki do formatu z Piwnic
        nazwa = engine.get_polish_name(p).capitalize()
        naglowki_planety.append(f"{nazwa} (Wsch-Zach)")

    try:
        start_date_local = datetime.datetime(rok, miesiac, dzien, 0, 0, 0, tzinfo=warsaw_tz)
    except ValueError as e:
        print(f"Błąd daty: {e}")
        return [], [], [], []

    wyniki_slonce = []
    wyniki_planety = []

    for j in range(days):
        current_local = start_date_local + datetime.timedelta(days=j)
        data_str = current_local.strftime('%d.%m.%Y')
        utc_time = current_local.astimezone(datetime.timezone.utc)

        # ==========================================
        # TABELA 1: SŁOŃCE I KSIĘŻYC (Codziennie)
        # ==========================================
        wiersz_s = [data_str]
        for cialo in [swe.SUN, swe.MOON]:
            try:
                wyniki = engine.calculate_rise_set(utc_time, LATITUDE, LONGITUDE, ELEV, cialo)
                # Formatowanie HH.MM zamiast HH:MM:SS !
                wsch = _jd_to_datetime(wyniki['wschod']).astimezone(warsaw_tz).strftime('%H.%M') if wyniki[
                    'wschod'] else "--.--"
                gor = _jd_to_datetime(wyniki['gorowanie_jd']).astimezone(warsaw_tz).strftime('%H.%M') if wyniki[
                    'gorowanie_jd'] else "--.--"
                zach = _jd_to_datetime(wyniki['zachod']).astimezone(warsaw_tz).strftime('%H.%M') if wyniki[
                    'zachod'] else "--.--"

                wiersz_s.extend([wsch, gor, zach])
            except Exception:
                wiersz_s.extend(["Błąd", "Błąd", "Błąd"])

        wyniki_slonce.append(tuple(wiersz_s))

        # ==========================================
        # TABELA 2: ZJAWISKA PLANETARNE
        # ==========================================
        # Żeby policzyć świt, musimy znać czas górowania Słońca danego dnia
        wyniki_s_tmp = engine.calculate_rise_set(utc_time, LATITUDE, LONGITUDE, ELEV, swe.SUN)
        jd_gor = wyniki_s_tmp['gorowanie_jd']

        if jd_gor is not None:
            swit, zmierzch = oblicz_swit_zmierzch(jd_gor, LONGITUDE, LATITUDE, engine.flags, warsaw_tz)
        else:
            swit, zmierzch = "--.--", "--.--"

        wiersz_p = [data_str, swit, zmierzch]

        for p in planety:
            try:
                wyniki = engine.calculate_rise_set(utc_time, LATITUDE, LONGITUDE, ELEV, p)
                wsch = _jd_to_datetime(wyniki['wschod']).astimezone(warsaw_tz).strftime('%H.%M') if wyniki[
                    'wschod'] else "--.--"
                zach = _jd_to_datetime(wyniki['zachod']).astimezone(warsaw_tz).strftime('%H.%M') if wyniki[
                    'zachod'] else "--.--"

                wiersz_p.append(f"{wsch} - {zach}")
            except Exception:
                wiersz_p.append("Błąd")

        wyniki_planety.append(tuple(wiersz_p))

    # Zwracamy dokładnie 4 elementy, których oczekuje main.py
    return wyniki_slonce, naglowki_slonce, wyniki_planety, naglowki_planety




if __name__ == "__main__":
    # 1. Inicjujemy silnik
    engine = EphemerisEngine(ephe_path='eph_data')
    sprawdz_typ_efemeryd('eph_data')
    # 3. Parametry geograficzne (Olsztyn / Warszawa)
    LATITUDE = 90  # N
    LONGITUDE = 20.49272  # E
    planets = {swe.SUN, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.NEPTUNE, swe.URANUS}
    for planet in planets:
        print(f"           {engine.get_polish_name(planet)}")
        print("   DATA      WSCHÓD   GÓROWANIE  ZACHÓD")
        for i in range(1, 32):
            try:
                flaga_wschod = 0
                flaga_zachod = 0
                # 2. Definiujemy datę i czas w naszej strefie czasowej (np. Warszawa)
                warsaw_tz = ZoneInfo("Europe/Warsaw")
                local_time = datetime.datetime(2026, 9, i, 0, 0, 0, tzinfo=warsaw_tz)

                # Zamieniamy na czas uniwersalny (UTC), którym posługuje się silnik
                utc_time = local_time.astimezone(datetime.timezone.utc)

                wyniki = engine.calculate_rise_set(
                    date_utc=utc_time,
                    lat=LATITUDE,
                    lon=LONGITUDE,
                    body_id=planet
                )

                # 5. Wyniki wracają w UTC, przeliczamy z powrotem na strefę polską do wyświetlenia
                try:
                    wschod_lokalny = _jd_to_datetime(wyniki['wschod']).astimezone(warsaw_tz).strftime('%H:%M:%S')
                except:
                    flaga_wschod = 1
                    wschod_lokalny = "**:**:**"

                gorowanie_lokalny = _jd_to_datetime(wyniki['gorowanie_jd']).astimezone(warsaw_tz).strftime('%H:%M:%S')
                try:
                    zachod_lokalny = _jd_to_datetime(wyniki['zachod']).astimezone(warsaw_tz).strftime('%H:%M:%S')
                except:
                    flaga_zachod = 1
                    zachod_lokalny = "**:**:**"
                if flaga_wschod == 1 or flaga_zachod == 1:
                    wysokosc = oblicz_wysokosc(wyniki['gorowanie_jd'], planet, LONGITUDE, LATITUDE, engine.flags)[2]
                    if wysokosc < 0:
                        flaga_gorowanie = '\\/'
                    elif wysokosc > 0:
                        flaga_gorowanie = '/\\'
                    else:
                        flaga_gorowanie = '---'
                    print(
                        f"{local_time.strftime('%Y-%m-%d')}  {wschod_lokalny}  {gorowanie_lokalny}  {zachod_lokalny}  {flaga_gorowanie}")
                else:
                    print(f"{local_time.strftime('%Y-%m-%d')}  {wschod_lokalny}  {gorowanie_lokalny}  {zachod_lokalny}")
            except:
                break
