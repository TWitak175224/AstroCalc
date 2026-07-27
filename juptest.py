import numpy as np
from astropy.time import Time
from astropy.coordinates import EarthLocation, get_body, AltAz
import astropy.units as u

# 1. Twarde ustawienie współrzędnych na Obserwatorium Królewskie w Greenwich
greenwich = EarthLocation(lat=50.053527 * u.deg, lon=0.0 * u.deg, height=0 * u.m)

# 2. Zakres czasu: Doba 2026-07-22 w czasie UT
midnight = Time('2026-07-27 00:00:00', scale='utc')
# Tworzymy tablicę 1440 minut (doba) do interpolacji przejścia przez horyzont
delta_t = np.linspace(0, 24, 1440) * u.hour
times = midnight + delta_t

# 3. Wyliczenie pozycji Jowisza
jupiter = get_body('moon', times, greenwich)
altaz = jupiter.transform_to(AltAz(obstime=times, location=greenwich))

# 4. Horyzont dla planet (-0.5667 stopnia - bez promienia tarczy słonecznej)
horizon = -(0.5667+0.25) * u.deg
is_up = altaz.alt > horizon

# 5. Detekcja wschodu i zachodu
changes = np.diff(is_up.astype(int))
rise_idx = np.where(changes == 1)[0]
set_idx = np.where(changes == -1)[0]

print("Wyniki dla Greenwich (Czas UT):")
print("-" * 30)

if len(rise_idx) > 0:
    # Pobieramy czas i celowo używamy .utc.datetime zamiast konwersji na strefę lokalną
    rise_time = times[rise_idx[0]].utc.datetime
    print(f"Wschód Księżyca: {rise_time.strftime('%H:%M:%S')}")

if len(set_idx) > 0:
    set_time = times[set_idx[0]].utc.datetime
    print(f"Zachód Księżyca: {set_time.strftime('%H:%M:%S')}")