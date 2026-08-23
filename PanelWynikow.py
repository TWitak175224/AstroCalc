import tkinter as tk
from tkinter import ttk


class PanelWynikow(tk.Frame):
    def __init__(self, parent, on_back_callback):
        super().__init__(parent)
        self.on_back_callback = on_back_callback
        self.setup_ui()

    def setup_ui(self):
        lbl = tk.Label(self, text="Kalendarz Astronomiczny", font=("Helvetica", 14, "bold"))
        lbl.pack(pady=10)

        # System Zakładek (Notebook)
        self.notatnik = ttk.Notebook(self)
        self.notatnik.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.zakladka_slonce = tk.Frame(self.notatnik)
        self.notatnik.add(self.zakladka_slonce, text="Słońce i Księżyc")

        self.zakladka_planety = tk.Frame(self.notatnik)
        self.notatnik.add(self.zakladka_planety, text="Zjawiska Planetarne")

        self.tabela_slonce = self.utworz_tabele(self.zakladka_slonce)
        self.tabela_planety = self.utworz_tabele(self.zakladka_planety)

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

    def zaladuj_dane(self, dane_slonce, naglowki_slonce, dane_planety, naglowki_planety):
        self.wypelnij_tabele(self.tabela_slonce, dane_slonce, naglowki_slonce)
        self.wypelnij_tabele(self.tabela_planety, dane_planety, naglowki_planety)

    def wypelnij_tabele(self, tabela, dane, naglowki):
        for wiersz in tabela.get_children():
            tabela.delete(wiersz)

        tabela["columns"] = naglowki

        for nazwa in naglowki:
            tabela.heading(nazwa, text=nazwa)
            szerokosc = 70 if nazwa == "Dzień" else 130
            tabela.column(nazwa, width=szerokosc, anchor=tk.CENTER, stretch=tk.NO)

        for wiersz in dane:
            tabela.insert("", tk.END, values=wiersz)