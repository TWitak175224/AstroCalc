import matplotlib.pyplot as plt
import numpy as np

# Załóżmy, że masz już wyliczone długości ekliptyczne planet w momencie wschodu / interesującym Cię czasie:
# (Wartości w stopnich od 0 do 360)
pozycje_planet = {
    'Słońce': 124.5,
    'Księżyc': 45.2,
    'Merkury': 110.8,
    'Wenus': 95.0,
    'Mars': 210.3,
    'Jowisz': 85.6,
    'Saturn': 330.1
}

# Tworzymy wykres polarny (idealny do odwzorowania koła zodiaku)
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})

# Ziemia w centrum
ax.plot(0, 0, 'ro', markersize=10, label='Ziemia (Centrum)')

# Nanosimy planety na okrąg
for nazwa, kat_deg in pozycje_planet.items():
    # Konwersja stopni na radiany wymagana przez matplotlib
    kat_rad = np.deg2rad(kat_deg)

    # Promień ustawiamy na stałą odległość (schemat) lub zmienną (faktyczna odległość geocentryczna)
    promien = 1.0

    # Rysujemy punkt planety
    ax.plot(kat_rad, promien, 'o', markersize=6)
    # Dodajemy etykietę z nazwą obok punktu
    ax.text(kat_rad, promien + 0.1, nazwa, fontsize=10, ha='center', va='center')

# Konfiguracja wykresu, aby przypominał zodiak (0 stopni u góry, kierunek przeciwny do wskazówek zegara)
ax.set_theta_zero_location('N')  # 0 stopni na górze (Baran)
ax.set_theta_direction(-1)  # Ruch zgodnie ze wskazówkami zegara (standard astrologiczny)
ax.set_rticks([])  # Usuwamy pierścienie odległości
ax.grid(True)

plt.title("Statyczny widok geocentryczny (układ zodiakalny)", va='bottom', fontsize=14)
plt.show()