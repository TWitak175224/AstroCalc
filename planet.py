import numpy as np
from astropy.time import Time
from astropy.coordinates import EarthLocation, get_body, AltAz,solar_system_ephemeris
import astropy.units as u
from zoneinfo import ZoneInfo

solar_system_ephemeris.set('de440')
# 1. Twarde ustawienie współrzędnych na Obserwatorium Królewskie w Greenwich
location = EarthLocation(lat=53.7784 * u.deg, lon=20.4801 * u.deg, height=0 * u.m)
strefa_polska = ZoneInfo("Europe/Warsaw")
# 2. Zakres czasu: Doba 2026-07-22 w czasie UT
midnight = Time('2026-07-27 00:00:00', scale='utc')
# Tworzymy tablicę 1440 minut (doba) do interpolacji przejścia przez horyzont
delta_t = np.linspace(0, 24, 1440) * u.hour
times = midnight + delta_t

# 3. Wyliczenie pozycji Jowisza
jupiter = get_body('mercury', times, location)
altaz = jupiter.transform_to(AltAz(obstime=times, location=location))

# 4. Horyzont dla planet (-0.5667 stopnia - bez promienia tarczy słonecznej)
horizon = -(0.5667) * u.deg
is_up = altaz.alt > horizon

# 5. Detekcja wschodu i zachodu
changes = np.diff(is_up.astype(int))
rise_idx = np.where(changes == 1)[0]
set_idx = np.where(changes == -1)[0]

print("Wyniki dla Greenwich (Czas UT):")
print("-" * 30)

if len(rise_idx) > 0:
    # Pobieramy czas i celowo używamy .utc.datetime zamiast konwersji na strefę lokalną
    rise_time = times[rise_idx[0]]
    rise_time_local = rise_time.utc.datetime.replace(tzinfo=ZoneInfo("UTC")).astimezone(strefa_polska)
    print(f"Wschód (Czas lokalny): {rise_time_local.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    ob_rise=get_body('mercury', rise_time, location)
    ra = ob_rise.ra
    dec = ob_rise.dec
    print(f"  -> Rektascensja (RA): {ra.to_string(u.hour, sep=':')}")
    print(f"  -> Deklinacja (Dec):  {dec.to_string(u.deg, sep=':')}")

if len(set_idx) > 0:
    set_time = times[set_idx[0]]
    set_time_local = set_time.utc.datetime.replace(tzinfo=ZoneInfo("UTC")).astimezone(strefa_polska)
    print(f"Zachód Merkurego: {set_time_local.strftime('%y-%m-%d %H:%M:%S')}")
