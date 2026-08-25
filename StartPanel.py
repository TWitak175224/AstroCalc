import tkinter as tk
from tkinter import ttk, messagebox
import tkintermapview
import requests
import threading
from timezonefinder import TimezoneFinder


class StartPanel(tk.Frame):
    def __init__(self, parent, on_start_callback):
        super().__init__(parent)
        self.on_start_callback = on_start_callback
        self.znacznik = None
        self.tf = TimezoneFinder()

        self.setup_ui()

    def setup_ui(self):
        panel_lewy = tk.Frame(self, width=280)
        panel_lewy.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        panel_prawy = tk.Frame(self)
        panel_prawy.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(panel_lewy, text="Parametry Obliczeń", font=("Helvetica", 12, "bold")).pack(pady=(0, 15))

        # Zakres Czasowy
        # Zakres Czasowy
        ramka_czasu = tk.LabelFrame(panel_lewy, text="Zakres Czasowy")
        ramka_czasu.pack(fill=tk.X, pady=5)

        tk.Label(ramka_czasu, text="Data startu (RRRR-MM-DD):").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.entry_date = tk.Entry(ramka_czasu)
        self.entry_date.insert(0, "2026-08-01")
        self.entry_date.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(ramka_czasu, text="Liczba dni do wyliczenia:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.entry_days = tk.Entry(ramka_czasu)
        self.entry_days.insert(0, "7")
        self.entry_days.pack(fill=tk.X, padx=5, pady=2)

        # --- NOWE: Kontrolka Spinbox do wyboru kroku dla planet ---
        tk.Label(ramka_czasu, text="Krok dla planet (1-20 dni):").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.entry_krok = tk.Spinbox(ramka_czasu, from_=1, to=20, width=18)
        self.entry_krok.delete(0, tk.END)
        self.entry_krok.insert(0, "2")  # Domyślnie ustawiamy klasyczne 2 dni
        self.entry_krok.pack(fill=tk.X, padx=5, pady=(2, 10))

        # Lokalizacja
        ramka_geo = tk.LabelFrame(panel_lewy, text="Lokalizacja Obserwatora")
        ramka_geo.pack(fill=tk.X, pady=10)

        tk.Label(ramka_geo, text="Szerokość (Lat DD):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_lat = tk.Entry(ramka_geo, width=12)
        self.entry_lat.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(ramka_geo, text="Długość (Lon DD):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_lon = tk.Entry(ramka_geo, width=12)
        self.entry_lon.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(ramka_geo, text="Wysokość (m n.p.m.):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_elev = tk.Entry(ramka_geo, width=12)
        self.entry_elev.insert(0, "100.0")
        self.entry_elev.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(ramka_geo, text="Strefa czasowa:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.lbl_strefa = tk.Label(ramka_geo, text="Europe/Warsaw", fg="blue", font=("Helvetica", 9, "bold"))
        self.lbl_strefa.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        tk.Label(ramka_geo, text="Wskazówka:\nKliknij Prawym Przyciskiem\nna mapie, aby ustawić pozycję.",
                 fg="gray", justify=tk.LEFT).grid(row=4, column=0, columnspan=2, pady=10)

        # Przycisk
        btn_start = tk.Button(panel_lewy, text="Generuj Efemerydy", command=self.zbierz_i_wyslij, bg="#4CAF50",
                              fg="white", font=("Helvetica", 10, "bold"))
        btn_start.pack(fill=tk.X, pady=20, ipady=5)


        # Mapa
        self.mapa = tkintermapview.TkinterMapView(panel_prawy, corner_radius=5)
        self.mapa.pack(fill=tk.BOTH, expand=True)

        # Ustawiamy powiększenie obejmujące całą Polskę (domyślnie było 2 dla świata)
        self.mapa.set_zoom(6)

        # Wyśrodkowanie mapy na geometryczny środek Polski (współrzędne miejscowości Piątek)
        self.mapa.set_position(52.0691, 19.4805)


        # (Wewnątrz def setup_ui)
        self.mapa.add_right_click_menu_command(label="Ustaw punkt obserwacji",
                                               command=self.ustaw_punkt_z_mapy,
                                               pass_coords=True)

        # --- WYWOŁANIE NASZEJ NOWEJ SIATKI ---
        self.rysuj_siatke(co_ile_stopni=15)

    def ustaw_punkt_z_mapy(self, coords):
        lat, lon = coords
        if self.znacznik:
            self.znacznik.delete()
        self.znacznik = self.mapa.set_marker(lat, lon, text="Obserwator")

        self.entry_lat.delete(0, tk.END)
        self.entry_lat.insert(0, str(round(lat, 5)))

        self.entry_lon.delete(0, tk.END)
        self.entry_lon.insert(0, str(round(lon, 5)))

        self.entry_elev.delete(0, tk.END)
        self.entry_elev.insert(0, "Pobieranie...")

        # Detekcja strefy czasowej offline
        strefa_str = self.tf.timezone_at(lat=lat, lng=lon)
        if not strefa_str:
            strefa_str = "UTC"
        self.lbl_strefa.config(text=strefa_str)

        # Pobieranie elewacji w tle
        thread = threading.Thread(target=self.pobierz_wysokosc, args=(lat, lon))
        thread.daemon = True
        thread.start()

    def pobierz_wysokosc(self, lat, lon):
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                dane = response.json()
                wysokosc = dane['results'][0]['elevation']
                self.entry_elev.delete(0, tk.END)
                self.entry_elev.insert(0, str(float(wysokosc)))
            else:
                self.ustaw_domyslna_wysokosc()
        except requests.RequestException:
            self.ustaw_domyslna_wysokosc()

    def ustaw_domyslna_wysokosc(self):
        self.entry_elev.delete(0, tk.END)
        self.entry_elev.insert(0, "100.0")

    def zbierz_i_wyslij(self):
        try:
            data_str = self.entry_date.get().split("-")
            rok, miesiac, dzien = int(data_str[0]), int(data_str[1]), int(data_str[2])
            dni = int(self.entry_days.get())

            lat_dd = float(self.entry_lat.get())
            lon_dd = float(self.entry_lon.get())
            strefa_str = self.lbl_strefa.cget("text")

            try:
                elev = float(self.entry_elev.get())
            except ValueError:
                elev = 100.0

            krok = int(self.entry_krok.get())
            if not (1 <= krok <= 20):
                raise ValueError("Krok dla planet musi być w przedziale 1-20.")

            konfiguracja = {
                "rok": rok,
                "miesiac": miesiac,
                "dzien": dzien,
                "dni_do_analizy": dni,
                "lat_dd": lat_dd,
                "lon_dd": lon_dd,
                "elev": elev,
                "timezone": strefa_str,
                "krok_planety": krok  
            }

            self.on_start_callback(konfiguracja)

        except Exception as e:
            messagebox.showerror("Błąd danych", f"Sprawdź poprawność wprowadzonych danych.\nSzczegóły: {e}")

    def rysuj_siatke(self, co_ile_stopni=15):
        """Generuje astronomiczną siatkę kartograficzną na mapie świata."""
        # Parametry wizualne siatki (subtelny, szary kolor)
        kolor_linii = "#808080"

        # 1. Równoleżniki (Szerokość geograficzna / Latitude)
        # Omijamy same bieguny, rysujemy od -75 do 75 stopni
        for lat in range(-75, 90, co_ile_stopni):
            # Linia musi składać się z wielu punktów, żeby gładko przylegać do mapy
            sciezka_lat = [(lat, lon) for lon in range(-180, 181, 5)]
            self.mapa.set_path(sciezka_lat, color=kolor_linii, width=1)

        # 2. Południki (Długość geograficzna / Longitude)
        for lon in range(-180, 181, co_ile_stopni):
            # Rysujemy od -85 do 85 (limit odwzorowania Mercatora)
            sciezka_lon = [(lat, lon) for lat in range(-85, 86, 5)]
            self.mapa.set_path(sciezka_lon, color=kolor_linii, width=1)