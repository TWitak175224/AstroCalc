import tkinter as tk
from tkinter import ttk, messagebox


class StartPanel(tk.Frame):
    def __init__(self, parent, on_start_callback):
        super().__init__(parent)
        self.on_start_callback = on_start_callback

        self.setup_ui()

    def setup_ui(self):
        # --- Sekcja Daty ---
        tk.Label(self, text="Data początkowa (RRRR-MM-DD):").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.entry_date = tk.Entry(self, width=15)
        self.entry_date.insert(0, "2026-08-01")
        self.entry_date.grid(row=0, column=1, pady=5, padx=5)

        tk.Label(self, text="Ilość dni do analizy:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.entry_days = tk.Entry(self, width=15)
        self.entry_days.insert(0, "7")
        self.entry_days.grid(row=1, column=1, pady=5, padx=5)

        # --- Sekcja Współrzędnych (DMS) ---
        tk.Label(self, text="Szerokość Geograficzna (N):").grid(row=2, column=0, sticky=tk.W, pady=15, padx=5)
        frame_lat = tk.Frame(self)
        frame_lat.grid(row=2, column=1, sticky=tk.W)
        self.lat_d = tk.Entry(frame_lat, width=4);
        self.lat_d.pack(side=tk.LEFT)
        tk.Label(frame_lat, text="°").pack(side=tk.LEFT)
        self.lat_m = tk.Entry(frame_lat, width=4);
        self.lat_m.pack(side=tk.LEFT)
        tk.Label(frame_lat, text="'").pack(side=tk.LEFT)
        self.lat_s = tk.Entry(frame_lat, width=4);
        self.lat_s.pack(side=tk.LEFT)
        tk.Label(frame_lat, text="\"").pack(side=tk.LEFT)

        tk.Label(self, text="Długość Geograficzna (E):").grid(row=3, column=0, sticky=tk.W, pady=5, padx=5)
        frame_lon = tk.Frame(self)
        frame_lon.grid(row=3, column=1, sticky=tk.W)
        self.lon_d = tk.Entry(frame_lon, width=4);
        self.lon_d.pack(side=tk.LEFT)
        tk.Label(frame_lon, text="°").pack(side=tk.LEFT)
        self.lon_m = tk.Entry(frame_lon, width=4);
        self.lon_m.pack(side=tk.LEFT)
        tk.Label(frame_lon, text="'").pack(side=tk.LEFT)
        self.lon_s = tk.Entry(frame_lon, width=4);
        self.lon_s.pack(side=tk.LEFT)
        tk.Label(frame_lon, text="\"").pack(side=tk.LEFT)

        # Wypełnienie domyślne (np. Olsztyn: 53°46'N, 20°29'E)
        self.lat_d.insert(0, "53");
        self.lat_m.insert(0, "46");
        self.lat_s.insert(0, "0")
        self.lon_d.insert(0, "20");
        self.lon_m.insert(0, "29");
        self.lon_s.insert(0, "0")

        # --- Przycisk Akcji ---
        btn_start = tk.Button(self, text="Uruchom Obliczenia", command=self.zbierz_i_wyslij, bg="#4CAF50", fg="white")
        btn_start.grid(row=4, column=0, columnspan=2, pady=20, ipadx=10, ipady=5)

    def dms_to_dd(self, d, m, s):
        """Konwersja Stopnie, Minuty, Sekundy na ułamek dziesiętny (Decimal Degrees)"""
        return float(d) + (float(m) / 60.0) + (float(s) / 3600.0)

    def zbierz_i_wyslij(self):
        try:
            # 1. Pobranie daty
            data_str = self.entry_date.get().split("-")
            rok, miesiac, dzien = int(data_str[0]), int(data_str[1]), int(data_str[2])
            dni = int(self.entry_days.get())

            # 2. Przeliczenie współrzędnych DMS -> DD
            lat_dd = self.dms_to_dd(self.lat_d.get(), self.lat_m.get(), self.lat_s.get())
            lon_dd = self.dms_to_dd(self.lon_d.get(), self.lon_m.get(), self.lon_s.get())

            # 3. Zapakowanie danych w słownik (struktura transferowa)
            konfiguracja = {
                "rok": rok,
                "miesiac": miesiac,
                "dzien": dzien,
                "dni_do_analizy": dni,
                "lat_dd": lat_dd,
                "lon_dd": lon_dd
            }

            # 4. Wywołanie callbacka z main.py
            self.on_start_callback(konfiguracja)

        except ValueError:
            messagebox.showerror("Błąd danych",
                                 "Upewnij się, że wprowadzone wartości są poprawne i mają format liczbowy.")