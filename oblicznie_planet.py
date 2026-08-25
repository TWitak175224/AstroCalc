import datetime
import os
from zoneinfo import ZoneInfo

import swisseph as swe


def oblicz_wysokosc(jd_utc, body_id, lon, lat, flags):
    flagi_rownikowe = flags | swe.FLG_EQUATORIAL
    coords, ret_flag = swe.calc_ut(jd_utc, body_id, flagi_rownikowe)
    geopos = (float(lon), float(lat), 0.0)
    pozycja_rownikowa = (coords[0], coords[1], coords[2])

    cisnienie = 1013.25
    temperatura = 15.0

    wynik_horyzontalny = swe.azalt(
        jd_utc,
        swe.EQU2HOR,
        geopos,
        cisnienie,
        temperatura,
        pozycja_rownikowa
    )

    azymut = wynik_horyzontalny[0]
    wysokosc_rzeczywista = wynik_horyzontalny[1]
    wysokosc_pozorna = wynik_horyzontalny[2]

    return azymut, wysokosc_rzeczywista, wysokosc_pozorna


def sprawdz_typ_efemeryd(ephe_path=None):
    jd_test = swe.julday(2026, 1, 1)
    wymagana_flaga = swe.FLG_SWIEPH
    try:
        wynik, zwrocona_flaga = swe.calc_ut(jd_test, swe.SUN, wymagana_flaga)
        print("\n--- RAPORT DIAGNOSTYCZNY SILNIKA ---")
        if zwrocona_flaga & swe.FLG_SWIEPH:
            print("[OK] Silnik korzysta z precyzyjnych plików Swiss Ephemeris (*.se1).")
        elif zwrocona_flaga & swe.FLG_MOSEPH:
            print("[OSTRZEŻENIE] Brak plików *.se1! Silnik używa wbudowanego algorytmu Moshiera.")
        elif zwrocona_flaga & swe.FLG_JPLEPH:
            print("[OK] Silnik korzysta z bardzo precyzyjnych efemeryd JPL NASA.")
    except Exception as e:
        print(f"[BŁĄD KRYTYCZNY] Awaria silnika podczas testu: {e}")
    finally:
        pass  # Nie zwalniamy pamięci, bo silnik zaraz rusza do pracy


def _jd_to_datetime(jd: float) -> datetime.datetime:
    year, month, day, decimal_hour = swe.revjul(jd)
    hours = int(decimal_hour)
    minutes = int((decimal_hour - hours) * 60)
    seconds = int((((decimal_hour - hours) * 60) - minutes) * 60)
    return datetime.datetime(year, month, day, hours, minutes, seconds, tzinfo=datetime.timezone.utc)


def oblicz_swit_zmierzch(jd_gorowanie, lon, lat, flags, tz_info):
    """
    Znajduje świt i zmierzch astronomiczny metodą bisekcji (Słońce -18 stopni).
    """
    KACIK_CIEMNOSCI = -18.0
    TOLERANCJA = 1.0 / 1440.0

    jd_polnoc_przed = jd_gorowanie - 0.5
    jd_polnoc_po = jd_gorowanie + 0.5

    def wysokosc_slonca(jd):
        return oblicz_wysokosc(jd, swe.SUN, lon, lat, flags)[1]

    # Świt
    if wysokosc_slonca(jd_polnoc_przed) > KACIK_CIEMNOSCI:
        swit_str = "Białe Noce"
    else:
        a, b = jd_polnoc_przed, jd_gorowanie
        while (b - a) > TOLERANCJA:
            mid = (a + b) / 2.0
            if wysokosc_slonca(mid) < KACIK_CIEMNOSCI:
                a = mid
            else:
                b = mid
        swit_str = _jd_to_datetime((a + b) / 2.0).astimezone(tz_info).strftime('%H.%M')

    # Zmierzch
    if wysokosc_slonca(jd_polnoc_po) > KACIK_CIEMNOSCI:
        zmierzch_str = "Białe Noce"
    else:
        a, b = jd_gorowanie, jd_polnoc_po
        while (b - a) > TOLERANCJA:
            mid = (a + b) / 2.0
            if wysokosc_slonca(mid) > KACIK_CIEMNOSCI:
                a = mid
            else:
                b = mid
        zmierzch_str = _jd_to_datetime((a + b) / 2.0).astimezone(tz_info).strftime('%H.%M')

    return swit_str, zmierzch_str


