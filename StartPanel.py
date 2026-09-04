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

        self.dso_vars = {f"M{i}": tk.BooleanVar(value=False) for i in range(1, 111)}

        self.zjawiska_vars = {
            "fazy_zacmienia": tk.BooleanVar(value=True),
            "pory_roje": tk.BooleanVar(value=True),
            "ekstrema": tk.BooleanVar(value=True),
            "slonce_planety": tk.BooleanVar(value=True),
            "elong_retro": tk.BooleanVar(value=True),
            "zakrycia": tk.BooleanVar(value=True)
        }

        self.setup_ui()

    def setup_ui(self):
        panel_lewy = tk.Frame(self, width=320)
        panel_lewy.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        panel_prawy = tk.Frame(self)
        panel_prawy.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(panel_lewy, text="Parametry Obliczeń", font=("Helvetica", 12, "bold")).pack(pady=(0, 5))

        self.notebook = ttk.Notebook(panel_lewy)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5)

        tab_efemerydy = ttk.Frame(self.notebook)
        tab_kosmogram = ttk.Frame(self.notebook)

        self.notebook.add(tab_efemerydy, text="Efemerydy")
        self.notebook.add(tab_kosmogram, text="Kosmogram")

        # --- ZAKŁADKA 1: EFEMERYDY ---
        ramka_czasu = tk.LabelFrame(tab_efemerydy, text="Zakres Czasowy")
        ramka_czasu.pack(fill=tk.X, pady=5, padx=5)

        tk.Label(ramka_czasu, text="Data startu (RRRR-MM-DD):").pack(anchor=tk.W, padx=5, pady=(2, 0))
        self.entry_date = tk.Entry(ramka_czasu)
        self.entry_date.insert(0, datetime.date.today().strftime('%Y-%m-%d'))
        self.entry_date.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(ramka_czasu, text="Maks. separacja koniunkcji [°]:").pack(anchor=tk.W, padx=5, pady=(2, 0))
        self.entry_okienko = tk.Entry(ramka_czasu)
        self.entry_okienko.insert(0, "5.0")
        self.entry_okienko.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(ramka_czasu, text="Liczba dni:").pack(anchor=tk.W, padx=5, pady=(2, 0))
        self.entry_days = tk.Entry(ramka_czasu)
        self.entry_days.insert(0, "7")
        self.entry_days.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(ramka_czasu, text="Krok dla planet:").pack(anchor=tk.W, padx=5, pady=(2, 0))
        self.entry_krok = tk.Spinbox(ramka_czasu, from_=1, to=20, width=18)
        self.entry_krok.delete(0, tk.END)
        self.entry_krok.insert(0, "2")
        self.entry_krok.pack(fill=tk.X, padx=5, pady=(2, 5))

        ramka_filtry = tk.LabelFrame(tab_efemerydy, text="Wybór Zjawisk")
        ramka_filtry.pack(fill=tk.X, pady=5, padx=5)

        tk.Checkbutton(ramka_filtry, text="Fazy Księżyca i zaćmienia", variable=self.zjawiska_vars["fazy_zacmienia"]).pack(anchor=tk.W, padx=5)
        tk.Checkbutton(ramka_filtry, text="Pory roku i roje meteorów", variable=self.zjawiska_vars["pory_roje"]).pack(anchor=tk.W, padx=5)
        tk.Checkbutton(ramka_filtry, text="Ekstrema (Perygeum, itp.)", variable=self.zjawiska_vars["ekstrema"]).pack(anchor=tk.W, padx=5)
        tk.Checkbutton(ramka_filtry, text="Koniunkcje (Słońce) i opozycje", variable=self.zjawiska_vars["slonce_planety"]).pack(anchor=tk.W, padx=5)
        tk.Checkbutton(ramka_filtry, text="Elongacje i retrogradacje", variable=self.zjawiska_vars["elong_retro"]).pack(anchor=tk.W, padx=5)
        tk.Checkbutton(ramka_filtry, text="Zakrycia i Koniunkcje(UWAGA: WOLNE!)", variable=self.zjawiska_vars["zakrycia"]).pack(anchor=tk.W, padx=5)

        ramka_dso = tk.LabelFrame(tab_efemerydy, text="Katalog Messiera (DSO)")
        ramka_dso.pack(fill=tk.X, pady=5, padx=5)
        tk.Button(ramka_dso, text="Wybierz obiekty DSO", command=self.otworz_okno_dso).pack(fill=tk.X, padx=5, pady=5)
        self.lbl_dso_info = tk.Label(ramka_dso, text="Wybrano obiektów: 0", fg="blue", font=("Helvetica", 9, "bold"))
        self.lbl_dso_info.pack(pady=(0, 5))

        # --- ZAKŁADKA 2: KOSMOGRAM ---
        ramka_urodzeniowa = tk.LabelFrame(tab_kosmogram, text="Dane Urodzeniowe")
        ramka_urodzeniowa.pack(fill=tk.X, pady=5, padx=5)

        tk.Label(ramka_urodzeniowa, text="Data (RRRR-MM-DD):").pack(anchor=tk.W, padx=5, pady=(2, 0))
        self.entry_urodz_data = tk.Entry(ramka_urodzeniowa)
        self.entry_urodz_data.insert(0, "2000-01-01")
        self.entry_urodz_data.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(ramka_urodzeniowa, text="Czas (GG:MM):").pack(anchor=tk.W, padx=5, pady=(2, 0))
        self.entry_urodz_czas = tk.Entry(ramka_urodzeniowa)
        self.entry_urodz_czas.insert(0, "12:00")
        self.entry_urodz_czas.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(ramka_urodzeniowa, text="System domów:").pack(anchor=tk.W, padx=5, pady=(2, 0))
        self.combo_domy = ttk.Combobox(ramka_urodzeniowa, values=["Placidus", "Koch", "Regiomontanus", "Campanus", "Równe (Equal)"])
        self.combo_domy.set("Placidus")
        self.combo_domy.pack(fill=tk.X, padx=5, pady=(2, 5))

        ramka_orby = tk.LabelFrame(tab_kosmogram, text="Tolerancje Aspektów (Orby [°])")
        ramka_orby.pack(fill=tk.X, pady=5, padx=5)

        tk.Label(ramka_orby, text="Koniunkcja:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.orb_kon = tk.Entry(ramka_orby, width=6)
        self.orb_kon.insert(0, "8.0")
        self.orb_kon.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(ramka_orby, text="Sekstyl:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.orb_sek = tk.Entry(ramka_orby, width=6)
        self.orb_sek.insert(0, "6.0")
        self.orb_sek.grid(row=0, column=3, padx=5, pady=2)

        tk.Label(ramka_orby, text="Kwadratura:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.orb_kwa = tk.Entry(ramka_orby, width=6)
        self.orb_kwa.insert(0, "8.0")
        self.orb_kwa.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(ramka_orby, text="Trygon:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.orb_try = tk.Entry(ramka_orby, width=6)
        self.orb_try.insert(0, "8.0")
        self.orb_try.grid(row=1, column=3, padx=5, pady=2)

        tk.Label(ramka_orby, text="Opozycja:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.orb_opo = tk.Entry(ramka_orby, width=6)
        self.orb_opo.insert(0, "8.0")
        self.orb_opo.grid(row=2, column=1, padx=5, pady=2)

        # --- LOKALIZACJA ---
        ramka_geo = tk.LabelFrame(panel_lewy, text="Lokalizacja (Obserwator / Urodzenie)")
        ramka_geo.pack(fill=tk.X, pady=5)

        tk.Label(ramka_geo, text="Szerokość:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.entry_lat = tk.Entry(ramka_geo, width=12)
        self.entry_lat.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(ramka_geo, text="Długość:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.entry_lon = tk.Entry(ramka_geo, width=12)
        self.entry_lon.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(ramka_geo, text="Wys (m):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.entry_elev = tk.Entry(ramka_geo, width=12)
        self.entry_elev.insert(0, "100.0")
        self.entry_elev.grid(row=2, column=1, padx=5, pady=2)

        self.lbl_strefa = tk.Label(ramka_geo, text="Europe/Warsaw", fg="blue", font=("Helvetica", 8, "bold"))
        self.lbl_strefa.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        tk.Button(panel_lewy, text="Generuj", command=self.zbierz_i_wyslij, bg="#4CAF50",
                  fg="white", font=("Helvetica", 12, "bold")).pack(fill=tk.X, pady=10, ipady=5)

        self.mapa = tkintermapview.TkinterMapView(panel_prawy, corner_radius=5)
        self.mapa.pack(fill=tk.BOTH, expand=True)
        self.mapa.set_zoom(6)
        self.mapa.set_position(52.0691, 19.4805)
        self.mapa.add_right_click_menu_command(label="Ustaw punkt obserwacji", command=self.ustaw_punkt_z_mapy, pass_coords=True)
        self.rysuj_siatke(co_ile_stopni=15)

    def rysuj_siatke(self, co_ile_stopni=15):
        for lat in range(-75, 90, co_ile_stopni):
            self.mapa.set_path([(lat, lon) for lon in range(-180, 181, 5)], color="#808080", width=1)
        for lon in range(-180, 181, co_ile_stopni):
            self.mapa.set_path([(lat, lon) for lat in range(-85, 86, 5)], color="#808080", width=1)

    def otworz_okno_dso(self):
        okno = tk.Toplevel(self)
        okno.title("Wybierz obiekty Messiera")
        okno.geometry("850x450")
        okno.transient(self)
        okno.grab_set()

        ramka_glowna = tk.Frame(okno)
        ramka_glowna.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # GÓRNA RAMKA NA MASTER CHECKBOXY
        ramka_top = tk.Frame(ramka_glowna)
        ramka_top.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))

        # Obiekty przyporządkowane do półkul na podstawie deklinacji (Dec > 0 i Dec < 0)
        polnocne = [1, 3, 5, 13, 15, 27, 29, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 44, 45, 49, 51, 52, 53, 56, 57, 58, 59, 60, 61, 63, 64, 65, 66, 67, 71, 74, 76, 78, 81, 82, 84, 85, 86, 87, 88, 89, 90, 91, 92, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 105, 106, 108, 109, 110]
        poludniowe = [2, 4, 6, 7, 8, 9, 10, 11, 12, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 28, 30, 41, 42, 43, 46, 47, 48, 50, 54, 55, 62, 68, 69, 70, 72, 73, 75, 77, 79, 80, 83, 93, 104, 107]

        var_pol = tk.BooleanVar(value=all(self.dso_vars[f"M{i}"].get() for i in polnocne))
        var_pld = tk.BooleanVar(value=all(self.dso_vars[f"M{i}"].get() for i in poludniowe))
        var_wsz = tk.BooleanVar(value=all(self.dso_vars[f"M{i}"].get() for i in range(1, 111)))

        def przelacz_wszystkie():
            stan = var_wsz.get()
            for i in range(1, 111): self.dso_vars[f"M{i}"].set(stan)
            var_pol.set(stan)
            var_pld.set(stan)

        def przelacz_polnocne():
            stan = var_pol.get()
            for i in polnocne: self.dso_vars[f"M{i}"].set(stan)
            var_wsz.set(all(self.dso_vars[f"M{i}"].get() for i in range(1, 111)))

        def przelacz_poludniowe():
            stan = var_pld.get()
            for i in poludniowe: self.dso_vars[f"M{i}"].set(stan)
            var_wsz.set(all(self.dso_vars[f"M{i}"].get() for i in range(1, 111)))

        cb_pol = tk.Checkbutton(ramka_top, text="Północne (Dec > 0°)", variable=var_pol, command=przelacz_polnocne, font=("Helvetica", 9, "bold"))
        cb_pol.pack(side=tk.LEFT, expand=True)

        cb_wsz = tk.Checkbutton(ramka_top, text="Wszystkie (M1-M110)", variable=var_wsz, command=przelacz_wszystkie, font=("Helvetica", 9, "bold"))
        cb_wsz.pack(side=tk.LEFT, expand=True)

        cb_pld = tk.Checkbutton(ramka_top, text="Południowe (Dec < 0°)", variable=var_pld, command=przelacz_poludniowe, font=("Helvetica", 9, "bold"))
        cb_pld.pack(side=tk.LEFT, expand=True)

        # ŚRODKOWA RAMKA NA PRZEWIJANE CHECKBOXY
        ramka_srodek = tk.Frame(ramka_glowna)
        ramka_srodek.pack(fill=tk.BOTH, expand=True)

        płótno = tk.Canvas(ramka_srodek)
        suwak = ttk.Scrollbar(ramka_srodek, orient="vertical", command=płótno.yview)
        ramka_przewijana = tk.Frame(płótno)

        ramka_przewijana.bind("<Configure>", lambda e: płótno.configure(scrollregion=płótno.bbox("all")))
        płótno.create_window((0, 0), window=ramka_przewijana, anchor="nw")
        płótno.configure(yscrollcommand=suwak.set)

        płótno.pack(side="left", fill="both", expand=True)
        suwak.pack(side="right", fill="y")

        # GENEROWANIE SIATKI CHECKBOXÓW
        def zaktualizuj_master_checkboxy():
            var_pol.set(all(self.dso_vars[f"M{i}"].get() for i in polnocne))
            var_pld.set(all(self.dso_vars[f"M{i}"].get() for i in poludniowe))
            var_wsz.set(all(self.dso_vars[f"M{i}"].get() for i in range(1, 111)))

        for i in range(1, 111):
            cb = tk.Checkbutton(ramka_przewijana, text=f"M{i}", variable=self.dso_vars[f"M{i}"], command=zaktualizuj_master_checkboxy)
            cb.grid(row=(i - 1) // 11, column=(i - 1) % 11, sticky="w", padx=8, pady=5)

        # ZATWIERDZENIE
        def zatwierdz_i_zamknij():
            self.lbl_dso_info.config(text=f"Wybrano obiektów: {sum(1 for v in self.dso_vars.values() if v.get())}")
            okno.destroy()

        tk.Button(okno, text="Zapisz i Zamknij", command=zatwierdz_i_zamknij, bg="#4CAF50", fg="white",
                  font=("Helvetica", 10, "bold")).pack(fill=tk.X, padx=20, pady=15)

    def ustaw_punkt_z_mapy(self, coords):
        lat, lon = coords
        if self.znacznik: self.znacznik.delete()
        self.znacznik = self.mapa.set_marker(lat, lon, text="Zaznaczone Miejsce")

        self.entry_lat.delete(0, tk.END)
        self.entry_lat.insert(0, str(round(lat, 5)))
        self.entry_lon.delete(0, tk.END)
        self.entry_lon.insert(0, str(round(lon, 5)))
        self.entry_elev.delete(0, tk.END)
        self.entry_elev.insert(0, "Pobieranie...")

        strefa_str = self.tf.timezone_at(lat=lat, lng=lon)
        self.lbl_strefa.config(text=strefa_str if strefa_str else "UTC")
        threading.Thread(target=self.pobierz_wysokosc, args=(lat, lon), daemon=True).start()

    def pobierz_wysokosc(self, lat, lon):
        try:
            r = requests.get(f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}", timeout=5)
            self.entry_elev.delete(0, tk.END)
            self.entry_elev.insert(0, str(float(r.json()['results'][0]['elevation'])) if r.status_code == 200 else "100.0")
        except:
            self.entry_elev.delete(0, tk.END)
            self.entry_elev.insert(0, "100.0")

    def zbierz_i_wyslij(self):
        try:
            aktywna_zakladka = self.notebook.index(self.notebook.select())
            tryb = "efemerydy" if aktywna_zakladka == 0 else "kosmogram"

            rok, miesiac, dzien = map(int, self.entry_date.get().split("-"))
            try:
                okienko_val = float(self.entry_okienko.get().replace(',', '.'))
            except ValueError:
                okienko_val = 5.0

            try:
                elev = float(self.entry_elev.get())
            except ValueError:
                elev = 100.0

            zjawiska_konf = {k: v.get() for k, v in self.zjawiska_vars.items()}

            def bezpieczny_float(val, domyslna):
                try: return float(val.replace(',', '.'))
                except ValueError: return domyslna

            konfiguracja = {
                "tryb": tryb,
                "rok": rok, "miesiac": miesiac, "dzien": dzien,
                "dni_do_analizy": int(self.entry_days.get()),
                "lat_dd": float(self.entry_lat.get()),
                "lon_dd": float(self.entry_lon.get()),
                "elev": elev,
                "timezone": self.lbl_strefa.cget("text"),
                "krok_planety": int(self.entry_krok.get()),
                "okienko_koniunkcji": okienko_val,
                "obiekty_dso": [n for n, v in self.dso_vars.items() if v.get()],
                "zjawiska": zjawiska_konf,
                "urodz_data": self.entry_urodz_data.get(),
                "urodz_czas": self.entry_urodz_czas.get(),
                "sys_domow": self.combo_domy.get(),
                "orby": {
                    "Koniunkcja": bezpieczny_float(self.orb_kon.get(), 8.0),
                    "Sekstyl": bezpieczny_float(self.orb_sek.get(), 6.0),
                    "Kwadratura": bezpieczny_float(self.orb_kwa.get(), 8.0),
                    "Trygon": bezpieczny_float(self.orb_try.get(), 8.0),
                    "Opozycja": bezpieczny_float(self.orb_opo.get(), 8.0)
                }
            }

            self.on_start_callback(konfiguracja)

        except Exception as e:
            messagebox.showerror("Błąd danych", f"Sprawdź poprawność danych.\nSzczegóły: {e}")