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

        # Zmienne logiczne dla wyboru zjawisk
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
        panel_lewy = tk.Frame(self, width=280)
        panel_lewy.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        panel_prawy = tk.Frame(self)
        panel_prawy.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(panel_lewy, text="Parametry Obliczeń", font=("Helvetica", 12, "bold")).pack(pady=(0, 5))

        # --- ZAKRES CZASOWY ---
        ramka_czasu = tk.LabelFrame(panel_lewy, text="Zakres Czasowy")
        ramka_czasu.pack(fill=tk.X, pady=5)

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

        # --- WYBÓR ZJAWISK ---
        ramka_filtry = tk.LabelFrame(panel_lewy, text="Wybór Zjawisk")
        ramka_filtry.pack(fill=tk.X, pady=5)

        tk.Checkbutton(ramka_filtry, text="Fazy Księżyca i zaćmienia",
                       variable=self.zjawiska_vars["fazy_zacmienia"]).pack(anchor=tk.W, padx=5)
        tk.Checkbutton(ramka_filtry, text="Pory roku i roje meteorów", variable=self.zjawiska_vars["pory_roje"]).pack(
            anchor=tk.W, padx=5)
        tk.Checkbutton(ramka_filtry, text="Ekstrema (Perygeum, itp.)", variable=self.zjawiska_vars["ekstrema"]).pack(
            anchor=tk.W, padx=5)
        tk.Checkbutton(ramka_filtry, text="Koniunkcje (Słońce) i opozycje",
                       variable=self.zjawiska_vars["slonce_planety"]).pack(anchor=tk.W, padx=5)
        tk.Checkbutton(ramka_filtry, text="Elongacje i retrogradacje", variable=self.zjawiska_vars["elong_retro"]).pack(
            anchor=tk.W, padx=5)
        tk.Checkbutton(ramka_filtry, text="Zakrycia i Koniunkcje (UWAGA WOLNE)", variable=self.zjawiska_vars["zakrycia"]).pack(
            anchor=tk.W, padx=5)

        # --- DSO ---
        ramka_dso = tk.LabelFrame(panel_lewy, text="Katalog Messiera (DSO)")
        ramka_dso.pack(fill=tk.X, pady=5)
        tk.Button(ramka_dso, text="Wybierz obiekty DSO", command=self.otworz_okno_dso).pack(fill=tk.X, padx=5, pady=5)
        self.lbl_dso_info = tk.Label(ramka_dso, text="Wybrano obiektów: 0", fg="blue", font=("Helvetica", 9, "bold"))
        self.lbl_dso_info.pack(pady=(0, 5))

        # --- LOKALIZACJA ---
        ramka_geo = tk.LabelFrame(panel_lewy, text="Lokalizacja Obserwatora")
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

        tk.Button(panel_lewy, text="Generuj Efemerydy", command=self.zbierz_i_wyslij, bg="#4CAF50",
                  fg="white", font=("Helvetica", 10, "bold")).pack(fill=tk.X, pady=10, ipady=5)

        # Mapa
        self.mapa = tkintermapview.TkinterMapView(panel_prawy, corner_radius=5)
        self.mapa.pack(fill=tk.BOTH, expand=True)
        self.mapa.set_zoom(6)
        self.mapa.set_position(52.0691, 19.4805)
        self.mapa.add_right_click_menu_command(label="Ustaw punkt obserwacji", command=self.ustaw_punkt_z_mapy,
                                               pass_coords=True)
        self.rysuj_siatke(co_ile_stopni=15)

    def rysuj_siatke(self, co_ile_stopni=15):
        for lat in range(-75, 90, co_ile_stopni):
            self.mapa.set_path([(lat, lon) for lon in range(-180, 181, 5)], color="#808080", width=1)
        for lon in range(-180, 181, co_ile_stopni):
            self.mapa.set_path([(lat, lon) for lat in range(-85, 86, 5)], color="#808080", width=1)

    def otworz_okno_dso(self):
        okno = tk.Toplevel(self)
        okno.title("Wybierz obiekty Messiera")
        okno.geometry("850x400")
        okno.transient(self)
        okno.grab_set()

        ramka_glowna = tk.Frame(okno)
        ramka_glowna.pack(fill=tk.BOTH, expand=True, padx=10)

        płótno = tk.Canvas(ramka_glowna)
        suwak = ttk.Scrollbar(ramka_glowna, orient="vertical", command=płótno.yview)
        ramka_przewijana = tk.Frame(płótno)

        ramka_przewijana.bind("<Configure>", lambda e: płótno.configure(scrollregion=płótno.bbox("all")))
        płótno.create_window((0, 0), window=ramka_przewijana, anchor="nw")
        płótno.configure(yscrollcommand=suwak.set)

        płótno.pack(side="left", fill="both", expand=True)
        suwak.pack(side="right", fill="y")

        for i in range(1, 111):
            cb = tk.Checkbutton(ramka_przewijana, text=f"M{i}", variable=self.dso_vars[f"M{i}"])
            cb.grid(row=(i - 1) // 11, column=(i - 1) % 11, sticky="w", padx=8, pady=5)

        def zatwierdz_i_zamknij():
            self.lbl_dso_info.config(text=f"Wybrano obiektów: {sum(1 for v in self.dso_vars.values() if v.get())}")
            okno.destroy()

        tk.Button(okno, text="Zapisz i Zamknij", command=zatwierdz_i_zamknij, bg="#4CAF50", fg="white",
                  font=("Helvetica", 10, "bold")).pack(fill=tk.X, padx=20, pady=15)

    def ustaw_punkt_z_mapy(self, coords):
        lat, lon = coords
        if self.znacznik: self.znacznik.delete()
        self.znacznik = self.mapa.set_marker(lat, lon, text="Obserwator")

        self.entry_lat.delete(0, tk.END);
        self.entry_lat.insert(0, str(round(lat, 5)))
        self.entry_lon.delete(0, tk.END);
        self.entry_lon.insert(0, str(round(lon, 5)))
        self.entry_elev.delete(0, tk.END);
        self.entry_elev.insert(0, "Pobieranie...")

        strefa_str = self.tf.timezone_at(lat=lat, lng=lon)
        self.lbl_strefa.config(text=strefa_str if strefa_str else "UTC")
        threading.Thread(target=self.pobierz_wysokosc, args=(lat, lon), daemon=True).start()

    def pobierz_wysokosc(self, lat, lon):
        try:
            r = requests.get(f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}", timeout=5)
            self.entry_elev.delete(0, tk.END)
            self.entry_elev.insert(0,
                                   str(float(r.json()['results'][0]['elevation'])) if r.status_code == 200 else "100.0")
        except:
            self.entry_elev.delete(0, tk.END);
            self.entry_elev.insert(0, "100.0")

    def zbierz_i_wyslij(self):
        try:
            rok, miesiac, dzien = map(int, self.entry_date.get().split("-"))

            try:
                okienko_val = float(self.entry_okienko.get().replace(',', '.'))
            except ValueError:
                okienko_val = 5.0

            try:
                elev = float(self.entry_elev.get())
            except ValueError:
                elev = 100.0

            krok = int(self.entry_krok.get())

            zjawiska_konf = {k: v.get() for k, v in self.zjawiska_vars.items()}

            konfiguracja = {
                "rok": rok, "miesiac": miesiac, "dzien": dzien,
                "dni_do_analizy": int(self.entry_days.get()),
                "lat_dd": float(self.entry_lat.get()),
                "lon_dd": float(self.entry_lon.get()),
                "elev": elev,
                "timezone": self.lbl_strefa.cget("text"),
                "krok_planety": krok,
                "okienko_koniunkcji": okienko_val,
                "obiekty_dso": [n for n, v in self.dso_vars.items() if v.get()],
                "zjawiska": zjawiska_konf
            }

            self.on_start_callback(konfiguracja)

        except Exception as e:
            messagebox.showerror("Błąd danych", f"Sprawdź poprawność danych.\nSzczegóły: {e}")