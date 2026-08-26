import tkinter as tk
from tkinter import ttk

# Słownik do tłumaczenia numerów miesięcy na piękne nazwy
MIESIACE_PL = {
    "01": "Styczeń", "02": "Luty", "03": "Marzec",
    "04": "Kwiecień", "05": "Maj", "06": "Czerwiec",
    "07": "Lipiec", "08": "Sierpień", "09": "Wrzesień",
    "10": "Październik", "11": "Listopad", "12": "Grudzień"
}


class PanelWynikow(tk.Frame):
    def __init__(self, parent, on_back_callback):
        super().__init__(parent)
        self.on_back_callback = on_back_callback
        self.setup_ui()

    def setup_ui(self):
        lbl = tk.Label(self, text="Kalendarz Astronomiczny (Efemerydy)", font=("Helvetica", 14, "bold"))
        lbl.pack(pady=10)

        # Kontener nadrzędny, w którym będziemy dynamicznie rysować zakładki
        self.kontener_notatnikow = tk.Frame(self)
        self.kontener_notatnikow.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        btn_back = tk.Button(self, text="← Powrót do mapy", command=self.on_back_callback, font=("Helvetica", 10))
        btn_back.pack(pady=15)

    def utworz_tabele(self, parent_frame):
        ramka_tabeli = tk.Frame(parent_frame)
        ramka_tabeli.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        tabela = ttk.Treeview(ramka_tabeli, show="headings", height=15)

        scroll_y = ttk.Scrollbar(ramka_tabeli, orient=tk.VERTICAL, command=tabela.yview)
        scroll_x = ttk.Scrollbar(ramka_tabeli, orient=tk.HORIZONTAL, command=tabela.xview)

        tabela.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        tabela.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        return tabela

    def zaladuj_dane(self, dane_slonce, naglowki_slonce, dane_planety, naglowki_planety, dane_kalendarium,
                     naglowki_kalendarium, dane_dso, naglowki_dso):
        # 1. Czyszczenie poprzedniego widoku
        for widget in self.kontener_notatnikow.winfo_children():
            widget.destroy()

        # 2. GRUPOWANIE DANYCH
        drzewo = {}

        for w in dane_slonce:
            _, mc, rok = w[0].split('.')
            if rok not in drzewo: drzewo[rok] = {}
            if mc not in drzewo[rok]: drzewo[rok][mc] = {'s': [], 'p': [], 'k': [], 'd': []}
            drzewo[rok][mc]['s'].append(w)

        for w in dane_planety:
            _, mc, rok = w[0].split('.')
            if rok not in drzewo: drzewo[rok] = {}
            if mc not in drzewo[rok]: drzewo[rok][mc] = {'s': [], 'p': [], 'k': [], 'd': []}
            drzewo[rok][mc]['p'].append(w)

        for w in dane_dso:
            _, mc, rok = w[0].split('.')
            if rok not in drzewo: drzewo[rok] = {}
            if mc not in drzewo[rok]: drzewo[rok][mc] = {'s': [], 'p': [], 'k': [], 'd': []}
            drzewo[rok][mc]['d'].append(w)

        for w in dane_kalendarium:
            rok = w[0][:4]
            mc = w[0][5:7]
            if rok not in drzewo: drzewo[rok] = {}
            if mc not in drzewo[rok]: drzewo[rok][mc] = {'s': [], 'p': [], 'k': [], 'd': []}
            drzewo[rok][mc]['k'].append(w)

        # 3. BUDOWANIE ZAKŁADEK (Z INTELIGENTNYM UKRYWANIEM)
        czy_wiele_lat = len(drzewo) > 1

        # LOGIKA DLA LAT
        if czy_wiele_lat:
            notatnik_lat = ttk.Notebook(self.kontener_notatnikow)
            notatnik_lat.pack(fill=tk.BOTH, expand=True)
        else:
            # Jeśli jest tylko jeden rok, tworzymy zwykłą, niewidoczną ramkę
            ramka_na_lata = tk.Frame(self.kontener_notatnikow)
            ramka_na_lata.pack(fill=tk.BOTH, expand=True)

        for rok in sorted(drzewo.keys()):
            if czy_wiele_lat:
                zakladka_roku = tk.Frame(notatnik_lat)
                notatnik_lat.add(zakladka_roku, text=f"Rok {rok}")
                rodzic_dla_miesiecy = zakladka_roku
            else:
                rodzic_dla_miesiecy = ramka_na_lata

            # LOGIKA DLA MIESIĘCY
            czy_wiele_miesiecy = len(drzewo[rok]) > 1

            if czy_wiele_miesiecy:
                notatnik_miesiecy = ttk.Notebook(rodzic_dla_miesiecy)
                notatnik_miesiecy.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            else:
                # Jeśli jest tylko jeden miesiąc, pomijamy zakładkę
                ramka_na_miesiac = tk.Frame(rodzic_dla_miesiecy)
                ramka_na_miesiac.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

            for mc in sorted(drzewo[rok].keys()):
                nazwa_mc = MIESIACE_PL.get(mc, mc)

                if czy_wiele_miesiecy:
                    zakladka_mc = tk.Frame(notatnik_miesiecy)
                    notatnik_miesiecy.add(zakladka_mc, text=nazwa_mc)
                    rodzic_dla_kategorii = zakladka_mc
                else:
                    rodzic_dla_kategorii = ramka_na_miesiac

                # LOGIKA DLA TABEL (TE ZAKŁADKI POJAWIAJĄ SIĘ ZAWSZE)
                notatnik_kategorii = ttk.Notebook(rodzic_dla_kategorii)
                notatnik_kategorii.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

                if drzewo[rok][mc]['s']:
                    z_slonce = tk.Frame(notatnik_kategorii)
                    notatnik_kategorii.add(z_slonce, text="Słońce i Księżyc")
                    tab_slonce = self.utworz_tabele(z_slonce)
                    self.wypelnij_tabele(tab_slonce, drzewo[rok][mc]['s'], naglowki_slonce)

                if drzewo[rok][mc]['p']:
                    z_planety = tk.Frame(notatnik_kategorii)
                    notatnik_kategorii.add(z_planety, text="Zjawiska Planetarne")
                    tab_planety = self.utworz_tabele(z_planety)
                    self.wypelnij_tabele(tab_planety, drzewo[rok][mc]['p'], naglowki_planety)

                if drzewo[rok][mc]['d']:
                    z_dso = tk.Frame(notatnik_kategorii)
                    notatnik_kategorii.add(z_dso, text="Obiekty Messiera (DSO)")
                    tab_dso = self.utworz_tabele(z_dso)
                    self.wypelnij_tabele(tab_dso, drzewo[rok][mc]['d'], naglowki_dso)

                if drzewo[rok][mc]['k']:
                    z_kalen = tk.Frame(notatnik_kategorii)
                    notatnik_kategorii.add(z_kalen, text="Kalendarium Zjawisk")
                    tab_kalen = self.utworz_tabele(z_kalen)
                    self.wypelnij_tabele(tab_kalen, drzewo[rok][mc]['k'], naglowki_kalendarium)

    def wypelnij_tabele(self, tabela, dane, naglowki):
        for wiersz in tabela.get_children():
            tabela.delete(wiersz)

        tabela["columns"] = naglowki

        for nazwa in naglowki:
            tabela.heading(nazwa, text=nazwa)
            if nazwa == "Dzień":
                szerokosc = 80
            elif nazwa in ["Zjawisko Astronomiczne", "Data i Czas"]:
                szerokosc = 200
            elif nazwa == "Dodatkowe Parametry":
                szerokosc = 160
            else:
                szerokosc = 130

            tabela.column(nazwa, width=szerokosc, anchor=tk.CENTER, stretch=tk.NO)

        for wiersz in dane:
            tabela.insert("", tk.END, values=wiersz)