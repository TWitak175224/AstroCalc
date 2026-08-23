import tkinter as tk
from tkinter import ttk, messagebox
import tkintermapview
import requests
import threading


class StartPanel(tk.Frame):
    def __init__(self, parent, on_start_callback):
        super().__init__(parent)
        self.on_start_callback = on_start_callback
        self.znacznik = None  # Przechowuje aktualną pinezkę na mapie

        self.setup_ui()

    def setup_ui(self):
        # --- Podział na lewy panel (formularz) i prawy (mapa) ---
        panel_lewy = tk.Frame(self, width=250)
        panel_lewy.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        panel_prawy = tk.Frame(self)
        panel_prawy.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ====== PANEL LEWY: FORMULARZ ======
        tk.Label(panel_lewy, text="Ustawienia Kalendarza", font=("Helvetica", 12, "bold")).pack(pady=(0, 15))

        # 1. Data i czas
        ramka_czasu = tk.LabelFrame(panel_lewy, text="Zakres Czasowy")
        ramka_czasu.pack(fill=tk.X, pady=5)

        tk.Label(ramka_czasu, text="Data startu (RRRR-MM-DD):").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.entry_date = tk.Entry(ramka_czasu)
        self.entry_date.insert(0, "2026-08-01")
        self.entry_date.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(ramka_czasu, text="Liczba dni do wyliczenia:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.entry_days = tk.Entry(ramka_czasu)
        self.entry_days.insert(0, "7")
        self.entry_days.pack(fill=tk.X, padx=5, pady=(2, 10))

        # 2. Współrzędne
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
        self.entry_elev.insert(0, "0.0")
        self.entry_elev.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(ramka_geo, text="Wskazówka:\nKliknij Prawym Przyciskiem\nna mapie, aby ustawić pozycję.",
                 fg="gray", justify=tk.LEFT).grid(row=3, column=0, columnspan=2, pady=10)

        # 3. Przycisk Akcji
        btn_start = tk.Button(panel_lewy, text="Generuj Efemerydy", command=self.zbierz_i_wyslij, bg="#4CAF50",
                              fg="white", font=("Helvetica", 10, "bold"))
        btn_start.pack(fill=tk.X, pady=20, ipady=5)

        # ====== PANEL PRAWY: MAPA ŚWIATA ======
        # Inicjalizacja widgetu mapy
        self.mapa = tkintermapview.TkinterMapView(panel_prawy, corner_radius=5)
        self.mapa.pack(fill=tk.BOTH, expand=True)

        # Ustawiamy oddalenie na mapę świata
        self.mapa.set_zoom(2)

        # Opcjonalnie: możemy wyśrodkować mapę np. na Europę
        self.mapa.set_position(52.0, 20.0)

        # Dodajemy zdarzenie: Kliknięcie prawym przyciskiem myszy wywołuje naszą metodę
        self.mapa.add_right_click_menu_command(label="Ustaw punkt obserwacji",
                                               command=self.ustaw_punkt_z_mapy,
                                               pass_coords=True)

    def ustaw_punkt_z_mapy(self, coords):
        """Metoda wywoływana po kliknięciu prawym przyciskiem na mapie."""
        lat, lon = coords

        # 1. Zarządzanie znacznikiem na mapie (usuwamy stary, dajemy nowy)
        if self.znacznik:
            self.znacznik.delete()
        self.znacznik = self.mapa.set_marker(lat, lon, text="Obserwator")

        # 2. Wpisanie danych do formularza (zaokrąglone do 5 miejsc po przecinku)
        self.entry_lat.delete(0, tk.END)
        self.entry_lat.insert(0, str(round(lat, 5)))

        self.entry_lon.delete(0, tk.END)
        self.entry_lon.insert(0, str(round(lon, 5)))

        self.entry_elev.delete(0, tk.END)
        self.entry_elev.insert(0, "Pobieranie...")

        # 3. Uruchomienie pobierania wysokości w osobnym wątku!
        thread = threading.Thread(target=self.pobierz_wysokosc, args=(lat, lon))
        thread.daemon = True  # Wątek zginie, gdy zamkniemy aplikację
        thread.start()

    def pobierz_wysokosc(self, lat, lon):
        """Odpytuje otwarte API topograficzne o wysokość n.p.m."""
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
        try:
            # Ustawiamy limit czasu (timeout), by nie czekać w nieskończoność
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                dane = response.json()
                wysokosc = dane['results'][0]['elevation']

                # Aktualizacja GUI (musimy to zrobić ostrożnie, wracając do głównego wątku)
                self.entry_elev.delete(0, tk.END)
                self.entry_elev.insert(0, str(float(wysokosc)))
            else:
                self.ustaw_domyslna_wysokosc()
        except requests.RequestException:
            # W razie braku internetu lub awarii serwera
            self.ustaw_domyslna_wysokosc()

    def ustaw_domyslna_wysokosc(self):
        self.entry_elev.delete(0, tk.END)
        self.entry_elev.insert(0, "100.0")

    def zbierz_i_wyslij(self):
        """Zbiera dane z formularza, waliduje i wysyła do głównego okna aplikacji."""
        try:
            data_str = self.entry_date.get().split("-")
            rok, miesiac, dzien = int(data_str[0]), int(data_str[1]), int(data_str[2])
            dni = int(self.entry_days.get())

            lat_dd = float(self.entry_lat.get())
            lon_dd = float(self.entry_lon.get())

            try:
                elev = float(self.entry_elev.get())
            except ValueError:
                elev = 100.0  # Zabezpieczenie, gdyby API wpisało "Pobieranie..." i użytkownik kliknął START

            konfiguracja = {
                "rok": rok,
                "miesiac": miesiac,
                "dzien": dzien,
                "dni_do_analizy": dni,
                "lat_dd": lat_dd,
                "lon_dd": lon_dd,
                "elev": elev
            }

            self.on_start_callback(konfiguracja)

        except Exception as e:
            messagebox.showerror("Błąd danych", f"Sprawdź poprawność wprowadzonych danych.\nSzczegóły: {e}")