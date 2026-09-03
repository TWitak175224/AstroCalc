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
    obecny_czas = datetime.datetime.now(datetime.timezone.utc)
    dziesietna_godzina = obecny_czas.hour + (obecny_czas.minute / 60.0) + (obecny_czas.second / 3600.0)
    jd_test = swe.julday(obecny_czas.year, obecny_czas.month, obecny_czas.day, dziesietna_godzina)

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
        pass


def _jd_to_datetime(jd: float) -> datetime.datetime:
    year, month, day, decimal_hour = swe.revjul(jd)
    hours = int(decimal_hour)
    minutes = int((decimal_hour - hours) * 60)
    seconds = int((((decimal_hour - hours) * 60) - minutes) * 60)
    if seconds >= 60: seconds = 59
    return datetime.datetime(year, month, day, hours, minutes, seconds, tzinfo=datetime.timezone.utc)


def oblicz_swit_zmierzch(jd_gorowanie, lon, lat, flags, tz_info):
    KACIK_CIEMNOSCI = -18.0
    TOLERANCJA = 1.0 / 1440.0

    jd_polnoc_przed = jd_gorowanie - 0.5
    jd_polnoc_po = jd_gorowanie + 0.5

    def wysokosc_slonca(jd):
        return oblicz_wysokosc(jd, swe.SUN, lon, lat, flags)[1]

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
        swit_str = _jd_to_datetime((a + b) / 2.0).astimezone(tz_info).strftime('%H:%M')

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
        zmierzch_str = _jd_to_datetime((a + b) / 2.0).astimezone(tz_info).strftime('%H:%M')

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

    def calculate_dso_rise_set(self, date_utc, lat, lon, elev, starname):
        decimal_hour = date_utc.hour + (date_utc.minute / 60.0) + (date_utc.second / 3600.0)
        jd_utc = swe.julday(date_utc.year, date_utc.month, date_utc.day, decimal_hour)
        geopos = (lon, lat, elev)
        wyniki = {'wschod_jd': None, 'gorowanie_jd': None, 'zachod_jd': None}

        nazwa_szukana = f",{starname}"

        try:
            res_rise = swe.rise_trans(jd_utc, swe.FIXSTAR, nazwa_szukana, self.flags,
                                      swe.CALC_RISE | swe.BIT_DISC_CENTER, geopos, 1013.25, 15.0)
            wyniki['wschod_jd'] = res_rise[0][0]
        except Exception:
            pass

        try:
            res_trans = swe.rise_trans(jd_utc, swe.FIXSTAR, nazwa_szukana, self.flags,
                                       swe.CALC_MTRANSIT | swe.BIT_DISC_CENTER, geopos, 1013.25, 15.0)
            wyniki['gorowanie_jd'] = res_trans[0][0]
        except Exception:
            pass

        try:
            res_set = swe.rise_trans(jd_utc, swe.FIXSTAR, nazwa_szukana, self.flags, swe.CALC_SET | swe.BIT_DISC_CENTER,
                                     geopos, 1013.25, 15.0)
            wyniki['zachod_jd'] = res_set[0][0]
        except Exception:
            pass

        return wyniki

    def get_dso_declination(self, date_utc, starname):
        decimal_hour = date_utc.hour + (date_utc.minute / 60.0) + (date_utc.second / 3600.0)
        jd_utc = swe.julday(date_utc.year, date_utc.month, date_utc.day, decimal_hour)
        try:
            res = swe.fixstar_ut(f",{starname}", jd_utc, self.flags | swe.FLG_EQUATORIAL)
            return res[0][1]
        except Exception:
            return None

    def pobierz_odleglosc(self, date_utc: datetime.datetime, body_id: int):
        decimal_hour = date_utc.hour + (date_utc.minute / 60.0) + (date_utc.second / 3600.0)
        jd_utc = swe.julday(date_utc.year, date_utc.month, date_utc.day, decimal_hour)

        coords, _ = swe.calc_ut(jd_utc, body_id, self.flags)
        return coords[2]

    def oblicz_faze_ksiezyca(self, date_utc: datetime.datetime):
        decimal_hour = date_utc.hour + (date_utc.minute / 60.0) + (date_utc.second / 3600.0)
        jd_utc = swe.julday(date_utc.year, date_utc.month, date_utc.day, decimal_hour)

        try:
            wynik = swe.pheno_ut(jd_utc, swe.MOON, self.flags)
            faza_ulamek = wynik[1]
            return faza_ulamek * 100.0
        except swe.Error as e:
            print(f"Błąd silnika przy obliczaniu fazy: {e}")
            return 0.0

    def _doprecyzuj_faze(self, jd_start, jd_end, faza_docelowa):
        best_jd = jd_start
        min_diff = 999.0
        jd = jd_start
        step = 1.0 / 1440.0
        while jd <= jd_end:
            sun, _ = swe.calc_ut(jd, swe.SUN, self.flags)
            moon, _ = swe.calc_ut(jd, swe.MOON, self.flags)
            E = (moon[0] - sun[0]) % 360.0

            diff = abs(E - faza_docelowa)
            if diff > 180: diff = 360.0 - diff

            if diff < min_diff:
                min_diff = diff
                best_jd = jd
            jd += step
        return best_jd

    def _doprecyzuj_ekstremum(self, jd_start, jd_end, body, szukaj_maksa, to_deklinacja):
        best_jd = jd_start
        best_val = -999999999 if szukaj_maksa else 999999999
        jd = jd_start
        step = 1.0 / 1440.0
        calc_flags = self.flags | swe.FLG_EQUATORIAL if to_deklinacja else self.flags

        while jd <= jd_end:
            coords, _ = swe.calc_ut(jd, body, calc_flags)
            val = coords[1] if to_deklinacja else coords[2]
            if body == swe.MOON and not to_deklinacja:
                val *= 149597870.7

            if szukaj_maksa:
                if val > best_val: best_val, best_jd = val, jd
            else:
                if val < best_val: best_val, best_jd = val, jd
            jd += step
        return best_jd, best_val

    def _doprecyzuj_slonce(self, jd_start, jd_end, faza_docelowa):
        best_jd = jd_start
        min_diff = 999.0
        jd = jd_start
        step = 1.0 / 1440.0
        while jd <= jd_end:
            sun, _ = swe.calc_ut(jd, swe.SUN, self.flags)
            lon = sun[0]
            diff = abs(lon - faza_docelowa)
            if diff > 180: diff = 360.0 - diff
            if diff < min_diff:
                min_diff = diff
                best_jd = jd
            jd += step
        return best_jd

    def _doprecyzuj_kat_planetarny(self, jd_start, jd_end, body1, body2, docelowy_kat):
        best_jd = jd_start
        min_diff = 999.0
        jd = jd_start
        step = 1.0 / 1440.0
        while jd <= jd_end:
            pos1, _ = swe.calc_ut(jd, body1, self.flags)
            pos2, _ = swe.calc_ut(jd, body2, self.flags)
            diff = abs((pos1[0] - pos2[0]) % 360.0)

            if docelowy_kat == 0:
                if diff > 180: diff = 360.0 - diff
            else:
                diff = abs(diff - 180.0)

            if diff < min_diff:
                min_diff = diff
                best_jd = jd
            jd += step
        return best_jd

    def _doprecyzuj_elongacje(self, jd_start, jd_end, body):
        best_jd = jd_start
        max_elong = -1.0
        best_kierunek = 0
        jd = jd_start
        step = 1.0 / 1440.0
        while jd <= jd_end:
            pos_p, _ = swe.calc_ut(jd, body, self.flags)
            pos_s, _ = swe.calc_ut(jd, swe.SUN, self.flags)
            diff = (pos_p[0] - pos_s[0]) % 360.0
            elong = diff if diff <= 180 else 360.0 - diff

            if elong > max_elong:
                max_elong = elong
                best_jd = jd
                best_kierunek = diff
            jd += step
        return best_jd, max_elong, best_kierunek

    def znajdz_kalendarium_zjawisk(self, utc_start, dni, pozycja, tz, okienko_koniunkcji=5.0):
        zjawiska_jd = []
        jd_base = swe.julday(utc_start.year, utc_start.month, utc_start.day, utc_start.hour)
        jd_end = jd_base + dni

        LONGITUDE, LATITUDE, ELEV = pozycja
        geopos = (float(LONGITUDE), float(LATITUDE), float(ELEV))

        def formatuj_czas(jd_val):
            if not jd_val or jd_val == 0.0: return "--:--"
            y, m, d, h_float = swe.revjul(jd_val)
            h = int(h_float)
            minute = int((h_float - h) * 60)
            sec = int((((h_float - h) * 60) - minute) * 60)
            if sec >= 60: sec = 59
            dt_utc = datetime.datetime(y, m, d, h, minute, sec, tzinfo=datetime.timezone.utc)
            return dt_utc.astimezone(tz).strftime('%H:%M')

        def przekroczono_0(prv, cur):
            return (prv > 300 and cur < 60) or (prv < 60 and cur > 300)

        def przekroczono_180(prv, cur):
            return (prv < 180 and cur >= 180) or (prv > 180 and cur <= 180)

        # --- 1. GLOBALNE ZAĆMIENIA KSIĘŻYCA ---
        jd_szukaj = jd_base
        while jd_szukaj <= jd_end:
            try:
                res = swe.lun_eclipse_when(jd_szukaj, self.flags, False)
                ret_code, tret = res[0], res[1]
                t_max = tret[0]

                if t_max > jd_end: break

                if ret_code != 0 and t_max >= jd_base:
                    typ = "Zaćmienie Księżyca"
                    if ret_code & swe.ECL_TOTAL:
                        typ = "Całkowite Zaćmienie Księżyca"
                    elif ret_code & swe.ECL_PARTIAL:
                        typ = "Częściowe Zaćmienie Księżyca"
                    elif ret_code & getattr(swe, 'ECL_PENUMBRAL', 64):
                        typ = "Półcieniowe Zaćmienie Księżyca"

                    kontakty = sorted(list(set([t for t in tret[1:] if t > 0.0])))

                    parts = []
                    if len(kontakty) >= 4:
                        parts.append(f"Półcień: {formatuj_czas(kontakty[0])}-{formatuj_czas(kontakty[-1])}")
                        parts.append(f"Cień: {formatuj_czas(kontakty[1])}-{formatuj_czas(kontakty[-2])}")
                    elif len(kontakty) >= 2:
                        parts.append(f"Faza: {formatuj_czas(kontakty[0])}-{formatuj_czas(kontakty[-1])}")
                    else:
                        parts.append(f"Maks: {formatuj_czas(t_max)}")

                    detal = " | ".join(parts)
                    zjawiska_jd.append((t_max, typ, detal))
                jd_szukaj = t_max + 10.0
            except Exception:
                jd_szukaj += 10.0

        # --- 2. SKANOWANIE OKIENKOWE ---
        step = 1.0 / 24.0
        prev_E = None
        prev_sun_lon = None
        hist_D_moon, hist_D_sun, hist_Dec = [], [], []

        planety_zewn = [swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO]
        planety_wewn = [swe.MERCURY, swe.VENUS]
        prev_lon_planet = {}
        hist_elong = {swe.MERCURY: [], swe.VENUS: []}

        # Wzajemne koniunkcje (Księżyc + wszystkie planety)
        wszystkie_ciala = [swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE,
                           swe.PLUTO]
        prev_pair_diff = {}

        jd = jd_base
        while jd <= jd_end:
            sun_pos, _ = swe.calc_ut(jd, swe.SUN, self.flags)
            moon_pos, _ = swe.calc_ut(jd, swe.MOON, self.flags)
            moon_eq, _ = swe.calc_ut(jd, swe.MOON, self.flags | swe.FLG_EQUATORIAL)

            E = (moon_pos[0] - sun_pos[0]) % 360.0
            sun_lon = sun_pos[0]
            D_sun, D_moon, Dec = sun_pos[2], moon_pos[2] * 149597870.7, moon_eq[1]

            if prev_sun_lon is not None:
                if prev_sun_lon > 350 and sun_lon < 10:
                    zjawiska_jd.append(
                        (self._doprecyzuj_slonce(jd - step, jd, 0), "Równonoc Wiosenna", "Początek Wiosny"))
                elif prev_sun_lon < 90 and sun_lon >= 90:
                    zjawiska_jd.append(
                        (self._doprecyzuj_slonce(jd - step, jd, 90), "Przesilenie Letnie", "Początek Lata"))
                elif prev_sun_lon < 180 and sun_lon >= 180:
                    zjawiska_jd.append(
                        (self._doprecyzuj_slonce(jd - step, jd, 180), "Równonoc Jesienna", "Początek Jesieni"))
                elif prev_sun_lon < 270 and sun_lon >= 270:
                    zjawiska_jd.append(
                        (self._doprecyzuj_slonce(jd - step, jd, 270), "Przesilenie Zimowe", "Początek Zimy"))
            prev_sun_lon = sun_lon

            if prev_E is not None:
                if prev_E > 300 and E < 60:
                    t_now = self._doprecyzuj_faze(jd - step, jd, 0)
                    zjawiska_jd.append((t_now, "Nów Księżyca", ""))

                    t_scan = t_now - 0.125
                    t_end_scan = t_now + 0.125
                    step_scan = 1.0 / 1440.0

                    widoczne_momenty = []
                    max_faza = 0.0
                    best_t = t_now
                    is_total = False
                    is_annular = False

                    while t_scan <= t_end_scan:
                        try:
                            try:
                                res_how = swe.sol_eclipse_how(t_scan, self.flags, geopos)
                            except TypeError:
                                res_how = swe.sol_eclipse_how(t_scan, geopos, self.flags)

                            ret_how, attr_how = res_how[0], res_how[1]
                            faza = attr_how[2] * 100

                            if faza > 0.1:
                                _, true_alt, _ = oblicz_wysokosc(t_scan, swe.SUN, geopos[0], geopos[1], self.flags)

                                if true_alt > -0.8333:
                                    widoczne_momenty.append(t_scan)
                                    if faza > max_faza:
                                        max_faza = faza
                                        best_t = t_scan
                                        if ret_how & swe.ECL_TOTAL: is_total = True
                                        if ret_how & swe.ECL_ANNULAR: is_annular = True
                        except Exception:
                            pass
                        t_scan += step_scan

                    if widoczne_momenty:
                        typ = "Częściowe Zaćmienie Słońca"
                        if is_total:
                            typ = "Całkowite Zaćmienie Słońca"
                        elif is_annular:
                            typ = "Obrączkowe Zaćmienie Słońca"

                        t_start = widoczne_momenty[0]
                        t_end = widoczne_momenty[-1]

                        try:
                            try:
                                r_end = swe.sol_eclipse_how(t_end, self.flags, geopos)
                            except TypeError:
                                r_end = swe.sol_eclipse_how(t_end, geopos, self.flags)
                            faza_koniec = r_end[1][2] * 100
                        except:
                            faza_koniec = 0.0

                        pocz_str = formatuj_czas(t_start)

                        if faza_koniec > 1.0:
                            kon_str = "--:--"
                        else:
                            kon_str = formatuj_czas(t_end)

                        detal = f"Maks: {max_faza:.1f}% | Pocz: {pocz_str} | Kon: {kon_str}"
                        zjawiska_jd.append((best_t, typ, detal))

                elif prev_E < 90 and E >= 90:
                    zjawiska_jd.append((self._doprecyzuj_faze(jd - step, jd, 90), "Pierwsza Kwadra", ""))
                elif prev_E < 180 and E >= 180:
                    zjawiska_jd.append((self._doprecyzuj_faze(jd - step, jd, 180), "Pełnia Księżyca", ""))
                elif prev_E < 270 and E >= 270:
                    zjawiska_jd.append((self._doprecyzuj_faze(jd - step, jd, 270), "Trzecia Kwadra", ""))

            hist_D_moon.append((jd, D_moon))
            hist_D_sun.append((jd, D_sun))
            hist_Dec.append((jd, Dec))
            if len(hist_D_moon) == 3:
                if hist_D_moon[1][1] < hist_D_moon[0][1] and hist_D_moon[1][1] < hist_D_moon[2][1]:
                    t, v = self._doprecyzuj_ekstremum(hist_D_moon[0][0], hist_D_moon[2][0], swe.MOON, False, False)
                    zjawiska_jd.append((t, "Perygeum Księżyca", f"Odl: {v:,.0f} km".replace(',', ' ')))
                elif hist_D_moon[1][1] > hist_D_moon[0][1] and hist_D_moon[1][1] > hist_D_moon[2][1]:
                    t, v = self._doprecyzuj_ekstremum(hist_D_moon[0][0], hist_D_moon[2][0], swe.MOON, True, False)
                    zjawiska_jd.append((t, "Apogeum Księżyca", f"Odl: {v:,.0f} km".replace(',', ' ')))

                if hist_D_sun[1][1] < hist_D_sun[0][1] and hist_D_sun[1][1] < hist_D_sun[2][1]:
                    t, v = self._doprecyzuj_ekstremum(hist_D_sun[0][0], hist_D_sun[2][0], swe.SUN, False, False)
                    zjawiska_jd.append((t, "Ziemia w peryhelium", f"Odl: {v:.4f} AU"))
                elif hist_D_sun[1][1] > hist_D_sun[0][1] and hist_D_sun[1][1] > hist_D_sun[2][1]:
                    t, v = self._doprecyzuj_ekstremum(hist_D_sun[0][0], hist_D_sun[2][0], swe.SUN, True, False)
                    zjawiska_jd.append((t, "Ziemia w aphelium", f"Odl: {v:.4f} AU"))

                if hist_Dec[1][1] < hist_Dec[0][1] and hist_Dec[1][1] < hist_Dec[2][1]:
                    t, v = self._doprecyzuj_ekstremum(hist_Dec[0][0], hist_Dec[2][0], swe.MOON, False, True)
                    zjawiska_jd.append((t, "Maks. deklinacja południowa Księżyca", f"Kąt: {v:.2f}°"))
                elif hist_Dec[1][1] > hist_Dec[0][1] and hist_Dec[1][1] > hist_Dec[2][1]:
                    t, v = self._doprecyzuj_ekstremum(hist_Dec[0][0], hist_Dec[2][0], swe.MOON, True, True)
                    zjawiska_jd.append((t, "Maks. deklinacja północna Księżyca", f"Kąt: {v:.2f}°"))

                hist_D_moon.pop(0)
                hist_D_sun.pop(0)
                hist_Dec.pop(0)

            # --- ZJAWISKA PLANETARNE ZE SŁOŃCEM ---
            for p in planety_zewn + planety_wewn:
                pos_p, _ = swe.calc_ut(jd, p, self.flags)
                diff_lon = (pos_p[0] - sun_lon) % 360.0

                if p in prev_lon_planet:
                    prev = prev_lon_planet[p]
                    nazwa_p = self.get_polish_name(p).capitalize()

                    if przekroczono_0(prev, diff_lon):
                        t_dok = self._doprecyzuj_kat_planetarny(jd - step, jd, p, swe.SUN, 0)

                        if p in planety_wewn:
                            pos_p_dok, _ = swe.calc_ut(t_dok, p, self.flags)
                            pos_s_dok, _ = swe.calc_ut(t_dok, swe.SUN, self.flags)
                            # Jeśli planeta jest bliżej Ziemi niż Słońce -> Koniunkcja dolna
                            if pos_p_dok[2] < pos_s_dok[2]:
                                zjawiska_jd.append((t_dok, f"Koniunkcja dolna: {nazwa_p}", "ze Słońcem"))
                            else:
                                zjawiska_jd.append((t_dok, f"Koniunkcja górna: {nazwa_p}", "ze Słońcem"))
                        else:
                            zjawiska_jd.append((t_dok, f"Koniunkcja: {nazwa_p}", "ze Słońcem"))

                    if p in planety_zewn and przekroczono_180(prev, diff_lon):
                        t_dok = self._doprecyzuj_kat_planetarny(jd - step, jd, p, swe.SUN, 180)
                        zjawiska_jd.append((t_dok, f"Opozycja: {nazwa_p}", ""))

                prev_lon_planet[p] = diff_lon

            # --- MAKSYMALNE ELONGACJE ---
            for p in planety_wewn:
                elong = diff_lon if prev_lon_planet[p] <= 180 else 360.0 - prev_lon_planet[p]
                hist_elong[p].append((jd, elong))

                if len(hist_elong[p]) == 3:
                    e0, e1, e2 = hist_elong[p][0], hist_elong[p][1], hist_elong[p][2]
                    if e1[1] > e0[1] and e1[1] > e2[1]:
                        t_dok, max_val, typ_w_z = self._doprecyzuj_elongacje(e0[0], e2[0], p)
                        nazwa_p = self.get_polish_name(p).capitalize()
                        kierunek = "Wschodnia (wieczorna)" if typ_w_z < 180 else "Zachodnia (poranna)"
                        zjawiska_jd.append((t_dok, f"Maks. elongacja: {nazwa_p}", f"Kąt: {max_val:.1f}° | {kierunek}"))
                    hist_elong[p].pop(0)

            # --- KONIUNKCJE WZAJEMNE (Planeta-Planeta i Księżyc-Planeta) ---
            for i in range(len(wszystkie_ciala)):
                for j in range(i + 1, len(wszystkie_ciala)):
                    b1, b2 = wszystkie_ciala[i], wszystkie_ciala[j]
                    para = (b1, b2)

                    pos1, _ = swe.calc_ut(jd, b1, self.flags)
                    pos2, _ = swe.calc_ut(jd, b2, self.flags)
                    diff_para = (pos1[0] - pos2[0]) % 360.0

                    if para in prev_pair_diff:
                        prev = prev_pair_diff[para]
                        if przekroczono_0(prev, diff_para):
                            t_dok = self._doprecyzuj_kat_planetarny(jd - step, jd, b1, b2, 0)
                            p1_dok, _ = swe.calc_ut(t_dok, b1, self.flags)
                            p2_dok, _ = swe.calc_ut(t_dok, b2, self.flags)

                            # Separacja kątowa na niebie to po prostu różnica szerokości ekliptycznej w momencie koniunkcji
                            sep = abs(p1_dok[1] - p2_dok[1])

                            # FILTR OKIENKA UŻYTKOWNIKA
                            if sep <= okienko_koniunkcji:
                                n1 = self.get_polish_name(b1).capitalize()
                                n2 = self.get_polish_name(b2).capitalize()
                                zjawiska_jd.append((t_dok, f"Zbliżenie: {n1} i {n2}", f"Separacja: {sep:.2f}°"))

                    prev_pair_diff[para] = diff_para

            prev_E = E
            jd += step

        return zjawiska_jd


