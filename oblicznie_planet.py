import datetime
import os
import math
from zoneinfo import ZoneInfo

import swisseph as swe


def oblicz_wysokosc(jd_utc, body_id, lon, lat, flags):
    # Wymuszamy tryb topocentryczny dla dokładnych zakryć
    swe.set_topo(float(lon), float(lat), 0.0)
    flagi_rownikowe = flags | swe.FLG_EQUATORIAL | swe.FLG_TOPOCTR

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


def _jd_to_datetime(jd: float) -> datetime.datetime:
    year, month, day, decimal_hour = swe.revjul(jd)
    hours = int(decimal_hour)
    minutes = int((decimal_hour - hours) * 60)
    seconds = int((((decimal_hour - hours) * 60) - minutes) * 60)
    if seconds >= 60: seconds = 59
    return datetime.datetime(year, month, day, hours, minutes, seconds, tzinfo=datetime.timezone.utc)


def oblicz_swit_zmierzch(jd_gorowanie, lon, lat, flags, tz_info):
    kat_nocy_astr = -18.0
    tolerancja = 1.0 / 1440.0

    jd_polnoc_przed = jd_gorowanie - 0.5
    jd_polnoc_po = jd_gorowanie + 0.5

    def wysokosc_slonca(jd):
        return oblicz_wysokosc(jd, swe.SUN, lon, lat, flags)[1]

    if wysokosc_slonca(jd_polnoc_przed) > kat_nocy_astr:
        swit_str = "Białe Noce"
    else:
        a, b = jd_polnoc_przed, jd_gorowanie
        while (b - a) > tolerancja:
            mid = (a + b) / 2.0
            if wysokosc_slonca(mid) < kat_nocy_astr:
                a = mid
            else:
                b = mid
        swit_str = _jd_to_datetime((a + b) / 2.0).astimezone(tz_info).strftime('%H:%M')

    if wysokosc_slonca(jd_polnoc_po) > kat_nocy_astr:
        zmierzch_str = "Białe Noce"
    else:
        a, b = jd_gorowanie, jd_polnoc_po
        while (b - a) > tolerancja:
            mid = (a + b) / 2.0
            if wysokosc_slonca(mid) > kat_nocy_astr:
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
            swe.SATURN: "SATURN", swe.URANUS: "URAN", swe.NEPTUNE: "NEPTUN"
        }

    def get_polish_name(self, body_id: int) -> str | None:
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
        geopos = (float(lon), float(lat), float(elev))
        wyniki = {'wschod_jd': None, 'gorowanie_jd': None, 'zachod_jd': None}

        nazwa_szukana = f",{starname}"

        flagi_dso = self.flags | swe.BIT_DISC_CENTER
        try:
            res_rise = swe.rise_trans(jd_utc, nazwa_szukana, swe.CALC_RISE, geopos, 1013.25, 15.0, flagi_dso)
            if res_rise[0] >= 0:
                wyniki['wschod_jd'] = res_rise[1][0]
        except Exception:
            pass

        try:
            res_trans = swe.rise_trans(jd_utc, nazwa_szukana, swe.CALC_MTRANSIT, geopos, 1013.25, 15.0, flagi_dso)
            if res_trans[0] >= 0:
                wyniki['gorowanie_jd'] = res_trans[1][0]
        except Exception:
            pass

        try:
            res_set = swe.rise_trans(jd_utc, nazwa_szukana, swe.CALC_SET, geopos, 1013.25, 15.0, flagi_dso)
            if res_set[0] >= 0:
                wyniki['zachod_jd'] = res_set[1][0]
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
            return wynik[1] * 100.0
        except swe.Error as e:
            print(f"Błąd silnika przy obliczaniu fazy: {e}")
            return 0.0

    def _doprecyzuj_faze(self, jd_start, jd_end, faza_docelowa):
        best_jd, min_diff = jd_start, 999.0
        jd, step = jd_start, 1.0 / 1440.0
        while jd <= jd_end:
            sun, _ = swe.calc_ut(jd, swe.SUN, self.flags)
            moon, _ = swe.calc_ut(jd, swe.MOON, self.flags)
            E = (moon[0] - sun[0]) % 360.0
            diff = abs(E - faza_docelowa)
            if diff > 180: diff = 360.0 - diff
            if diff < min_diff: min_diff, best_jd = diff, jd
            jd += step
        return best_jd

    def _doprecyzuj_ekstremum(self, jd_start, jd_end, body, szukaj_maksa, to_deklinacja):
        best_jd = jd_start
        best_val = -999999999 if szukaj_maksa else 999999999
        jd, step = jd_start, 1.0 / 1440.0
        calc_flags = self.flags | swe.FLG_EQUATORIAL if to_deklinacja else self.flags
        while jd <= jd_end:
            coords, _ = swe.calc_ut(jd, body, calc_flags)
            val = coords[1] if to_deklinacja else coords[2]
            if body == swe.MOON and not to_deklinacja: val *= 149597870.7
            if szukaj_maksa and val > best_val:
                best_val, best_jd = val, jd
            elif not szukaj_maksa and val < best_val:
                best_val, best_jd = val, jd
            jd += step
        return best_jd, best_val

    def _doprecyzuj_slonce(self, jd_start, jd_end, faza_docelowa):
        best_jd, min_diff = jd_start, 999.0
        jd, step = jd_start, 1.0 / 1440.0
        while jd <= jd_end:
            sun, _ = swe.calc_ut(jd, swe.SUN, self.flags)
            diff = abs(sun[0] - faza_docelowa)
            if diff > 180: diff = 360.0 - diff
            if diff < min_diff: min_diff, best_jd = diff, jd
            jd += step
        return best_jd

    def _doprecyzuj_kat_planetarny(self, jd_start, jd_end, body1, body2, docelowy_kat):
        best_jd, min_diff = jd_start, 999.0
        jd, step = jd_start, 1.0 / 1440.0
        while jd <= jd_end:
            pos1, _ = swe.calc_ut(jd, body1, self.flags)
            pos2, _ = swe.calc_ut(jd, body2, self.flags)
            diff = abs((pos1[0] - pos2[0]) % 360.0)
            if docelowy_kat == 0:
                if diff > 180: diff = 360.0 - diff
            else:
                diff = abs(diff - 180.0)
            if diff < min_diff: min_diff, best_jd = diff, jd
            jd += step
        return best_jd

    def _doprecyzuj_elongacje(self, jd_start, jd_end, body):
        best_jd, max_elong, best_kierunek = jd_start, -1.0, 0
        jd, step = jd_start, 1.0 / 1440.0
        while jd <= jd_end:
            pos_p, _ = swe.calc_ut(jd, body, self.flags)
            pos_s, _ = swe.calc_ut(jd, swe.SUN, self.flags)
            diff = (pos_p[0] - pos_s[0]) % 360.0
            elong = diff if diff <= 180 else 360.0 - diff
            if elong > max_elong: max_elong, best_jd, best_kierunek = elong, jd, diff
            jd += step
        return best_jd, max_elong, best_kierunek

    def _doprecyzuj_stacjonarna(self, jd_start, jd_end, body):
        best_jd, min_speed = jd_start, 999.0
        jd, step = jd_start, 1.0 / 1440.0
        while jd <= jd_end:
            coords, _ = swe.calc_ut(jd, body, self.flags)
            if abs(coords[3]) < min_speed: min_speed, best_jd = abs(coords[3]), jd
            jd += step
        return best_jd

    def znajdz_kalendarium_zjawisk(self, utc_start, dni, pozycja, tz, okienko_koniunkcji=5.0, zjawiska_konf=None):
        if zjawiska_konf is None: zjawiska_konf = {}

        zjawiska_jd = []
        jd_base = swe.julday(utc_start.year, utc_start.month, utc_start.day, utc_start.hour)
        jd_end = jd_base + dni
        geopos = (float(pozycja[0]), float(pozycja[1]), float(pozycja[2]))

        def formatuj_czas(jd_val):
            if not jd_val or jd_val == 0.0: return "--:--"
            y, m, d, h_float = swe.revjul(jd_val)
            h, mnt = int(h_float), int((h_float - int(h_float)) * 60)
            sec = int((((h_float - h) * 60) - mnt) * 60)
            dt_utc = datetime.datetime(y, m, d, h, mnt, min(sec, 59), tzinfo=datetime.timezone.utc)
            return dt_utc.astimezone(tz).strftime('%H:%M')

        def przekroczono_0(prv, cur):
            return (prv > 300 and cur < 60) or (prv < 60 and cur > 300)

        def przekroczono_180(prv, cur):
            return (prv < 180 and cur >= 180) or (prv > 180 and cur <= 180)

        def przekroczono_kat(prv, cur, cel):
            if prv < cel <= cur: return True
            if prv > 350 and cur < 10 and (prv < cel <= 360 or 0 <= cel <= cur): return True
            return False

        roje_meteorow = {
            "Kwadrantydy": {"start": 282.5, "max": 283.16, "end": 284.0, "zhr": "110"},
            "Alpha Centaurydy": {"start": 311.0, "max": 319.2, "end": 321.0, "zhr": "Zmienne (do 30)"},
            "Gamma Normidy": {"start": 335.0, "max": 354.0, "end": 7.0, "zhr": "6"},
            "Lirydy": {"start": 24.0, "max": 32.32, "end": 40.0, "zhr": "18"},
            "Pi Puppidy": {"start": 25.0, "max": 33.5, "end": 38.0, "zhr": "Zmienne (do 40)"},
            "Eta Akwarydy": {"start": 19.0, "max": 45.5, "end": 58.0, "zhr": "50"},
            "Czerwcowe Bootydy": {"start": 90.0, "max": 95.7, "end": 100.0, "zhr": "Zmienne (0-100+)"},
            "Alpha Kaprikornidy": {"start": 101.0, "max": 127.0, "end": 142.0, "zhr": "5"},
            "Południowe Delta Akwarydy": {"start": 110.0, "max": 127.6, "end": 146.0, "zhr": "25"},
            "Perseidy": {"start": 114.0, "max": 140.0, "end": 151.0, "zhr": "100"},
            "Kappa Cygnidy": {"start": 131.0, "max": 144.0, "end": 152.0, "zhr": "3"},
            "Aurigidy": {"start": 155.0, "max": 158.6, "end": 163.0, "zhr": "6"},
            "Wrześniowe Epsilon Perseidy": {"start": 162.0, "max": 166.7, "end": 178.0, "zhr": "5"},
            "Południowe Taurydy": {"start": 167.0, "max": 198.0, "end": 238.0, "zhr": "5"},
            "Drakonidy": {"start": 193.0, "max": 195.4, "end": 198.0, "zhr": "Zmienne (0-1000+)"},
            "Orionidy": {"start": 189.0, "max": 208.0, "end": 225.0, "zhr": "20"},
            "Północne Taurydy": {"start": 208.0, "max": 230.0, "end": 258.0, "zhr": "5"},
            "Leonidy": {"start": 224.0, "max": 235.27, "end": 248.0, "zhr": "Zmienne (15-100+)"},
            "Monocerotydy": {"start": 245.0, "max": 257.0, "end": 268.0, "zhr": "3"},
            "Geminidy": {"start": 252.0, "max": 262.2, "end": 265.5, "zhr": "150"},
            "Ursydy": {"start": 265.0, "max": 270.7, "end": 274.0, "zhr": "10 (Zmienne do 50)"}
        }

        if zjawiska_konf.get("fazy_zacmienia", True):
            jd_szukaj = jd_base
            while jd_szukaj <= jd_end:
                try:
                    res = swe.lun_eclipse_when(jd_szukaj, self.flags, False)
                    t_max = res[1][0]
                    if t_max > jd_end: break
                    if res[0] != 0 and t_max >= jd_base:
                        typ = "Zaćmienie Księżyca"
                        if res[0] & swe.ECL_TOTAL:
                            typ = "Całkowite Zaćmienie Księżyca"
                        elif res[0] & swe.ECL_PARTIAL:
                            typ = "Częściowe Zaćmienie Księżyca"
                        zjawiska_jd.append((t_max, typ, f"Maks: {formatuj_czas(t_max)}"))
                    jd_szukaj = t_max + 10.0
                except:
                    jd_szukaj += 10.0

        step = 1.0 / 24.0
        prev_E = prev_sun_lon = None
        hist_D_moon, hist_D_sun, hist_Dec = [], [], []

        planety_zewn = [swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE]
        planety_wewn = [swe.MERCURY, swe.VENUS]
        prev_lon_planet, prev_speed_planet = {}, {}
        hist_elong = {swe.MERCURY: [], swe.VENUS: []}
        wszystkie_ciala = [swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE]
        prev_pair_diff = {}

        jd = jd_base
        while jd <= jd_end:
            sun_pos, _ = swe.calc_ut(jd, swe.SUN, self.flags)
            moon_pos, _ = swe.calc_ut(jd, swe.MOON, self.flags)
            moon_eq, _ = swe.calc_ut(jd, swe.MOON, self.flags | swe.FLG_EQUATORIAL)

            E = (moon_pos[0] - sun_pos[0]) % 360.0
            sun_lon = sun_pos[0]
            D_sun, D_moon, Dec = sun_pos[2], moon_pos[2] * 149597870.7, moon_eq[1]

            if prev_sun_lon is not None and zjawiska_konf.get("pory_roje", True):
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

                for nazwa_roju, p in roje_meteorow.items():
                    if przekroczono_kat(prev_sun_lon, sun_lon, p["start"]): zjawiska_jd.append(
                        (self._doprecyzuj_slonce(jd - step, jd, p["start"]), f"Rój: {nazwa_roju}",
                         "Początek aktywności"))
                    if przekroczono_kat(prev_sun_lon, sun_lon, p["max"]): zjawiska_jd.append(
                        (self._doprecyzuj_slonce(jd - step, jd, p["max"]), f"Rój: {nazwa_roju} (Maksimum)",
                         f"Szczyt (ZHR: ~{p['zhr']})"))
                    if przekroczono_kat(prev_sun_lon, sun_lon, p["end"]): zjawiska_jd.append(
                        (self._doprecyzuj_slonce(jd - step, jd, p["end"]), f"Rój: {nazwa_roju}", "Koniec aktywności"))

            prev_sun_lon = sun_lon

            if prev_E is not None and zjawiska_konf.get("fazy_zacmienia", True):
                if prev_E > 300 and E < 60:
                    t_now = self._doprecyzuj_faze(jd - step, jd, 0)
                    zjawiska_jd.append((t_now, "Nów Księżyca", ""))

                    t_scan, t_end_scan = t_now - 0.125, t_now + 0.125
                    widoczne_momenty, max_faza = [], 0.0

                    while t_scan <= t_end_scan:
                        try:
                            try:
                                res_how = swe.sol_eclipse_how(t_scan, self.flags, geopos)
                            except TypeError:
                                res_how = swe.sol_eclipse_how(t_scan, geopos, self.flags)
                            if res_how[1][2] * 100 > 0.1 and \
                                    oblicz_wysokosc(t_scan, swe.SUN, geopos[0], geopos[1], self.flags)[1] > -0.8333:
                                widoczne_momenty.append(t_scan)
                                if res_how[1][2] * 100 > max_faza: max_faza = res_how[1][2] * 100
                        except:
                            pass
                        t_scan += 1.0 / 1440.0

                    if widoczne_momenty:
                        pocz_str, kon_str = formatuj_czas(widoczne_momenty[0]), formatuj_czas(widoczne_momenty[-1])
                        zjawiska_jd.append(
                            (t_now, "Zaćmienie Słońca", f"Maks: {max_faza:.1f}% | Pocz: {pocz_str} | Kon: {kon_str}"))
                elif prev_E < 90 and E >= 90:
                    zjawiska_jd.append((self._doprecyzuj_faze(jd - step, jd, 90), "Pierwsza Kwadra", ""))
                elif prev_E < 180 and E >= 180:
                    zjawiska_jd.append((self._doprecyzuj_faze(jd - step, jd, 180), "Pełnia Księżyca", ""))
                elif prev_E < 270 and E >= 270:
                    zjawiska_jd.append((self._doprecyzuj_faze(jd - step, jd, 270), "Trzecia Kwadra", ""))

            hist_D_moon.append((jd, D_moon));
            hist_D_sun.append((jd, D_sun));
            hist_Dec.append((jd, Dec))
            if len(hist_D_moon) == 3 and zjawiska_konf.get("ekstrema", True):
                if hist_D_moon[1][1] < hist_D_moon[0][1] and hist_D_moon[1][1] < hist_D_moon[2][1]:
                    zjawiska_jd.append(
                        (self._doprecyzuj_ekstremum(hist_D_moon[0][0], hist_D_moon[2][0], swe.MOON, False, False)[0],
                         "Perygeum Księżyca", ""))
                elif hist_D_moon[1][1] > hist_D_moon[0][1] and hist_D_moon[1][1] > hist_D_moon[2][1]:
                    zjawiska_jd.append(
                        (self._doprecyzuj_ekstremum(hist_D_moon[0][0], hist_D_moon[2][0], swe.MOON, True, False)[0],
                         "Apogeum Księżyca", ""))
                if hist_D_sun[1][1] < hist_D_sun[0][1] and hist_D_sun[1][1] < hist_D_sun[2][1]:
                    zjawiska_jd.append(
                        (self._doprecyzuj_ekstremum(hist_D_sun[0][0], hist_D_sun[2][0], swe.SUN, False, False)[0],
                         "Ziemia w peryhelium", ""))
                elif hist_D_sun[1][1] > hist_D_sun[0][1] and hist_D_sun[1][1] > hist_D_sun[2][1]:
                    zjawiska_jd.append(
                        (self._doprecyzuj_ekstremum(hist_D_sun[0][0], hist_D_sun[2][0], swe.SUN, True, False)[0],
                         "Ziemia w aphelium", ""))
                if hist_Dec[1][1] < hist_Dec[0][1] and hist_Dec[1][1] < hist_Dec[2][1]:
                    zjawiska_jd.append(
                        (self._doprecyzuj_ekstremum(hist_Dec[0][0], hist_Dec[2][0], swe.MOON, False, True)[0],
                         "Maks. deklinacja płd. Księżyca", ""))
                elif hist_Dec[1][1] > hist_Dec[0][1] and hist_Dec[1][1] > hist_Dec[2][1]:
                    zjawiska_jd.append(
                        (self._doprecyzuj_ekstremum(hist_Dec[0][0], hist_Dec[2][0], swe.MOON, True, True)[0],
                         "Maks. deklinacja płn. Księżyca", ""))
                hist_D_moon.pop(0);
                hist_D_sun.pop(0);
                hist_Dec.pop(0)

            for p in planety_zewn + planety_wewn:
                pos_p, _ = swe.calc_ut(jd, p, self.flags)
                diff_lon, speed_lon = (pos_p[0] - sun_lon) % 360.0, pos_p[3]

                if p in prev_lon_planet:
                    prev_lon, nazwa_p = prev_lon_planet[p], self.get_polish_name(p).capitalize()
                    if zjawiska_konf.get("slonce_planety", True):
                        if przekroczono_0(prev_lon, diff_lon): zjawiska_jd.append(
                            (self._doprecyzuj_kat_planetarny(jd - step, jd, p, swe.SUN, 0),
                             f"Koniunkcja ze Słońcem: {nazwa_p}", ""))
                        if p in planety_zewn and przekroczono_180(prev_lon, diff_lon): zjawiska_jd.append(
                            (self._doprecyzuj_kat_planetarny(jd - step, jd, p, swe.SUN, 180), f"Opozycja: {nazwa_p}",
                             ""))

                    if zjawiska_konf.get("elong_retro", True) and p in prev_speed_planet:
                        if prev_speed_planet[p] > 0 and speed_lon <= 0:
                            zjawiska_jd.append(
                                (self._doprecyzuj_stacjonarna(jd - step, jd, p), f"Punkt stacjonarny: {nazwa_p}",
                                 "Początek retrogradacji"))
                        elif prev_speed_planet[p] < 0 and speed_lon >= 0:
                            zjawiska_jd.append(
                                (self._doprecyzuj_stacjonarna(jd - step, jd, p), f"Punkt stacjonarny: {nazwa_p}",
                                 "Koniec retrogradacji"))

                prev_lon_planet[p], prev_speed_planet[p] = diff_lon, speed_lon

            if zjawiska_konf.get("elong_retro", True):
                for p in planety_wewn:
                    elong = diff_lon if prev_lon_planet[p] <= 180 else 360.0 - prev_lon_planet[p]
                    hist_elong[p].append((jd, elong))
                    if len(hist_elong[p]) == 3:
                        e0, e1, e2 = hist_elong[p][0], hist_elong[p][1], hist_elong[p][2]
                        if e1[1] > e0[1] and e1[1] > e2[1]:
                            t_dok, max_val, typ_w_z = self._doprecyzuj_elongacje(e0[0], e2[0], p)
                            kierunek = "Wschodnia" if typ_w_z < 180 else "Zachodnia"
                            zjawiska_jd.append((t_dok, f"Maks. elongacja: {self.get_polish_name(p).capitalize()}",
                                                f"{max_val:.1f}° | {kierunek}"))
                        hist_elong[p].pop(0)

            if zjawiska_konf.get("zakrycia", True):
                for i in range(len(wszystkie_ciala)):
                    for j in range(i + 1, len(wszystkie_ciala)):
                        b1, b2 = wszystkie_ciala[i], wszystkie_ciala[j]
                        if b2 == swe.MOON: b1, b2 = b2, b1
                        para = (b1, b2)

                        diff_para = (swe.calc_ut(jd, b1, self.flags)[0][0] - swe.calc_ut(jd, b2, self.flags)[0][
                            0]) % 360.0
                        if para in prev_pair_diff and przekroczono_0(prev_pair_diff[para], diff_para):
                            t_dok_geo = self._doprecyzuj_kat_planetarny(jd - step, jd, b1, b2, 0)
                            t_scan, min_sep, best_t_topo, best_alt1 = t_dok_geo - 0.5, 999.0, t_dok_geo, 0.0

                            while t_scan <= t_dok_geo + 0.5:
                                az1, alt1, _ = oblicz_wysokosc(t_scan, b1, geopos[0], geopos[1], self.flags)
                                az2, alt2, _ = oblicz_wysokosc(t_scan, b2, geopos[0], geopos[1], self.flags)
                                sep_lokalna = math.sqrt(
                                    (abs(az1 - az2) * math.cos(math.radians(alt1))) ** 2 + abs(alt1 - alt2) ** 2)
                                if sep_lokalna < min_sep: min_sep, best_t_topo, best_alt1 = sep_lokalna, t_scan, alt1
                                t_scan += 2.0 / 1440.0

                            n1, n2 = self.get_polish_name(b1).capitalize(), self.get_polish_name(b2).capitalize()
                            wid = f"(Wys: {best_alt1:.1f}°)" if best_alt1 > 0 else "(Pod horyzontem)"
                            if b1 == swe.MOON and min_sep <= 0.28:
                                zjawiska_jd.append(
                                    (best_t_topo, f"ZAKRYCIE: {n2} przez Księżyc", f"Sep: {min_sep:.2f}° {wid}"))
                            elif min_sep <= okienko_koniunkcji:
                                zjawiska_jd.append(
                                    (best_t_topo, f"Złączenie: {n1} i {n2}", f"Sep: {min_sep:.2f}° {wid}"))
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


