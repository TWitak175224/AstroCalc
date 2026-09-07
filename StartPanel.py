import tkinter as tk
from tkinter import ttk, messagebox
import tkintermapview
import requests
import threading
import datetime
import json
import os
from timezonefinder import TimezoneFinder

try:
    from tkcalendar import Calendar

    TKCALENDAR_DOSTEPNY = True
except ImportError:
    TKCALENDAR_DOSTEPNY = False


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
        panel_lewy = tk.Frame(self, width=330)
        panel_lewy.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        panel_lewy.pack_propagate(False)

        panel_prawy = tk.Frame(self)
        panel_prawy.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(panel_lewy, text="Parametry Obliczeń", font=("Helvetica", 12, "bold")).pack(pady=(0, 5))

        tk.Button(panel_lewy, text="Generuj", command=self.zbierz_i_wyslij, bg="#4CAF50",
                  fg="white", font=("Helvetica", 12, "bold")).pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0), ipady=5)

        ramka_geo = tk.LabelFrame(panel_lewy, text="Lokalizacja (Obserwator / Urodzenie)")
        ramka_geo.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 5))

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

        self.notebook = ttk.Notebook(panel_lewy)
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)

        tab_efemerydy = ttk.Frame(self.notebook)
        tab_kosmogram = ttk.Frame(self.notebook)

        self.notebook.add(tab_efemerydy, text="Efemerydy")
        self.notebook.add(tab_kosmogram, text="Kosmogram")

        # ==========================================
        # ZAKŁADKA 1: EFEMERYDY
        # ==========================================
        ramka_czasu = tk.LabelFrame(tab_efemerydy, text="Zakres Czasowy")
        ramka_czasu.pack(fill=tk.X, pady=5, padx=5)
        ramka_czasu.columnconfigure(1, weight=1)

        tk.Label(ramka_czasu, text="Data startu:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)

        # --- Zintegrowane pole daty z przyciskiem do ładnego kalendarza ---
        ramka_daty_efe = tk.Frame(ramka_czasu)
        ramka_daty_efe.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)

        self.entry_date = tk.Entry(ramka_daty_efe)
        self.entry_date.insert(0, datetime.date.today().strftime('%Y-%m-%d'))
        self.entry_date.pack(side=tk.LEFT, fill=tk.X, expand=True)

        if TKCALENDAR_DOSTEPNY:
            btn_cal1 = tk.Button(ramka_daty_efe, text="📅", command=lambda: self.otworz_kalendarz(self.entry_date))
            btn_cal1.pack(side=tk.RIGHT, padx=(5, 0))

        tk.Label(ramka_czasu, text="Liczba dni:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.entry_days = tk.Entry(ramka_czasu)
        self.entry_days.insert(0, "7")
        self.entry_days.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)

        tk.Label(ramka_czasu, text="Krok (planety):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.entry_krok = tk.Spinbox(ramka_czasu, from_=1, to=20)
        self.entry_krok.delete(0, tk.END)
        self.entry_krok.insert(0, "2")
        self.entry_krok.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)

        tk.Label(ramka_czasu, text="Min. koniunkcja [°]:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.entry_okienko = tk.Entry(ramka_czasu)
        self.entry_okienko.insert(0, "5.0")
        self.entry_okienko.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=2)

        ramka_filtry = tk.LabelFrame(tab_efemerydy, text="Wybór Zjawisk")
        ramka_filtry.pack(fill=tk.X, pady=5, padx=5)

        tk.Checkbutton(ramka_filtry, text="Fazy Księżyca i zaćmienia",
                       variable=self.zjawiska_vars["fazy_zacmienia"]).grid(row=0, column=0, sticky=tk.W, padx=5)
        tk.Checkbutton(ramka_filtry, text="Pory roku i roje meteorów", variable=self.zjawiska_vars["pory_roje"]).grid(
            row=1, column=0, sticky=tk.W, padx=5)
        tk.Checkbutton(ramka_filtry, text="Ekstrema (Perygeum, itp.)", variable=self.zjawiska_vars["ekstrema"]).grid(
            row=2, column=0, sticky=tk.W, padx=5)
        tk.Checkbutton(ramka_filtry, text="Koniunkcje i opozycje", variable=self.zjawiska_vars["slonce_planety"]).grid(
            row=3, column=0, sticky=tk.W, padx=5)
        tk.Checkbutton(ramka_filtry, text="Elongacje i retrogradacje", variable=self.zjawiska_vars["elong_retro"]).grid(
            row=4, column=0, sticky=tk.W, padx=5)
        tk.Checkbutton(ramka_filtry, text="Zakrycia planetarne", variable=self.zjawiska_vars["zakrycia"]).grid(row=5,
                                                                                                               column=0,
                                                                                                               sticky=tk.W,
                                                                                                               padx=5)

        ramka_dso = tk.LabelFrame(tab_efemerydy, text="Katalog Messiera (DSO)")
        ramka_dso.pack(fill=tk.X, pady=5, padx=5)

        tk.Button(ramka_dso, text="Wybierz obiekty DSO do raportu", command=self.otworz_okno_dso).pack(fill=tk.X,
                                                                                                       padx=5, pady=5)

        self.lbl_dso_info = tk.Label(ramka_dso, text="Wybrano obiektów: 0", fg="blue", font=("Helvetica", 9, "bold"))
        self.lbl_dso_info.pack(pady=(0, 2))

        tk.Button(tab_efemerydy, text="Pomoc - Efemerydy",
                  command=lambda: self.otworz_pomoc("pomoc_efemerydy.json", "Pomoc - Kalendarium i Efemerydy"),
                  bg="#2196F3", fg="white", font=("Helvetica", 9, "bold")).pack(fill=tk.X, padx=5, pady=(5, 5))

        # ==========================================
        # ZAKŁADKA 2: KOSMOGRAM
        # ==========================================
        ramka_urodzeniowa = tk.LabelFrame(tab_kosmogram, text="Dane Urodzeniowe")
        ramka_urodzeniowa.pack(fill=tk.X, pady=5, padx=5)
        ramka_urodzeniowa.columnconfigure(1, weight=1)

        tk.Label(ramka_urodzeniowa, text="Data urodzenia:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)

        # --- Zintegrowane pole daty w kosmogramie ---
        ramka_daty_ur = tk.Frame(ramka_urodzeniowa)
        ramka_daty_ur.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)

        self.entry_urodz_data = tk.Entry(ramka_daty_ur)
        self.entry_urodz_data.insert(0, "2000-01-01")
        self.entry_urodz_data.pack(side=tk.LEFT, fill=tk.X, expand=True)

        if TKCALENDAR_DOSTEPNY:
            btn_cal2 = tk.Button(ramka_daty_ur, text="📅", command=lambda: self.otworz_kalendarz(self.entry_urodz_data))
            btn_cal2.pack(side=tk.RIGHT, padx=(5, 0))

        tk.Label(ramka_urodzeniowa, text="Czas (GG:MM):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ramka_zegar = tk.Frame(ramka_urodzeniowa)
        ramka_zegar.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        self.spin_godz = ttk.Spinbox(ramka_zegar, from_=0, to=23, width=3, format="%02.0f")
        self.spin_godz.set("12")
        self.spin_godz.pack(side=tk.LEFT)
        tk.Label(ramka_zegar, text=" : ", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        self.spin_min = ttk.Spinbox(ramka_zegar, from_=0, to=59, width=3, format="%02.0f")
        self.spin_min.set("00")
        self.spin_min.pack(side=tk.LEFT)

        tk.Label(ramka_urodzeniowa, text="System domów:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.combo_domy = ttk.Combobox(ramka_urodzeniowa,
                                       values=["Placidus", "Koch", "Regiomontanus", "Campanus", "Równe (Equal)"])
        self.combo_domy.set("Placidus")
        self.combo_domy.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)

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

        tk.Button(tab_kosmogram, text="Pomoc - Kosmogram",
                  command=lambda: self.otworz_pomoc("pomoc_kosmogram.json", "Pomoc - Ustawienia Kosmogramu"),
                  bg="#9C27B0", fg="white", font=("Helvetica", 9, "bold")).pack(fill=tk.X, padx=5, pady=(10, 5))

        self.mapa = tkintermapview.TkinterMapView(panel_prawy, corner_radius=5)
        self.mapa.pack(fill=tk.BOTH, expand=True)
        self.mapa.set_zoom(6)
        self.mapa.set_position(52.0691, 19.4805)
        self.mapa.add_right_click_menu_command(label="Ustaw punkt obserwacji", command=self.ustaw_punkt_z_mapy,
                                               pass_coords=True)
        self.rysuj_siatke(co_ile_stopni=15)

        self.wczytaj_ustawienia()

    # --- NOWA METODA: WYSKAKUJĄCY, BEZPIECZNY KALENDARZ ---
    def otworz_kalendarz(self, pole_docelowe):
        okno_kal = tk.Toplevel(self)
        okno_kal.title("Wybierz datę")
        okno_kal.geometry("280x250")
        okno_kal.transient(self)
        okno_kal.grab_set()

        try:
            aktualna = datetime.datetime.strptime(pole_docelowe.get(), "%Y-%m-%d").date()
        except ValueError:
            aktualna = datetime.date.today()

        kalendarz = Calendar(okno_kal, selectmode='day', year=aktualna.year, month=aktualna.month, day=aktualna.day,
                             date_pattern='y-mm-dd', background='#2C3E50', foreground='white', borderwidth=2)
        kalendarz.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

        def zapisz_date():
            pole_docelowe.delete(0, tk.END)
            pole_docelowe.insert(0, kalendarz.get_date())
            okno_kal.destroy()

        tk.Button(okno_kal, text="Wybierz tę datę", command=zapisz_date, bg="#4CAF50", fg="white",
                  font=("Helvetica", 10, "bold")).pack(pady=(0, 10), padx=10, fill=tk.X)

    def otworz_pomoc(self, plik_json, domyslny_tytul):
        okno = tk.Toplevel(self)
        okno.title(domyslny_tytul)
        okno.geometry("500x400")
        okno.transient(self)

        txt = tk.Text(okno, wrap=tk.WORD, font=("Helvetica", 10), padx=15, pady=15, bg="#F9F9F9")
        suwak = ttk.Scrollbar(okno, orient=tk.VERTICAL, command=txt.yview)
        txt.config(yscrollcommand=suwak.set)

        suwak.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tresc = ""
        if os.path.exists(plik_json):
            try:
                with open(plik_json, "r", encoding="utf-8") as f:
                    dane = json.load(f)

                if "tytul" in dane:
                    tresc += f"{dane['tytul']}\n"
                    tresc += "=" * len(dane['tytul']) + "\n\n"

                if "sekcje" in dane:
                    for naglowek, tekst in dane["sekcje"].items():
                        tresc += f"[{naglowek}]\n{tekst}\n\n"
                elif isinstance(dane, dict):
                    for k, v in dane.items():
                        tresc += f"{k}\n{v}\n\n"
                else:
                    tresc = str(dane)
            except Exception as e:
                tresc = f"Wystąpił błąd podczas odczytu pliku {plik_json}:\n{e}"
        else:
            tresc = f"Brak pliku pomocy: {plik_json}\n\nUtwórz ten plik JSON w folderze głównym aplikacji, aby dodać dedykowaną instrukcję."

        txt.insert(tk.END, tresc)
        txt.config(state=tk.DISABLED)

    def rysuj_siatke(self, co_ile_stopni=15):
        for lat in range(-75, 90, co_ile_stopni):
            self.mapa.set_path([(lat, lon) for lon in range(-180, 181, 5)], color="#808080", width=1)
        for lon in range(-180, 181, co_ile_stopni):
            self.mapa.set_path([(lat, lon) for lat in range(-85, 86, 5)], color="#808080", width=1)

    def otworz_katalog_dso(self, parent_window):
        okno = tk.Toplevel(parent_window)
        okno.title("Katalog Obiektów Messiera")
        okno.geometry("800x550")
        okno.transient(parent_window)

        baza_messiera = {}
        if os.path.exists("messier_katalog.json"):
            try:
                with open("messier_katalog.json", "r", encoding="utf-8") as f:
                    baza_messiera = json.load(f)
            except Exception as e:
                print(f"Błąd ładowania jsona: {e}")

        ramka_lista = tk.Frame(okno, width=150)
        ramka_lista.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        ramka_detale = tk.Frame(okno)
        ramka_detale.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        lista = tk.Listbox(ramka_lista, font=("Helvetica", 11))
        suwak = ttk.Scrollbar(ramka_lista, orient=tk.VERTICAL, command=lista.yview)
        lista.config(yscrollcommand=suwak.set)
        suwak.pack(side=tk.RIGHT, fill=tk.Y)
        lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for i in range(1, 111):
            lista.insert(tk.END, f"M{i}")

        lbl_tytul = tk.Label(ramka_detale, text="Wybierz obiekt z listy", font=("Helvetica", 16, "bold"))
        lbl_tytul.pack(pady=(0, 10))

        lbl_zdjecie = tk.Label(ramka_detale, text="[Brak zdjęcia]", bg="#E0E0E0", width=50, height=15)
        lbl_zdjecie.pack(pady=10)

        txt_opis = tk.Text(ramka_detale, wrap=tk.WORD, height=10, font=("Helvetica", 10), bg="#F8F9FA")
        txt_opis.pack(fill=tk.BOTH, expand=True)
        txt_opis.insert(tk.END, "Tutaj pojawi się opis obiektu po jego wybraniu.")
        txt_opis.config(state=tk.DISABLED)

        def on_select(evt):
            if not lista.curselection():
                return
            wybrany = lista.get(lista.curselection())
            dane = baza_messiera.get(wybrany, {})

            nazwa = dane.get("nazwa", "Brak nazwy w bazie")
            opis = dane.get("opis", "Plik messier_katalog.json nie zawiera opisu dla tego obiektu.")
            sciezka_zdjecia = dane.get("zdjecie", "")

            lbl_tytul.config(text=f"{wybrany} - {nazwa}")

            txt_opis.config(state=tk.NORMAL)
            txt_opis.delete(1.0, tk.END)
            txt_opis.insert(tk.END, opis)
            txt_opis.config(state=tk.DISABLED)

            try:
                if sciezka_zdjecia and os.path.exists(sciezka_zdjecia):
                    img = tk.PhotoImage(file=sciezka_zdjecia)
                    lbl_zdjecie.config(image=img, text="", width=0, height=0)

                    # noinspection PyUnresolvedReferences
                    lbl_zdjecie.image = img
                else:
                    lbl_zdjecie.config(image="", text="[Zdjęcie niedostępne]", width=50, height=15)
            except Exception:
                lbl_zdjecie.config(image="", text="[Format nieobsługiwany - użyj .png lub .gif]", width=50, height=15)

        lista.bind("<<ListboxSelect>>", on_select)

    def otworz_okno_dso(self):
        okno = tk.Toplevel(self)
        okno.title("Wybierz obiekty Messiera")
        okno.geometry("850x550")
        okno.transient(self)
        okno.grab_set()

        ramka_glowna = tk.Frame(okno)
        ramka_glowna.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ramka_top = tk.LabelFrame(ramka_glowna, text="Szybkie filtry (czyszczą poprzedni wybór)")
        ramka_top.pack(fill=tk.X, side=tk.TOP, pady=(0, 10), ipady=5)

        ramka_top.columnconfigure(1, weight=1)
        ramka_top.columnconfigure(3, weight=1)

        tk.Label(ramka_top, text="Typ obiektu:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        combo_typ = ttk.Combobox(ramka_top,
                                 values=["Wszystkie", "Galaktyki", "Mgławice", "Gromady Otwarte", "Gromady Kuliste",
                                         "Inne"], state="readonly")
        combo_typ.set("Wszystkie")
        combo_typ.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        tk.Label(ramka_top, text="Widoczność:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.E)
        combo_polkula = ttk.Combobox(ramka_top, values=["Całe niebo", "Północna (Dec > 0°)", "Południowa (Dec < 0°)"],
                                     state="readonly")
        combo_polkula.set("Całe niebo")
        combo_polkula.grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)

        polnocne = [1, 3, 5, 13, 15, 27, 29, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 44, 45, 49, 51, 52, 53, 56, 57, 58,
                    59, 60, 61, 63, 64, 65, 66, 67, 71, 74, 76, 78, 81, 82, 84, 85, 86, 87, 88, 89, 90, 91, 92, 94, 95,
                    96, 97, 98, 99, 100, 101, 102, 103, 105, 106, 108, 109, 110]
        poludniowe = [2, 4, 6, 7, 8, 9, 10, 11, 12, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 28, 30, 41, 42, 43,
                      46, 47, 48, 50, 54, 55, 62, 68, 69, 70, 72, 73, 75, 77, 79, 80, 83, 93, 104, 107]

        typy_dso = {
            "Wszystkie": list(range(1, 111)),
            "Galaktyki": [31, 32, 33, 49, 51, 58, 59, 60, 61, 63, 64, 65, 66, 74, 77, 81, 82, 83, 84, 85, 86, 87, 88,
                          89, 90, 91, 94, 95, 96, 98, 99, 100, 101, 102, 104, 105, 106, 108, 109, 110],
            "Mgławice": [1, 8, 17, 20, 27, 42, 43, 57, 76, 78, 97],
            "Gromady Otwarte": [6, 7, 11, 16, 18, 21, 23, 24, 25, 26, 29, 34, 35, 36, 37, 38, 39, 41, 44, 45, 46, 47,
                                48, 50, 52, 67, 93, 103],
            "Gromady Kuliste": [2, 3, 4, 5, 9, 10, 12, 13, 14, 15, 19, 22, 28, 30, 53, 54, 55, 56, 62, 68, 69, 70, 71,
                                72, 75, 79, 80, 92, 107],
            "Inne": [40, 73]
        }

        polkule = {
            "Całe niebo": list(range(1, 111)),
            "Północna (Dec > 0°)": polnocne,
            "Południowa (Dec < 0°)": poludniowe
        }

        def zastosuj_filtr():
            wybrany_typ = combo_typ.get()
            wybrana_polkula = combo_polkula.get()

            do_zaznaczenia = set(typy_dso[wybrany_typ]).intersection(set(polkule[wybrana_polkula]))

            for i in range(1, 111):
                self.dso_vars[f"M{i}"].set(i in do_zaznaczenia)

        def wyczysc_wszystko():
            for i in range(1, 111):
                self.dso_vars[f"M{i}"].set(False)

        ramka_przyciski_filtry = tk.Frame(ramka_top)
        ramka_przyciski_filtry.grid(row=1, column=0, columnspan=4, pady=5)

        tk.Button(ramka_przyciski_filtry, text="Zaznacz", command=zastosuj_filtr, bg="#2196F3", fg="white",
                  font=("Helvetica", 9, "bold")).pack(side=tk.LEFT, padx=10)
        tk.Button(ramka_przyciski_filtry, text="Odznacz wszystko", command=wyczysc_wszystko).pack(side=tk.LEFT, padx=10)

        ramka_srodek = tk.Frame(ramka_glowna)
        ramka_srodek.pack(fill=tk.BOTH, expand=True)

        płótno = tk.Canvas(ramka_srodek)
        suwak_y = ttk.Scrollbar(ramka_srodek, orient="vertical", command=płótno.yview)
        suwak_x = ttk.Scrollbar(ramka_srodek, orient="horizontal", command=płótno.xview)

        ramka_przewijana = tk.Frame(płótno)

        ramka_przewijana.bind("<Configure>", lambda e: płótno.configure(scrollregion=płótno.bbox("all")))
        płótno.create_window((0, 0), window=ramka_przewijana, anchor="nw")
        płótno.configure(yscrollcommand=suwak_y.set, xscrollcommand=suwak_x.set)

        suwak_x.pack(side="bottom", fill="x")
        suwak_y.pack(side="right", fill="y")
        płótno.pack(side="left", fill="both", expand=True)

        for i in range(1, 111):
            cb = tk.Checkbutton(ramka_przewijana, text=f"M{i}", variable=self.dso_vars[f"M{i}"])
            cb.grid(row=(i - 1) // 11, column=(i - 1) % 11, sticky="w", padx=8, pady=5)

        def zatwierdz_i_zamknij():
            self.lbl_dso_info.config(text=f"Wybrano obiektów: {sum(1 for v in self.dso_vars.values() if v.get())}")
            okno.destroy()

        ramka_przyciski = tk.Frame(okno)
        ramka_przyciski.pack(fill=tk.X, padx=20, pady=15)

        tk.Button(ramka_przyciski, text="Przeglądaj Katalog (Opisy i Zdjęcia)",
                  command=lambda: self.otworz_katalog_dso(okno),
                  bg="#FF9800", fg="white", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, fill=tk.X, expand=True,
                                                                                 padx=(0, 10))

        tk.Button(ramka_przyciski, text="Zapisz i Zamknij", command=zatwierdz_i_zamknij,
                  bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold")).pack(side=tk.RIGHT, fill=tk.X, expand=True,
                                                                                 padx=(10, 0))

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
            self.entry_elev.insert(0,
                                   str(float(r.json()['results'][0]['elevation'])) if r.status_code == 200 else "100.0")
        except:
            self.entry_elev.delete(0, tk.END)
            self.entry_elev.insert(0, "100.0")

    def wczytaj_ustawienia(self):
        if not os.path.exists("ustawienia.json"):
            return
        try:
            with open("ustawienia.json", "r", encoding="utf-8") as f:
                dane = json.load(f)

            if "lat" in dane:
                self.entry_lat.delete(0, tk.END)
                self.entry_lat.insert(0, dane["lat"])
            if "lon" in dane:
                self.entry_lon.delete(0, tk.END)
                self.entry_lon.insert(0, dane["lon"])
            if "elev" in dane:
                self.entry_elev.delete(0, tk.END)
                self.entry_elev.insert(0, dane["elev"])
            if "timezone" in dane:
                self.lbl_strefa.config(text=dane["timezone"])

            if "zjawiska" in dane:
                for klucz, wartosc in dane["zjawiska"].items():
                    if klucz in self.zjawiska_vars:
                        self.zjawiska_vars[klucz].set(wartosc)

            if "dso" in dane:
                for klucz, wartosc in dane["dso"].items():
                    if klucz in self.dso_vars:
                        self.dso_vars[klucz].set(wartosc)
                if hasattr(self, 'lbl_dso_info'):
                    self.lbl_dso_info.config(
                        text=f"Wybrano obiektów: {sum(1 for v in self.dso_vars.values() if v.get())}")

            if "orby" in dane:
                def wstaw_orb(pole, wartosc):
                    pole.delete(0, tk.END)
                    pole.insert(0, str(wartosc))

                orby = dane["orby"]
                if "Koniunkcja" in orby: wstaw_orb(self.orb_kon, orby["Koniunkcja"])
                if "Sekstyl" in orby: wstaw_orb(self.orb_sek, orby["Sekstyl"])
                if "Kwadratura" in orby: wstaw_orb(self.orb_kwa, orby["Kwadratura"])
                if "Trygon" in orby: wstaw_orb(self.orb_try, orby["Trygon"])
                if "Opozycja" in orby: wstaw_orb(self.orb_opo, orby["Opozycja"])

            if "lat" in dane and "lon" in dane:
                try:
                    lat_f, lon_f = float(dane["lat"]), float(dane["lon"])
                    self.mapa.set_position(lat_f, lon_f)
                    if self.znacznik: self.znacznik.delete()
                    self.znacznik = self.mapa.set_marker(lat_f, lon_f, text="Zaznaczone Miejsce")
                except ValueError:
                    pass

        except Exception as e:
            print(f"Nie udało się wczytać ustawień: {e}")

    def zapisz_ustawienia(self):
        dane_do_zapisu = {
            "lat": self.entry_lat.get(),
            "lon": self.entry_lon.get(),
            "elev": self.entry_elev.get(),
            "timezone": self.lbl_strefa.cget("text"),
            "zjawiska": {klucz: zmienna.get() for klucz, zmienna in self.zjawiska_vars.items()},
            "dso": {klucz: zmienna.get() for klucz, zmienna in self.dso_vars.items()},
            "orby": {
                "Koniunkcja": self.orb_kon.get(),
                "Sekstyl": self.orb_sek.get(),
                "Kwadratura": self.orb_kwa.get(),
                "Trygon": self.orb_try.get(),
                "Opozycja": self.orb_opo.get()
            }
        }
        try:
            with open("ustawienia.json", "w", encoding="utf-8") as f:
                json.dump(dane_do_zapisu, f, indent=4)
        except Exception as e:
            print(f"Nie udało się zapisać ustawień: {e}")

    def zbierz_i_wyslij(self):
        try:
            aktywna_zakladka = self.notebook.index(self.notebook.select())
            tryb = "efemerydy" if aktywna_zakladka == 0 else "kosmogram"

            def bezpieczny_float(val, domyslna):
                try:
                    return float(str(val).replace(',', '.'))
                except ValueError:
                    return domyslna

            def bezpieczny_int(val, domyslna):
                try:
                    return int(val)
                except ValueError:
                    return domyslna

            data_start_str = self.entry_date.get()
            try:
                rok, miesiac, dzien = map(int, data_start_str.split("-"))
            except ValueError:
                dzisiaj = datetime.date.today()
                rok, miesiac, dzien = dzisiaj.year, dzisiaj.month, dzisiaj.day

            okienko_val = bezpieczny_float(self.entry_okienko.get(), 5.0)
            elev = bezpieczny_float(self.entry_elev.get(), 100.0)
            lat_val = bezpieczny_float(self.entry_lat.get(), 53.75)
            lon_val = bezpieczny_float(self.entry_lon.get(), 20.51)

            dni_analizy = bezpieczny_int(self.entry_days.get(), 7)
            krok = bezpieczny_int(self.entry_krok.get(), 2)

            godzina = bezpieczny_int(self.spin_godz.get(), 12)
            minuta = bezpieczny_int(self.spin_min.get(), 0)

            urodz_czas_skladany = f"{godzina:02d}:{minuta:02d}"

            zjawiska_konf = {k: v.get() for k, v in self.zjawiska_vars.items()}

            konfiguracja = {
                "tryb": tryb,
                "rok": rok, "miesiac": miesiac, "dzien": dzien,
                "dni_do_analizy": dni_analizy,
                "lat_dd": lat_val,
                "lon_dd": lon_val,
                "elev": elev,
                "timezone": self.lbl_strefa.cget("text"),
                "krok_planety": krok,
                "okienko_koniunkcji": okienko_val,
                "obiekty_dso": [n for n, v in self.dso_vars.items() if v.get()],
                "zjawiska": zjawiska_konf,
                "urodz_data": self.entry_urodz_data.get(),
                "urodz_czas": urodz_czas_skladany,
                "sys_domow": self.combo_domy.get(),
                "orby": {
                    "Koniunkcja": bezpieczny_float(self.orb_kon.get(), 8.0),
                    "Sekstyl": bezpieczny_float(self.orb_sek.get(), 6.0),
                    "Kwadratura": bezpieczny_float(self.orb_kwa.get(), 8.0),
                    "Trygon": bezpieczny_float(self.orb_try.get(), 8.0),
                    "Opozycja": bezpieczny_float(self.orb_opo.get(), 8.0)
                }
            }

            self.zapisz_ustawienia()
            self.on_start_callback(konfiguracja)

        except Exception as e:
            messagebox.showerror("Błąd danych", f"Sprawdź poprawność danych.\nSzczegóły: {e}")