class EphemerisEngine:
    def __init__(self, ephe_path: str):
        if not os.path.isdir(ephe_path):
            raise FileNotFoundError(f"Nie znaleziono katalogu {ephe_path}")
        swe.set_ephe_path(ephe_path)
        self.ephe_path = ephe_path
        self.flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        self.polish_names = {
            swe.SUN: "SŁOŃCE", swe.MOON: "KSIĘŻYC", swe.MERCURY: "MERKURY",
            swe.VENUS: "WENUS", swe.MARS: "MARS", swe.JUPITER: "JOWISZ",
            swe.SATURN: "SATURN", swe.URANUS: "URAN", swe.NEPTUNE: "NEPTUN",
            swe.PLUTO: "PLUTON"
        }

    def get_polish_name(self, body_id: int) -> str:
        return self.polish_names.get(body_id, swe.get_planet_name(body_id))

    def calculate_rise_set(self, date_utc: datetime.datetime, lat: float, lon: float, height: float,
                           body_id: int = swe.SUN):
        decimal_hour = date_utc.hour + (date_utc.minute / 60.0) + (date_utc.second / 3600.0)
        jd_utc = swe.julday(date_utc.year, date_utc.month, date_utc.day, decimal_hour)
        geopos = (float(lon), float(lat), height)
        try:
            res_rise = swe.rise_trans(jd_utc, body_id, swe.CALC_RISE, geopos, 0.0, 0.0, self.flags)
            jd_rise = res_rise[1][0] if res_rise[0] >= 0 else None

            res_set = swe.rise_trans(jd_utc, body_id, swe.CALC_SET, geopos, 0.0, 0.0, self.flags)
            jd_set = res_set[1][0] if res_set[0] >= 0 else None

            res_transit = swe.rise_trans(jd_utc, body_id, swe.CALC_MTRANSIT, geopos, 0.0, 0.0, self.flags)
            jd_transit = res_transit[1][0] if res_transit[0] >= 0 else None
        except swe.Error as e:
            raise RuntimeError(f"Błąd silnika Astrodienst: {e}")

        return {'wschod': jd_rise, 'zachod': jd_set, "gorowanie_jd": jd_transit}

    def pobierz_odleglosc(self, date_utc: datetime.datetime, body_id: int):
        """Pobiera odległość ciała od Ziemi w Jednostkach Astronomicznych (AU)."""
        decimal_hour = date_utc.hour + (date_utc.minute / 60.0) + (date_utc.second / 3600.0)
        jd_utc = swe.julday(date_utc.year, date_utc.month, date_utc.day, decimal_hour)

        # Funkcja calc_ut zwraca krotkę, gdzie indeks 2 to zawsze odległość w AU
        coords, _ = swe.calc_ut(jd_utc, body_id, self.flags)
        return coords[2]

    def oblicz_faze_ksiezyca(self, date_utc: datetime.datetime):
        """
        Zwraca procentowe oświetlenie tarczy Księżyca (0.0 - 100.0).
        """
        decimal_hour = date_utc.hour + (date_utc.minute / 60.0) + (date_utc.second / 3600.0)
        jd_utc = swe.julday(date_utc.year, date_utc.month, date_utc.day, decimal_hour)

        try:
            # pheno_ut zwraca krotkę z dokładnie 20 wartościami
            wynik = swe.pheno_ut(jd_utc, swe.MOON, self.flags)

            faza_ulamek = wynik[1]  # Indeks 1 to ułamek oświetlonej tarczy (0.0 do 1.0)
            return faza_ulamek * 100.0
        except swe.Error as e:
            print(f"Błąd silnika przy obliczaniu fazy: {e}")
            return 0.0


def odkoduj_zjawisko(wyniki, cialo, lon, lat, flags, strefa_tz, jd_bazowe):
    """
    Formatuje czasy wschodu, górowania i zachodu.
    Wykrywa obiekty okołobiegunowe i nadaje znaczniki /\\ lub \\/.
    """
    wsch_jd = wyniki['wschod']
    gor_jd = wyniki['gorowanie_jd']
    zach_jd = wyniki['zachod']

    gor_str = _jd_to_datetime(gor_jd).astimezone(strefa_tz).strftime('%H.%M') if gor_jd else "--.--"
    wsch_str = _jd_to_datetime(wsch_jd).astimezone(strefa_tz).strftime('%H.%M') if wsch_jd else None
    zach_str = _jd_to_datetime(zach_jd).astimezone(strefa_tz).strftime('%H.%M') if zach_jd else None

    # Detekcja braku wschodu lub zachodu
    if wsch_str is None or zach_str is None:
        jd_test = gor_jd if gor_jd else jd_bazowe
        _, _, alt = oblicz_wysokosc(jd_test, cialo, lon, lat, flags)
        znacznik = "/\\" if alt > 0 else "\\/"

        wsch_str = wsch_str if wsch_str else znacznik
        zach_str = zach_str if zach_str else znacznik

    return wsch_str, gor_str, zach_str


