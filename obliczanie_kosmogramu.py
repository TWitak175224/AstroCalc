import swisseph as swe
import datetime
from zoneinfo import ZoneInfo
import itertools

ZNAKI_ZODIAKU = ["Baran", "Byk", "Bliźnięta", "Rak", "Lew", "Panna",
                 "Waga", "Skorpion", "Strzelec", "Koziorożec", "Wodnik", "Ryby"]

SYSTEMY_DOMOW = {
    "Placidus": b'P', "Koch": b'K', "Regiomontanus": b'R',
    "Campanus": b'C', "Równe (Equal)": b'E'
}

# Grupy obiektów do dynamicznego zwężania orbów
PUNKTY_WIRTUALNE = ["Lilith", "Węzeł Półn.", "Węzeł Połud.", "Ascendent", "Medium Coeli"]
PLANETY_POKOLENIOWE = ["Uran", "Neptun", "Pluton"]


def stopnie_na_znak(stopnie):
    indeks = int(stopnie // 30)
    reszta = stopnie % 30
    stopnie_calkowite = int(reszta)
    minuty = int((reszta - stopnie_calkowite) * 60)
    return f"{stopnie_calkowite:02d}°{minuty:02d}' {ZNAKI_ZODIAKU[indeks]}"


def pobierz_limit_orbu(nazwa1, nazwa2, bazowy_orb):
    # Punkty matematyczne (osie, węzły, Lilith) wymagają dużej precyzji
    if nazwa1 in PUNKTY_WIRTUALNE or nazwa2 in PUNKTY_WIRTUALNE:
        return min(bazowy_orb, 5.0)

    # Aspekty między wolnymi planetami pokoleniowymi rzadko liczy się z pełnym orbem
    if nazwa1 in PLANETY_POKOLENIOWE and nazwa2 in PLANETY_POKOLENIOWE:
        return min(bazowy_orb, 4.0)

    # Dla świateł (Słońce, Księżyc) i planet osobistych zostawiamy pełny orb z GUI
    return bazowy_orb


def sprawdz_aspekt(nazwa1, lon1, nazwa2, lon2, aspekty_konfig):
    diff = abs(lon1 - lon2)
    if diff > 180: diff = 360.0 - diff
    for asp in aspekty_konfig:
        dopuszczalny_orb = pobierz_limit_orbu(nazwa1, nazwa2, asp["orb"])

        if abs(diff - asp["kat"]) <= dopuszczalny_orb:
            dokladnosc = abs(diff - asp["kat"])
            deg = int(dokladnosc)
            minut = int((dokladnosc - deg) * 60)
            return asp["nazwa"], f"{deg}°{minut:02d}'", dokladnosc
    return None, None, None


def generuj_kosmogram(config):
    swe.set_ephe_path('eph_data')
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED

    rok, mc, dzien = map(int, config['urodz_data'].split('-'))
    godz, min_ = map(int, config['urodz_czas'].split(':'))

    lokalna_strefa = ZoneInfo(config['timezone'])
    dt_local = datetime.datetime(rok, mc, dzien, godz, min_, 0, tzinfo=lokalna_strefa)
    dt_utc = dt_local.astimezone(datetime.timezone.utc)

    decimal_hour = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    jd_utc = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, decimal_hour)

    orby_cfg = config.get("orby", {})
    aspekty_konfig = [
        {"nazwa": "Koniunkcja", "kat": 0, "orb": orby_cfg.get("Koniunkcja", 8.0)},
        {"nazwa": "Sekstyl", "kat": 60, "orb": orby_cfg.get("Sekstyl", 6.0)},
        {"nazwa": "Kwadratura", "kat": 90, "orb": orby_cfg.get("Kwadratura", 8.0)},
        {"nazwa": "Trygon", "kat": 120, "orb": orby_cfg.get("Trygon", 8.0)},
        {"nazwa": "Opozycja", "kat": 180, "orb": orby_cfg.get("Opozycja", 8.0)}
    ]

    planety = [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS,
               swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO,
               swe.MEAN_APOG, swe.TRUE_NODE]

    nazwy_planet = ["Słońce", "Księżyc", "Merkury", "Wenus", "Mars",
                    "Jowisz", "Saturn", "Uran", "Neptun", "Pluton",
                    "Lilith", "Węzeł Półn."]

    wyniki_planety = []
    dane_do_aspektow = []
    wezel_pn_lon = None

    for p, nazwa in zip(planety, nazwy_planet):
        coords, _ = swe.calc_ut(jd_utc, p, flags)
        lon = coords[0]
        znak_str = stopnie_na_znak(lon)

        retro = " (R)" if coords[3] < 0 and p not in (swe.SUN, swe.MOON, swe.MEAN_APOG) else ""
        wyniki_planety.append((nazwa, znak_str + retro, f"{lon:.4f}°"))
        dane_do_aspektow.append((nazwa, lon))

        if p == swe.TRUE_NODE:
            wezel_pn_lon = lon

    if wezel_pn_lon is not None:
        wezel_pd_lon = (wezel_pn_lon + 180.0) % 360.0
        wyniki_planety.append(("Węzeł Połud.", stopnie_na_znak(wezel_pd_lon), f"{wezel_pd_lon:.4f}°"))
        dane_do_aspektow.append(("Węzeł Połud.", wezel_pd_lon))

    hsys = SYSTEMY_DOMOW.get(config['sys_domow'], b'P')
    cusps, ascmc = swe.houses(jd_utc, float(config['lat_dd']), float(config['lon_dd']), hsys)

    wyniki_domy = []

    asc = ascmc[0]
    mc = ascmc[1]
    dc = (asc + 180.0) % 360.0
    ic = (mc + 180.0) % 360.0

    wyniki_domy.append(("Ascendent (ASC)", stopnie_na_znak(asc), f"{asc:.4f}°"))
    wyniki_domy.append(("Descendant (DC)", stopnie_na_znak(dc), f"{dc:.4f}°"))
    wyniki_domy.append(("Medium Coeli (MC)", stopnie_na_znak(mc), f"{mc:.4f}°"))
    wyniki_domy.append(("Imum Coeli (IC)", stopnie_na_znak(ic), f"{ic:.4f}°"))
    wyniki_domy.append(("", "", ""))

    dane_do_aspektow.append(("Ascendent", asc))
    dane_do_aspektow.append(("Medium Coeli", mc))

    for i in range(12):
        wyniki_domy.append((f"Dom {i + 1}", stopnie_na_znak(cusps[i]), f"{cusps[i]:.4f}°"))

    wyniki_aspekty = []
    for p1, p2 in itertools.combinations(dane_do_aspektow, 2):
        nazwa1, lon1 = p1
        nazwa2, lon2 = p2
        aspekt, opis_orbu, dokladnosc_raw = sprawdz_aspekt(nazwa1, lon1, nazwa2, lon2, aspekty_konfig)
        if aspekt:
            wyniki_aspekty.append((nazwa1, aspekt, nazwa2, opis_orbu, dokladnosc_raw))

    wyniki_aspekty.sort(key=lambda x: x[4])
    wyniki_aspekty_final = [(w[0], w[1], w[2], w[3]) for w in wyniki_aspekty]

    return wyniki_planety, wyniki_domy, wyniki_aspekty_final