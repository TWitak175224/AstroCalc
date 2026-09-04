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

ASPEKTY = [
    {"nazwa": "Koniunkcja", "kat": 0, "orb": 8},
    {"nazwa": "Sekstyl", "kat": 60, "orb": 6},
    {"nazwa": "Kwadratura", "kat": 90, "orb": 8},
    {"nazwa": "Trygon", "kat": 120, "orb": 8},
    {"nazwa": "Opozycja", "kat": 180, "orb": 8}
]


def stopnie_na_znak(stopnie):
    indeks = int(stopnie // 30)
    reszta = stopnie % 30
    stopnie_calkowite = int(reszta)
    minuty = int((reszta - stopnie_calkowite) * 60)
    return f"{stopnie_calkowite:02d}°{minuty:02d}' {ZNAKI_ZODIAKU[indeks]}"


def sprawdz_aspekt(lon1, lon2):
    diff = abs(lon1 - lon2)
    if diff > 180: diff = 360.0 - diff
    for asp in ASPEKTY:
        if abs(diff - asp["kat"]) <= asp["orb"]:
            dokladnosc = abs(diff - asp["kat"])
            deg = int(dokladnosc)
            minut = int((dokladnosc - deg) * 60)
            return asp["nazwa"], f"{deg}°{minut:02d}'"
    return None, None


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
        aspekt, orb = sprawdz_aspekt(lon1, lon2)
        if aspekt:
            wyniki_aspekty.append((nazwa1, aspekt, nazwa2, orb))

    # Sortujemy od najściślejszego aspektu (orb najbliżej 0)
    wyniki_aspekty.sort(key=lambda x: x[3])

    return wyniki_planety, wyniki_domy, wyniki_aspekty