def generuj_raport(pozycja, rok, miesiac, dzien, days, strefa_str, krok_planety):
    engine = EphemerisEngine(ephe_path='eph_data')
    sprawdz_typ_efemeryd('eph_data')

    LONGITUDE, LATITUDE, ELEV = pozycja
    lokalna_strefa_tz = ZoneInfo(strefa_str)


    naglowki_slonce = ["Dzień", "Słońce Wsch.", "Słońce Gór.", "Słońce Zach.", "Odl. Słońca [AU]", "Księżyc Wsch.",
                       "Księżyc Gór.", "Księżyc Zach.", "Odl. Księżyca [km]", "Faza [%]"]

    planety = [swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO]
    naglowki_planety = ["Dzień", "Świt astr.", "Zmierzch astr."]
    for p in planety:
        nazwa = engine.get_polish_name(p).capitalize()
        naglowki_planety.append(f"{nazwa} W-G-Z")

    try:
        start_date_local = datetime.datetime(rok, miesiac, dzien, 0, 0, 0, tzinfo=lokalna_strefa_tz)
    except ValueError as e:
        print(f"Błąd daty: {e}")
        return [], [], [], []

    wyniki_slonce = []
    wyniki_planety = []

    for j in range(days):
        current_local = start_date_local + datetime.timedelta(days=j)
        data_str = current_local.strftime('%d.%m.%Y')
        utc_time = current_local.astimezone(datetime.timezone.utc)
        jd_midnight = swe.julday(utc_time.year, utc_time.month, utc_time.day, 12.0)

        # TABELA 1: Słońce i Księżyc
        wiersz_s = [data_str]
        jd_gor_ksiezyca = None

        for cialo in [swe.SUN, swe.MOON]:
            try:
                wyniki = engine.calculate_rise_set(utc_time, LATITUDE, LONGITUDE, ELEV, cialo)
                w, g, z = odkoduj_zjawisko(wyniki, cialo, LONGITUDE, LATITUDE, engine.flags, lokalna_strefa_tz,
                                           jd_midnight)
                wiersz_s.extend([w, g, z])

                # --- NOWE: Doklejanie odległości ---
                odl_au = engine.pobierz_odleglosc(utc_time, cialo)
                if cialo == swe.SUN:
                    wiersz_s.append(f"{odl_au:.4f}")  # Słońce zostawiamy w AU
                else:
                    odl_km = odl_au * 149597870.7  # Przelicznik AU na km
                    wiersz_s.append(f"{odl_km:,.0f}".replace(',', ' '))  # Formatowanie Księżyca (np. 384 400)

                    jd_gor_ksiezyca = wyniki['gorowanie_jd']
            except Exception:
                wiersz_s.extend(["Błąd", "Błąd", "Błąd", "Błąd"])
        # --- OBLICZANIE FAZY DLA MOMENTU GÓROWANIA ---
        if jd_gor_ksiezyca is not None:
            # Jeśli Księżyc góruje, konwertujemy JD na obiekt datetime
            czas_do_fazy = _jd_to_datetime(jd_gor_ksiezyca)
        else:
            # Awaryjnie (dzień bez górowania) używamy północy czasu lokalnego
            czas_do_fazy = utc_time

        faza_proc = engine.oblicz_faze_ksiezyca(czas_do_fazy)
        wiersz_s.append(f"{faza_proc:.1f} %")

        wyniki_slonce.append(tuple(wiersz_s))

        # TABELA 2: Planety i Świt/Zmierzch
        # Znak '%' sprawdza, czy dany dzień dzieli się bez reszty przez nasz krok
        if j % krok_planety == 0:
            wyniki_s_tmp = engine.calculate_rise_set(utc_time, LATITUDE, LONGITUDE, ELEV, swe.SUN)
            jd_gor = wyniki_s_tmp['gorowanie_jd']

            if jd_gor is not None:
                swit, zmierzch = oblicz_swit_zmierzch(jd_gor, LONGITUDE, LATITUDE, engine.flags, lokalna_strefa_tz)
            else:
                swit, zmierzch = "--.--", "--.--"

            wiersz_p = [data_str, swit, zmierzch]

            for p in planety:
                try:
                    wyniki = engine.calculate_rise_set(utc_time, LATITUDE, LONGITUDE, ELEV, p)
                    w, g, z = odkoduj_zjawisko(wyniki, p, LONGITUDE, LATITUDE, engine.flags, lokalna_strefa_tz,
                                               jd_midnight)
                    wiersz_p.append(f"{w}  {g}  {z}")
                except Exception:
                    wiersz_p.append("Błąd")

            wyniki_planety.append(tuple(wiersz_p))

    return wyniki_slonce, naglowki_slonce, wyniki_planety, naglowki_planety