def generuj_raport(pozycja, rok, miesiac, dzien, days, strefa_str, krok_planety, obiekty_dso, okienko_koniunkcji=5.0,
                   zjawiska_konf=None):
    if zjawiska_konf is None: zjawiska_konf = {}

    engine = EphemerisEngine(ephe_path='eph_data')
    sprawdz_typ_efemeryd('eph_data')

    LONGITUDE, LATITUDE, ELEV = pozycja
    lokalna_strefa_tz = ZoneInfo(strefa_str)

    naglowki_slonce = ["Dzień", "Słońce Wsch.", "Słońce Gór.", "Słońce Zach.", "Odl. Słońca\n[AU]", "Księżyc Wsch.",
                       "Księżyc Gór.", "Księżyc Zach.", "Odl. Księżyca\n[km]", "Faza\n[%]"]

    planety = [swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE]
    naglowki_planety = ["Dzień", "Świt\nastr.", "Zmierzch\nastr."]
    for p in planety:
        nazwa = engine.get_polish_name(p).capitalize()
        naglowki_planety.append(f"{nazwa}\nW-G-Z")

    try:
        start_date_local = datetime.datetime(rok, miesiac, dzien, 0, 0, 0, tzinfo=lokalna_strefa_tz)
    except ValueError as e:
        print(f"Błąd daty: {e}")
        return [], [], [], [], [], [], [], []

    wyniki_slonce, wyniki_planety, wyniki_dso = [], [], []
    naglowki_dso = ["Dzień"]
    for dso in obiekty_dso: naglowki_dso.append(f"{dso}\nW-G-Z")

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
                    wiersz_s.append(f"{odl_au * 149597870.7:,.0f}".replace(',', ' '))
                    jd_gor_ksiezyca = wyniki['gorowanie_jd']
            except:
                wiersz_s.extend(["Błąd", "Błąd", "Błąd", "Błąd"])

        faza_proc = engine.oblicz_faze_ksiezyca(_jd_to_datetime(jd_gor_ksiezyca) if jd_gor_ksiezyca else utc_time)
        wiersz_s.append(f"{faza_proc:.1f} %")
        wyniki_slonce.append(tuple(wiersz_s))

        if j % krok_planety == 0:
            wyniki_s_tmp = engine.calculate_rise_set(utc_time, LATITUDE, LONGITUDE, ELEV, swe.SUN)
            jd_gor = wyniki_s_tmp['gorowanie_jd']
            swit, zmierzch = oblicz_swit_zmierzch(jd_gor, LONGITUDE, LATITUDE, engine.flags,
                                                  lokalna_strefa_tz) if jd_gor else ("--:--", "--:--")
            wiersz_p = [data_str, swit, zmierzch]

            for p in planety:
                try:
                    wyniki = engine.calculate_rise_set(utc_time, LATITUDE, LONGITUDE, ELEV, p)
                    w, g, z = odkoduj_zjawisko(wyniki, p, LONGITUDE, LATITUDE, engine.flags, lokalna_strefa_tz,
                                               jd_midnight)
                    wiersz_p.append(f"{w}  {g}  {z}")
                except:
                    wiersz_p.append("Błąd")
            wyniki_planety.append(tuple(wiersz_p))

            if obiekty_dso:
                wiersz_dso = [data_str]
                for dso in obiekty_dso:
                    try:
                        wyn = engine.calculate_dso_rise_set(utc_time, LATITUDE, LONGITUDE, ELEV, dso)
                        w = _jd_to_datetime(wyn['wschod_jd']).astimezone(lokalna_strefa_tz).strftime('%H:%M') if wyn[
                            'wschod_jd'] else None
                        g = _jd_to_datetime(wyn['gorowanie_jd']).astimezone(lokalna_strefa_tz).strftime('%H:%M') if wyn[
                            'gorowanie_jd'] else "--:--"
                        z = _jd_to_datetime(wyn['zachod_jd']).astimezone(lokalna_strefa_tz).strftime('%H:%M') if wyn[
                            'zachod_jd'] else None

                        if not w and not z:
                            dec = engine.get_dso_declination(utc_time, dso)
                            if dec:
                                w = z = "/\\" if (LATITUDE >= 0 and dec > 90 - LATITUDE) or (
                                            LATITUDE < 0 and dec < -90 - LATITUDE) else "\\/"
                            else:
                                w = z = "--:--"
                        wiersz_dso.append(f"{w or '--:--'}  {g}  {z or '--:--'}")
                    except:
                        wiersz_dso.append("Błąd")
                wyniki_dso.append(tuple(wiersz_dso))

    naglowki_kalendarium = ["Data i Czas", "Zjawisko Astronomiczne", "Dodatkowe Parametry"]
    utc_start_date = start_date_local.astimezone(datetime.timezone.utc)

    surowe_zjawiska = engine.znajdz_kalendarium_zjawisk(utc_start_date, days, pozycja, lokalna_strefa_tz,
                                                        okienko_koniunkcji, zjawiska_konf)

    wyniki_kalendarium = []
    for jd, nazwa, detal in sorted(surowe_zjawiska, key=lambda x: x[0]):
        czas_str = _jd_to_datetime(jd).astimezone(lokalna_strefa_tz).strftime('%Y-%m-%d %H:%M')
        wyniki_kalendarium.append((czas_str, nazwa, detal))

    return wyniki_slonce, naglowki_slonce, wyniki_planety, naglowki_planety, wyniki_kalendarium, naglowki_kalendarium, wyniki_dso, naglowki_dso