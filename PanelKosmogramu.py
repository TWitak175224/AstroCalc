import tkinter as tk
from tkinter import ttk
import math


class PanelKosmogramu(tk.Frame):
    def __init__(self, parent, on_back_callback):
        super().__init__(parent)
        self.on_back_callback = on_back_callback

        self.planety_dane = []
        self.domy_dane = []
        self.aspekty_dane = []

        self.setup_ui()

    def setup_ui(self):
        lbl_tytul = tk.Label(self, text="Dane Kosmogramu", font=("Helvetica", 16, "bold"))
        lbl_tytul.pack(pady=10)

        ramka_gorna = tk.Frame(self)
        ramka_gorna.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        ramka_planety = tk.LabelFrame(ramka_gorna, text="Pozycje Planet")
        ramka_planety.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree_planety = self.stworz_tabele(ramka_planety, ["Ciało niebieskie", "Znak Zodiaku", "Długość [°]"])

        ramka_domy = tk.LabelFrame(ramka_gorna, text="Domy Astrologiczne i Osie")
        ramka_domy.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree_domy = self.stworz_tabele(ramka_domy, ["Dom / Oś", "Znak Zodiaku", "Długość [°]"])

        ramka_dolna = tk.LabelFrame(self, text="Główne Aspekty")
        ramka_dolna.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        self.tree_aspekty = self.stworz_tabele(ramka_dolna, ["Obiekt 1", "Aspekt", "Obiekt 2", "Orb (Odchylenie)"])

        panel_btn = tk.Frame(self)
        panel_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        btn_wroc = tk.Button(panel_btn, text="< Wróć do ustawień", command=self.on_back_callback,
                             font=("Helvetica", 10))
        btn_wroc.pack(side=tk.LEFT)

        btn_rysuj = tk.Button(panel_btn, text="Generuj Wykres (Wizualizacja)", command=self.pokaz_wykres, bg="#9C27B0",
                              fg="white", font=("Helvetica", 10, "bold"))
        btn_rysuj.pack(side=tk.RIGHT, padx=10)

    def sortuj_kolumne(self, tree, col, reverse):
        # Pobranie danych z kolumny do posortowania
        dane = [(tree.set(k, col), k) for k in tree.get_children('')]

        def konwertuj_do_sortowania(wartosc):
            # Czyszczenie ze stopni i minut, aby móc sortować liczbowo
            czysta_wartosc = wartosc.replace('°', '').replace("'", '').strip()
            try:
                return float(czysta_wartosc.split()[0])
            except (ValueError, IndexError):
                return wartosc

        # Sortowanie (liczbowo lub alfabetycznie w zależności od zawartości)
        dane.sort(key=lambda t: konwertuj_do_sortowania(t[0]), reverse=reverse)

        # Przestawienie wierszy w Treeview
        for index, (val, k) in enumerate(dane):
            tree.move(k, '', index)

        # Zmiana kierunku sortowania przy następnym kliknięciu
        tree.heading(col, command=lambda _col=col: self.sortuj_kolumne(tree, _col, not reverse))

    def stworz_tabele(self, parent, naglowki):
        scroll_y = ttk.Scrollbar(parent, orient=tk.VERTICAL)
        tree = ttk.Treeview(parent, yscrollcommand=scroll_y.set, show="headings")

        scroll_y.config(command=tree.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tree["columns"] = naglowki
        for naglowek in naglowki:
            # Podpięcie metody sortującej pod kliknięcie w nagłówek
            tree.heading(naglowek, text=naglowek, command=lambda _col=naglowek: self.sortuj_kolumne(tree, _col, False))
            tree.column(naglowek, anchor=tk.CENTER)

        return tree

    def zaladuj_dane(self, planety, domy, aspekty):
        self.planety_dane = planety
        self.domy_dane = domy
        self.aspekty_dane = aspekty

        self.tree_planety.delete(*self.tree_planety.get_children())
        self.tree_domy.delete(*self.tree_domy.get_children())
        self.tree_aspekty.delete(*self.tree_aspekty.get_children())

        for p in planety: self.tree_planety.insert("", tk.END, values=p)
        for d in domy: self.tree_domy.insert("", tk.END, values=d)
        for a in aspekty: self.tree_aspekty.insert("", tk.END, values=a)

    def pokaz_wykres(self):
        okno = tk.Toplevel(self)
        okno.title("Wizualizacja Kosmogramu")
        okno.geometry("820x750")
        okno.configure(bg="#f0f0f0")

        panel_zapisu = tk.Frame(okno, bg="#e0e0e0", pady=10)
        panel_zapisu.pack(side=tk.BOTTOM, fill=tk.X)

        def zapisz_obraz():
            from tkinter import filedialog, messagebox
            try:
                from PIL import ImageGrab
            except ImportError:
                messagebox.showerror("Brak biblioteki", "Zainstaluj bibliotekę Pillow w terminalu:\npip install Pillow")
                return

            plik = filedialog.asksaveasfilename(
                title="Zapisz kosmogram jako",
                defaultextension=".png",
                filetypes=[("Pliki PNG", "*.png")],
                initialfile="Kosmogram.png"
            )

            if not plik:
                return

            okno.update()
            x = canvas.winfo_rootx()
            y = canvas.winfo_rooty()
            w = canvas.winfo_width()
            h = canvas.winfo_height()

            try:
                img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
                img.save(plik)
                messagebox.showinfo("Sukces", "Kosmogram został pomyślnie zapisany!")
            except Exception as e:
                messagebox.showerror("Błąd zapisu", f"Nie udało się zapisać pliku:\n{e}")

        tk.Button(panel_zapisu, text="Zapisz kosmogram (PNG)", command=zapisz_obraz,
                  bg="#2196F3", fg="white", font=("Helvetica", 10, "bold"), padx=20).pack()

        ramka_wykresu = tk.Frame(okno, bg="white")
        ramka_wykresu.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        suwak_y = ttk.Scrollbar(ramka_wykresu, orient=tk.VERTICAL)
        suwak_y.pack(side=tk.RIGHT, fill=tk.Y)

        suwak_x = ttk.Scrollbar(ramka_wykresu, orient=tk.HORIZONTAL)
        suwak_x.pack(side=tk.BOTTOM, fill=tk.X)

        canvas = tk.Canvas(ramka_wykresu, bg="white", width=800, height=800, highlightthickness=0,
                           scrollregion=(0, 0, 800, 800),
                           yscrollcommand=suwak_y.set, xscrollcommand=suwak_x.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        suwak_y.config(command=canvas.yview)
        suwak_x.config(command=canvas.xview)

        cx, cy = 400, 400
        r_zew = 320
        r_wew = 240
        r_planety = 200

        asc_lon = 0.0
        for d in self.domy_dane:
            if "ASC" in d[0]:
                asc_lon = float(d[2].replace('°', ''))
                break

        def lon_na_xy(lon, promien):
            kat_rad = math.radians(asc_lon - lon + 180)
            return cx + promien * math.cos(kat_rad), cy + promien * math.sin(kat_rad)

        ZNAKI = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
        for i in range(12):
            stopien_poczatku = i * 30
            x_zew, y_zew = lon_na_xy(stopien_poczatku, r_zew)
            x_wew, y_wew = lon_na_xy(stopien_poczatku, r_wew)
            canvas.create_line(x_wew, y_wew, x_zew, y_zew, fill="#e0e0e0", width=1)

            x_txt, y_txt = lon_na_xy(stopien_poczatku + 15, r_zew - 40)
            canvas.create_text(x_txt, y_txt, text=ZNAKI[i], font=("Helvetica", 18, "bold"), fill="gray")

        canvas.create_oval(cx - r_zew, cy - r_zew, cx + r_zew, cy + r_zew, outline="black", width=2)
        canvas.create_oval(cx - r_wew, cy - r_wew, cx + r_wew, cy + r_wew, outline="black", width=2)

        kordy = {}
        domy_kordy = {}

        for p in self.planety_dane:
            kordy[p[0]] = float(p[2].replace('°', ''))

        for d in self.domy_dane:
            if not d[0]: continue
            wartosc = float(d[2].replace('°', ''))
            if "ASC" in d[0]: kordy["Ascendent"] = wartosc
            if "MC" in d[0]: kordy["Medium Coeli"] = wartosc
            if "DC" in d[0]: kordy["Descendant"] = wartosc
            if "IC" in d[0]: kordy["Imum Coeli"] = wartosc
            if d[0].startswith("Dom "):
                numer = int(d[0].replace("Dom ", ""))
                domy_kordy[numer] = wartosc

        for i in range(1, 13):
            if i in domy_kordy:
                lon = domy_kordy[i]
                if i not in [1, 4, 7, 10]:
                    x1, y1 = lon_na_xy(lon, 40)
                    x2, y2 = lon_na_xy(lon, r_wew)
                    canvas.create_line(x1, y1, x2, y2, fill="gray", dash=(4, 4), width=1)

                nast_i = i + 1 if i < 12 else 1
                lon1 = domy_kordy[i]
                lon2 = domy_kordy[nast_i]
                roznica = lon2 - lon1
                if roznica < 0: roznica += 360

                mid_lon = (lon1 + roznica / 2) % 360
                txt_x, txt_y = lon_na_xy(mid_lon, 70)
                canvas.create_text(txt_x, txt_y, text=str(i), font=("Helvetica", 14, "bold"), fill="gray")

        if "Ascendent" in kordy and "Descendant" in kordy:
            x1, y1 = lon_na_xy(kordy["Ascendent"], r_wew)
            x2, y2 = lon_na_xy(kordy["Descendant"], r_wew)
            canvas.create_line(x1, y1, x2, y2, fill="red", width=2)
            canvas.create_text(x1 - 25, y1, text="ASC", fill="red", font=("Helvetica", 10, "bold"))
            canvas.create_text(x2 + 25, y2, text="DC", fill="red", font=("Helvetica", 10, "bold"))

        if "Medium Coeli" in kordy and "Imum Coeli" in kordy:
            x1, y1 = lon_na_xy(kordy["Medium Coeli"], r_wew)
            x2, y2 = lon_na_xy(kordy["Imum Coeli"], r_wew)
            canvas.create_line(x1, y1, x2, y2, fill="blue", width=2)
            canvas.create_text(x1, y1 - 20, text="MC", fill="blue", font=("Helvetica", 10, "bold"))
            canvas.create_text(x2, y2 + 20, text="IC", fill="blue", font=("Helvetica", 10, "bold"))

        kolory_aspektow = {
            "Koniunkcja": "black",
            "Trygon": "green",
            "Sekstyl": "cyan",
            "Kwadratura": "red",
            "Opozycja": "purple"
        }

        for a in self.aspekty_dane:
            nazwa1, aspekt, nazwa2, orb = a
            if nazwa1 in kordy and nazwa2 in kordy:
                x1, y1 = lon_na_xy(kordy[nazwa1], r_planety - 15)
                x2, y2 = lon_na_xy(kordy[nazwa2], r_planety - 15)
                kolor = kolory_aspektow.get(aspekt, "gray")
                canvas.create_line(x1, y1, x2, y2, fill=kolor, width=1)

        for nazwa, dlugosc in kordy.items():
            if nazwa in ["Ascendent", "Descendant", "Medium Coeli", "Imum Coeli"]:
                continue

            x, y = lon_na_xy(dlugosc, r_planety)
            canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="black")

            kat_rad = math.radians(asc_lon - dlugosc + 180)
            txt_x = cx + (r_planety + 20) * math.cos(kat_rad)
            txt_y = cy + (r_planety + 20) * math.sin(kat_rad)

            skrot = nazwa[:3].upper() if "Węzeł" not in nazwa else ("WĘZ_N" if "Półn" in nazwa else "WĘZ_S")
            canvas.create_text(txt_x, txt_y, text=skrot, font=("Helvetica", 9, "bold"))

        legenda_x = 20
        legenda_y = 20
        canvas.create_text(legenda_x, legenda_y, text="LEGENDA KOSMOGRAMU:", anchor=tk.W,
                           font=("Helvetica", 10, "bold"))
        legenda_y += 25

        elementy_legendy = [
            ("Koniunkcja (0°)", "black", 1, None),
            ("Sekstyl (60°)", "cyan", 1, None),
            ("Kwadratura (90°)", "red", 1, None),
            ("Trygon (120°)", "green", 1, None),
            ("Opozycja (180°)", "purple", 1, None),
            ("Oś ASC - DC", "red", 2, None),
            ("Oś MC - IC", "blue", 2, None),
            ("Granice domów", "gray", 1, (4, 4))
        ]

        for tekst, kolor, grubosc, my_dash in elementy_legendy:
            if my_dash:
                canvas.create_line(legenda_x, legenda_y, legenda_x + 30, legenda_y, fill=kolor, width=grubosc,
                                   dash=my_dash)
            else:
                canvas.create_line(legenda_x, legenda_y, legenda_x + 30, legenda_y, fill=kolor, width=grubosc)
            canvas.create_text(legenda_x + 40, legenda_y, text=tekst, anchor=tk.W, font=("Helvetica", 9))
            legenda_y += 20