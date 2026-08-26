import tkinter as tk
from tkinter import ttk, messagebox
import tkintermapview
import requests
import threading
import datetime
from timezonefinder import TimezoneFinder


class StartPanel(tk.Frame):
    def __init__(self, parent, on_start_callback):
        super().__init__(parent)
        self.on_start_callback = on_start_callback
        self.znacznik = None
        self.tf = TimezoneFinder()

        # Inicjalizacja słownika zmiennych logicznych dla 110 obiektów Messiera
        self.dso_vars = {f"M{i}": tk.BooleanVar(value=False) for i in range(1, 111)}

        self.setup_ui()

    def setup_ui(self):
        panel_lewy = tk.Frame(self, width=280)
        panel_lewy.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        panel_prawy = tk.Frame(self)
        panel_prawy.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(panel_lewy, text="Parametry Obliczeń", font=("Helvetica", 12, "bold")).pack(pady=(0, 15))

        # Zakres Czasowy
        ramka_czasu = tk.LabelFrame(panel_lewy, text="Zakres Czasowy")
        ramka_czasu.pack(fill=tk.X, pady=5)

        tk.Label(ramka_czasu, text="Data startu (RRRR-MM-DD):").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.entry_date = tk.Entry(ramka_czasu)

        # Zczytanie obecnej daty z systemu i sformatowanie na wzór RRRR-MM-DD
        dzisiejsza_data = datetime.date.today().strftime('%Y-%m-%d')
        self.entry_date.insert(0, dzisiejsza_data)

        self.entry_date.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(ramka_czasu, text="Liczba dni do wyliczenia:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.entry_days = tk.Entry(ramka_czasu)
        self.entry_days.insert(0, "7")
        self.entry_days.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(ramka_czasu, text="Krok dla planet (1-20 dni):").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.entry_krok = tk.Spinbox(ramka_czasu, from_=1, to=20, width=18)
        self.entry_krok.delete(0, tk.END)
        self.entry_krok.insert(0, "2")
        self.entry_krok.pack(fill=tk.X, padx=5, pady=(2, 10))

        # --- NOWA RAMKA: Obiekty DSO ---
        ramka_dso = tk.LabelFrame(panel_lewy, text="Katalog Messiera (DSO)")
        ramka_dso.pack(fill=tk.X, pady=5)

        btn_dso = tk.Button(ramka_dso, text="Wybierz obiekty DSO", command=self.otworz_okno_dso)
        btn_dso.pack(fill=tk.X, padx=5, pady=5)

        self.lbl_dso_info = tk.Label(ramka_dso, text="Wybrano obiektów: 0", fg="blue", font=("Helvetica", 9, "bold"))
        self.lbl_dso_info.pack(pady=(0, 5))

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
        self.mapa.set_zoom(6)
        self.mapa.set_position(52.0691, 19.4805)
        self.mapa.add_right_click_menu_command(label="Ustaw punkt obserwacji", command=self.ustaw_punkt_z_mapy,
                                               pass_coords=True)

        self.rysuj_siatke(co_ile_stopni=15)

    def rysuj_siatke(self, co_ile_stopni=15):
        kolor_linii = "#808080"
        for lat in range(-75, 90, co_ile_stopni):
            sciezka_lat = [(lat, lon) for lon in range(-180, 181, 5)]
            self.mapa.set_path(sciezka_lat, color=kolor_linii, width=1)
        for lon in range(-180, 181, co_ile_stopni):
            sciezka_lon = [(lat, lon) for lat in range(-85, 86, 5)]
            self.mapa.set_path(sciezka_lon, color=kolor_linii, width=1)

    # --- METODA OTWIERAJĄCA OKIENKO WYBORU DSO ---
    def otworz_okno_dso(self):
        okno = tk.Toplevel(self)
        okno.title("Wybierz obiekty Messiera")
        # Zmieniamy rozmiar okna na dużo szersze (850 pikseli), żeby pomieścić 11 kolumn
        okno.geometry("850x400")
        okno.transient(self)  # Okienko "przyklejone" do okna głównego
        okno.grab_set()  # Blokuje klikanie w inne elementy, póki okno jest otwarte

        tk.Label(okno, text="Zaznacz obiekty do wyliczeń:", font=("Helvetica", 10, "bold")).pack(pady=10)

        # Kontenery dla przewijanej ramki
        ramka_glowna = tk.Frame(okno)
        ramka_glowna.pack(fill=tk.BOTH, expand=True, padx=10)

        płótno = tk.Canvas(ramka_glowna)
        suwak = ttk.Scrollbar(ramka_glowna, orient="vertical", command=płótno.yview)
        ramka_przewijana = tk.Frame(płótno)

        ramka_przewijana.bind(
            "<Configure>",
            lambda e: płótno.configure(scrollregion=płótno.bbox("all"))
        )

        płótno.create_window((0, 0), window=ramka_przewijana, anchor="nw")
        płótno.configure(yscrollcommand=suwak.set)

        płótno.pack(side="left", fill="both", expand=True)
        suwak.pack(side="right", fill="y")

        # Rysowanie 110 checkboxów w 11 kolumnach (idealnie 10 wierszy!)
        for i in range(1, 111):
            nazwa = f"M{i}"
            cb = tk.Checkbutton(ramka_przewijana, text=nazwa, variable=self.dso_vars[nazwa])
            wiersz = (i - 1) // 11  # Dzielenie całkowite przez 11 określa wiersz
            kolumna = (i - 1) % 11  # Reszta z dzielenia przez 11 określa kolumnę

            # Zmniejszony odstęp (padx=8), aby checkboxy zgrabnie leżały obok siebie
            cb.grid(row=wiersz, column=kolumna, sticky="w", padx=8, pady=5)

        def zatwierdz_i_zamknij():
            ilosc = sum(1 for var in self.dso_vars.values() if var.get())
            self.lbl_dso_info.config(text=f"Wybrano obiektów: {ilosc}")
            okno.destroy()

        btn_ok = tk.Button(okno, text="Zapisz i Zamknij", command=zatwierdz_i_zamknij, bg="#4CAF50", fg="white",
                           font=("Helvetica", 10, "bold"))
        btn_ok.pack(fill=tk.X, padx=20, pady=15)

    # -----------------------------------------------

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

        strefa_str = self.tf.timezone_at(lat=lat, lng=lon)
        if not strefa_str:
            strefa_str = "UTC"
        self.lbl_strefa.config(text=strefa_str)

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

            # --- POBIERAMY ZAZNACZONE OBIEKTY DSO ---
            wybrane_dso = [nazwa for nazwa, zmienna in self.dso_vars.items() if zmienna.get()]

            konfiguracja = {
                "rok": rok,
                "miesiac": miesiac,
                "dzien": dzien,
                "dni_do_analizy": dni,
                "lat_dd": lat_dd,
                "lon_dd": lon_dd,
                "elev": elev,
                "timezone": strefa_str,
                "krok_planety": krok,
                "obiekty_dso": wybrane_dso  # <-- Paczka leci do kontrolera!
            }

            self.on_start_callback(konfiguracja)

        except Exception as e:
            messagebox.showerror("Błąd danych", f"Sprawdź poprawność wprowadzonych danych.\nSzczegóły: {e}")