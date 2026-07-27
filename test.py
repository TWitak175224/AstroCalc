import ephem
import math
import datetime
import swisseph as swe
import pyfiglet
from astropy.time import Time
from astropy.coordinates import solar_system_ephemeris, EarthLocation, get_body
solar_system_ephemeris.set('de440')
# Define time and location
t = Time("2026-07-19 22:30:00")
loc = EarthLocation.of_site('greenwich')

# Set ephemeris and get body coordinates

jup = get_body('jupiter', t, loc)
mars = get_body('mars', t, loc)
mercury = get_body('mercury', t, loc)
venus = get_body('venus', t, loc)
saturn = get_body('saturn', t, loc)
uranus = get_body('uranus', t, loc)
neptune = get_body('neptune', t, loc)
moon = get_body('moon', t, loc)
plutoni = get_body('pluto', t, loc)
sun = get_body('sun', t, loc)

print("RA SOL w godzinach:", sun.ra.to_string(unit='hour', sep='hms'), "Dekl SOL: ",sun.dec)
print("RA Mercury w godzinach:", mercury.ra.to_string(unit='hour', sep='hms'),"Dekl: ",mercury.dec)
print("RA Venus w h: ",venus.ra.to_string(unit='hour', sep='hms'),"Dekl: ",venus.dec)
print("RA Moon w h: ",moon.ra.to_string(unit='hour', sep='hms'),"Dekl: ",moon.dec)
print("RA Mars w h: ",mars.ra.to_string(unit='hour', sep='hms'),"Dekl: ",mars.dec)
print("RA Jupiter w h: ",jup.ra.to_string(unit='hour', sep='hms'),"Dekl: ",jup.dec)
print("RA Saturn w h: ",saturn.ra.to_string(unit='hour', sep='hms'),"Dekl: ",saturn.dec)
print("RA Uran w h: ",uranus.ra.to_string(unit='hour', sep='hms'),"Dekl: ",uranus.dec)
print("RA Neptun w h: ",neptune.ra.to_string(unit='hour', sep='hms'),"Dekl: ",neptune.dec)
print("RA Pluto w h: ",plutoni.ra.to_string(unit='hour', sep='hms'),"Dekl: ",plutoni.dec)

from astropy.coordinates import AltAz
from astropy import units as u
# Definiujesz lokalizację obserwatora (Twoje miasto)
obserwator = EarthLocation(lat=53.7784*u.deg, lon=20.4817*u.deg, height=100*u.m) # Olsztyn
altaz_frame = AltAz(location=obserwator, obstime=t)

# Konwertujesz pozycję Jowisza na horyzontalną
jup_altaz = jup.transform_to(altaz_frame)
print(f"Wysokość Jowisza: {jup_altaz.alt}")

from astropy.coordinates import AltAz, EarthLocation, get_body, solar_system_ephemeris
from astropy.time import Time
import astropy.units as u
import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import brentq

# 1. Definiujemy obserwatora (Olsztyn)
loc = EarthLocation(lat=53.7784*u.deg, lon=20.4817*u.deg, height=100*u.m)

# 2. Definiujemy ramkę AltAz z uwzględnieniem refrakcji
# Standardowe ciśnienie: 1013.25 hPa, temperatura: 15 stopni Celsjusza
altaz_frame = AltAz(location=loc,
                    pressure=1013.25 * u.hPa,
                    temperature=15 * u.deg_C)

# 3. Przygotowujemy czas (np. w okolicy wschodu)
t_range = Time('2026-07-27 00:00:00') + np.linspace(0, 0.2, 100) * u.day *2

# 4. Obliczamy pozycje
with solar_system_ephemeris.set('de440'):
    planeta = get_body('jupiter', t_range, loc)
    # Przy transformacji przekazujemy nasz frame z refrakcją
    # Musimy przypisać czas do frame'a, bo refrakcja zależy od wysokości obiektu

    altaz_coords = planeta.transform_to(AltAz(location=loc,
                                              obstime=t_range,
                                              pressure=1013.25 * u.hPa,
                                              temperature=15 * u.deg_C))

# 5. Interpolacja i szukanie zera (horyzontu)
altitudes = altaz_coords.alt.deg
f_alt = interp1d(t_range.jd, altitudes, kind='cubic')

# Szukamy przejścia przez zero
idx = np.where((altitudes[:-1] < 0) & (altitudes[1:] > 0))[0][0]
t_wschodu_jd = brentq(f_alt, t_range[idx].jd, t_range[idx+1].jd)

print(f"Wschód z uwzględnieniem refrakcji: {Time(t_wschodu_jd, format='jd').iso}")
# Upewnij się, że zakres t_range obejmuje wystarczająco czasu (np. 24h)
# Dla pewności, czytając wschód/zachód, używamy interpolacji f_alt (z poprzednich kroków)

# 1. Znajdź wszystkie miejsca przejścia przez zero
# np.diff zwraca 1 gdy (alt < 0 -> alt > 0) i -1 gdy (alt > 0 -> alt < 0)
signs = np.sign(altitudes)
diffs = np.diff(signs)

# Indeksy, gdzie następuje przejście
indices = np.where(diffs != 0)[0]

results = []
for idx in indices:
    # brentq szuka zera w przedziale [idx, idx+1]
    t_jd = brentq(f_alt, t_range[idx].jd, t_range[idx + 1].jd)
    time_iso = Time(t_jd, format='jd')

    # Rozróżnienie wschodu i zachodu
    event_type = "Wschód" if diffs[idx] > 0 else "Zachód"
    results.append((event_type, time_iso))

# Wyświetl wyniki posortowane czasowo
for event_type, t in sorted(results, key=lambda x: x[1]):
    print(f"{event_type}: {t.iso}")