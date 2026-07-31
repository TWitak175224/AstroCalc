import tkinter as tk
from tkinter import ttk
import datetime



class StartPanel(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Kalkulator Astronomiczny - Panel Startowy")
        self.geometry("450x480")
        self.resizable(False, False)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)

        self.create_widgets()

    def create_widgets(self):
        # --- NAGŁÓWEK ---
        header = ttk.Label(self, text="Konfiguracja Kalendarza", font=("Helvetica", 14, "bold"))
        header.grid(row=0, column=0, columnspan=2, pady=(15, 10))

        # --- 1. MIEJSCE (NAZWA IDENTYFIKACYJNA) ---
        ttk.Label(self, text="Nazwa miejsca:").grid(row=1, column=0, sticky=tk.W, padx=20, pady=5)
        self.location_var = tk.StringVar(value="Olsztyn")
        self.location_entry = ttk.Entry(self, textvariable=self.location_var, width=30)
        self.location_entry.grid(row=1, column=1, sticky=tk.W, pady=5)

        # --- 2. WSPÓŁRZĘDNE GEOGRAFICZNE (RAMKA) ---
        coord_frame = ttk.LabelFrame(self, text="Współrzędne (Stopnie, Minuty, Sekundy)")
        coord_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="ew")

        # Szerokość (Latitude)
        ttk.Label(coord_frame, text="Szerokość:").grid(row=0, column=0, padx=(10, 5), pady=5, sticky=tk.W)
        self.lat_deg = ttk.Spinbox(coord_frame, from_=0, to=90, width=3)
        self.lat_deg.set(53)
        self.lat_deg.grid(row=0, column=1)
        ttk.Label(coord_frame, text="°").grid(row=0, column=2)

        self.lat_min = ttk.Spinbox(coord_frame, from_=0, to=59, width=3)
        self.lat_min.set(46)
        self.lat_min.grid(row=0, column=3)
        ttk.Label(coord_frame, text="'").grid(row=0, column=4)

        self.lat_sec = ttk.Spinbox(coord_frame, from_=0, to=59, width=3)
        self.lat_sec.set(42)
        self.lat_sec.grid(row=0, column=5)
        ttk.Label(coord_frame, text="\"").grid(row=0, column=6)

        self.lat_dir = ttk.Combobox(coord_frame, values=["N", "S"], state="readonly", width=3)
        self.lat_dir.set("N")
        self.lat_dir.grid(row=0, column=7, padx=(5, 10))

        # Długość (Longitude)
        ttk.Label(coord_frame, text="Długość:").grid(row=1, column=0, padx=(10, 5), pady=5, sticky=tk.W)
        self.lon_deg = ttk.Spinbox(coord_frame, from_=0, to=180, width=3)
        self.lon_deg.set(20)
        self.lon_deg.grid(row=1, column=1)
        ttk.Label(coord_frame, text="°").grid(row=1, column=2)

        self.lon_min = ttk.Spinbox(coord_frame, from_=0, to=59, width=3)
        self.lon_min.set(28)
        self.lon_min.grid(row=1, column=3)
        ttk.Label(coord_frame, text="'").grid(row=1, column=4)

        self.lon_sec = ttk.Spinbox(coord_frame, from_=0, to=59, width=3)
        self.lon_sec.set(48)
        self.lon_sec.grid(row=1, column=5)
        ttk.Label(coord_frame, text="\"").grid(row=1, column=6)

        self.lon_dir = ttk.Combobox(coord_frame, values=["E", "W"], state="readonly", width=3)
        self.lon_dir.set("E")
        self.lon_dir.grid(row=1, column=7, padx=(5, 10))

        # --- 3. MIESIĄC I ROK STARTOWY ---
        ttk.Label(self, text="Start obliczeń:").grid(row=3, column=0, sticky=tk.W, padx=20, pady=10)
        date_frame = ttk.Frame(self)
        date_frame.grid(row=3, column=1, sticky=tk.W, pady=10)

        miesiace = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
                    "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
        self.month_cb = ttk.Combobox(date_frame, values=miesiace, state="readonly", width=12)
        self.month_cb.current(datetime.date.today().month - 1)
        self.month_cb.pack(side=tk.LEFT, padx=(0, 5))

        self.year_sb = ttk.Spinbox(date_frame, from_=1900, to=2100, width=6)
        self.year_sb.set(datetime.date.today().year)
        self.year_sb.pack(side=tk.LEFT)

        # --- 4. ILOŚĆ MIESIĘCY ---
        ttk.Label(self, text="Zakres (miesiące):").grid(row=4, column=0, sticky=tk.W, padx=20, pady=5)
        self.duration_sb = ttk.Spinbox(self, from_=1, to=120, width=5)
        self.duration_sb.set(1)
        self.duration_sb.grid(row=4, column=1, sticky=tk.W, pady=5)

        # --- PRZYCISK GENERUJ ---
        self.submit_btn = ttk.Button(self, text="Generuj Kalendarz", command=self.on_submit)
        self.submit_btn.grid(row=5, column=0, columnspan=2, pady=(20, 10))

    def dms_to_decimal(self, degrees, minutes, seconds, direction):
        """Przelicza format DMS na stopnie dziesiętne."""
        decimal = float(degrees) + (float(minutes) / 60.0) + (float(seconds) / 3600.0)
        if direction in ['S', 'W']:
            decimal *= -1
        return decimal

    def on_submit(self):
        lokalizacja = self.location_var.get().strip()
        miesiac = self.month_cb.current() + 1
        rok = int(self.year_sb.get())
        ilosc_miesiecy = int(self.duration_sb.get())

        lat_dec = self.dms_to_decimal(self.lat_deg.get(), self.lat_min.get(), self.lat_sec.get(), self.lat_dir.get())
        lon_dec = self.dms_to_decimal(self.lon_deg.get(), self.lon_min.get(), self.lon_sec.get(), self.lon_dir.get())

        # Pakujemy wszystkie dane do słownika
        dane_wejsciowe = {
            "lokalizacja": lokalizacja,
            "lat": lat_dec,
            "lon": lon_dec,
            "rok": rok,
            "miesiac": miesiac,
            "ilosc_miesiecy": ilosc_miesiecy
        }

        # Jeśli przekazano funkcję z głównego programu, wywołujemy ją
        if self.on_generate_callback:
            self.on_generate_callback(dane_wejsciowe)

        # Zamykamy okno startowe po udanym przekazaniu danych
        self.destroy()


if __name__ == "__main__":
    app = StartPanel()
    app.mainloop()