def odkoduj_zjawisko(wyniki, cialo, lon, lat, flags, strefa_tz, jd_bazowe):
    wsch_jd = wyniki['wschod']
    gor_jd = wyniki['gorowanie_jd']
    zach_jd = wyniki['zachod']

    gor_str = _jd_to_datetime(gor_jd).astimezone(strefa_tz).strftime('%H:%M') if gor_jd else "--:--"
    wsch_str = _jd_to_datetime(wsch_jd).astimezone(strefa_tz).strftime('%H:%M') if wsch_jd else None
    zach_str = _jd_to_datetime(zach_jd).astimezone(strefa_tz).strftime('%H:%M') if zach_jd else None

    if wsch_str is None or zach_str is None:
        jd_test = gor_jd if gor_jd else jd_bazowe
        _, _, alt = oblicz_wysokosc(jd_test, cialo, lon, lat, flags)
        znacznik = "/\\" if alt > 0 else "\\/"

        wsch_str = wsch_str if wsch_str else znacznik
        zach_str = zach_str if zach_str else znacznik

    return wsch_str, gor_str, zach_str


def generuj_raport(pozycja, rok, miesiac, dzien, days, strefa_str, krok_planety, obiekty_dso, okienko_koniunkcji=5.0):
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
        return [], [], [], [], [], []

    wyniki_slonce = []
    wyniki_planety = []
    wyniki_dso = []
    naglowki_dso = ["Dzień"]
    for dso in obiekty_dso:
        naglowki_dso.append(f"{dso} (W-G-Z)")

    for j in range(days):
        current_local = start_date_local + datetime.timedelta(days=j)
        data_str = current_local.strftime('%d.%m.%Y')
        utc_time = current_local.astimezone(datetime.timezone.utc)
        jd_midnight = swe.julday(utc_time.year, utc_time.month, utc_time.day, 12.0)

        wiersz_s = [data_str]
        jd_gor_ksiezyca = None

        for cialo in [swe.SUN, swe.MOON]:
            try:
                wyniki = engine.calculate_rise_set(utc_time, LATITUDE, LONGITUDE, ELEV, cialo)
                w, g, z = odkoduj_zjawisko(wyniki, cialo, LONGITUDE, LATITUDE, engine.flags, lokalna_strefa_tz,
                                           jd_midnight)
                wiersz_s.extend([w, g, z])

                odl_au = engine.pobierz_odleglosc(utc_time, cialo)
                if cialo == swe.SUN:
                    wiersz_s.append(f"{odl_au:.4f}")
                else:
                    odl_km = odl_au * 149597870.7
                    wiersz_s.append(f"{odl_km:,.0f}".replace(',', ' '))
                    jd_gor_ksiezyca = wyniki['gorowanie_jd']
            except Exception:
                wiersz_s.extend(["Błąd", "Błąd", "Błąd", "Błąd"])

        if jd_gor_ksiezyca is not None:
            czas_do_fazy = _jd_to_datetime(jd_gor_ksiezyca)
        else:
            czas_do_fazy = utc_time

        faza_proc = engine.oblicz_faze_ksiezyca(czas_do_fazy)
        wiersz_s.append(f"{faza_proc:.1f} %")

        wyniki_slonce.append(tuple(wiersz_s))

        if j % krok_planety == 0:
            wyniki_s_tmp = engine.calculate_rise_set(utc_time, LATITUDE, LONGITUDE, ELEV, swe.SUN)
            jd_gor = wyniki_s_tmp['gorowanie_jd']

            if jd_gor is not None:
                swit, zmierzch = oblicz_swit_zmierzch(jd_gor, LONGITUDE, LATITUDE, engine.flags, lokalna_strefa_tz)
            else:
                swit, zmierzch = "--:--", "--:--"

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

            if obiekty_dso:
                wiersz_dso = [data_str]
                for dso in obiekty_dso:
                    try:
                        wyn = engine.calculate_dso_rise_set(utc_time, LATITUDE, LONGITUDE, ELEV, dso)

                        def format_time(jd):
                            if jd is None: return None
                            dt = _jd_to_datetime(jd).astimezone(lokalna_strefa_tz)
                            return dt.strftime('%H:%M')

                        w = format_time(wyn['wschod_jd'])
                        g = format_time(wyn['gorowanie_jd'])
                        z = format_time(wyn['zachod_jd'])

                        if not w and not z:
                            dec = engine.get_dso_declination(utc_time, dso)
                            if dec is not None:
                                if (LATITUDE >= 0 and dec > 90 - LATITUDE) or (LATITUDE < 0 and dec < -90 - LATITUDE):
                                    w = z = "/\\"
                                else:
                                    w = z = "\\/"
                            else:
                                w = z = "--:--"
                        else:
                            w = w if w else "--:--"
                            z = z if z else "--:--"

                        g = g if g else "--:--"

                        wiersz_dso.append(f"{w}  {g}  {z}")
                    except Exception:
                        wiersz_dso.append("Błąd")
                wyniki_dso.append(tuple(wiersz_dso))

    naglowki_kalendarium = ["Data i Czas", "Zjawisko Astronomiczne", "Dodatkowe Parametry"]
    wyniki_kalendarium = []

    utc_start_date = start_date_local.astimezone(datetime.timezone.utc)

    surowe_zjawiska = engine.znajdz_kalendarium_zjawisk(utc_start_date, days, pozycja, lokalna_strefa_tz,
                                                        okienko_koniunkcji)

    for jd, nazwa, detal in sorted(surowe_zjawiska, key=lambda x: x[0]):
        dt_local = _jd_to_datetime(jd).astimezone(lokalna_strefa_tz)
        czas_str = dt_local.strftime('%Y-%m-%d %H:%M')
        wyniki_kalendarium.append((czas_str, nazwa, detal))

    return wyniki_slonce, naglowki_slonce, wyniki_planety, naglowki_planety, wyniki_kalendarium, naglowki_kalendarium, wyniki_dso, naglowki_dso