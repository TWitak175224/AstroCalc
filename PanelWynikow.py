import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import os
from datetime import datetime, timedelta

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


class PanelWynikow(tk.Frame):
    def __init__(self, parent, on_back_callback):
        super().__init__(parent)
        self.on_back_callback = on_back_callback

        self.w_s = self.n_s = []
        self.w_p = self.n_p = []
        self.w_k = self.n_k = []
        self.w_dso = self.n_dso = []
        self.config_dane = None

        try:
            pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
            pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))
            self.font_regular = 'Arial'
            self.font_bold = 'Arial-Bold'
        except:
            self.font_regular = 'Helvetica'
            self.font_bold = 'Helvetica-Bold'

        self.setup_ui()

    def setup_ui(self):
        panel_btn = tk.Frame(self)
        panel_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        btn_wroc = tk.Button(panel_btn, text="< Wróć do ustawień", command=self.on_back_callback,
                             font=("Helvetica", 10))
        btn_wroc.pack(side=tk.LEFT)

        btn_eksport_pdf = tk.Button(panel_btn, text="Eksportuj do PDF", command=self.eksportuj_pdf, bg="#f44336",
                                    fg="white", font=("Helvetica", 10, "bold"))
        btn_eksport_pdf.pack(side=tk.RIGHT, padx=(10, 0))

        btn_eksport_csv = tk.Button(panel_btn, text="Eksportuj do CSV", command=self.eksportuj_csv, bg="#2196F3",
                                    fg="white", font=("Helvetica", 10, "bold"))
        btn_eksport_csv.pack(side=tk.RIGHT)

        # Główny kontener na zakładki miesięcy i lat
        self.main_notebook = ttk.Notebook(self)
        self.main_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def stworz_tabele(self, parent):
        scroll_y = ttk.Scrollbar(parent, orient=tk.VERTICAL)
        scroll_x = ttk.Scrollbar(parent, orient=tk.HORIZONTAL)

        tree = ttk.Treeview(parent, yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.config(command=tree.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        scroll_x.config(command=tree.xview)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        tree.pack(fill=tk.BOTH, expand=True)
        return tree

    def wypelnij_tabele(self, tree, naglowki, dane):
        tree.delete(*tree.get_children())
        tree["columns"] = naglowki
        tree["show"] = "headings"

        for naglowek in naglowki:
            tree.heading(naglowek, text=naglowek)
            tree.column(naglowek, width=130, anchor=tk.CENTER)

        for wiersz in dane:
            tree.insert("", tk.END, values=wiersz)

    def _parsuj_rok_miesiac(self, data_str, format_typu):
        try:
            if format_typu == 'k':
                return int(data_str[:4]), int(data_str[5:7])
            else:
                czesci = data_str.split('.')
                return int(czesci[2]), int(czesci[1])
        except:
            return 0, 0

    def zaladuj_dane(self, w_s, n_s, w_p, n_p, w_k, n_k, w_dso, n_dso, config=None):
        self.w_s, self.n_s = w_s, n_s
        self.w_p, self.n_p = w_p, n_p
        self.w_k, self.n_k = w_k, n_k
        self.w_dso, self.n_dso = w_dso, n_dso
        self.config_dane = config

        for tab in self.main_notebook.tabs():
            self.main_notebook.forget(tab)

        miesiace_nazwy = ["", "STYCZEŃ", "LUTY", "MARZEC", "KWIECIEŃ", "MAJ", "CZERWIEC",
                          "LIPIEC", "SIERPIEŃ", "WRZESIEŃ", "PAŹDZIERNIK", "LISTOPAD", "GRUDZIEŃ"]

        unikalne_m_y = set()
        for w in self.w_s: unikalne_m_y.add(self._parsuj_rok_miesiac(w[0], 's'))
        for w in self.w_p: unikalne_m_y.add(self._parsuj_rok_miesiac(w[0], 'p'))
        for w in self.w_dso: unikalne_m_y.add(self._parsuj_rok_miesiac(w[0], 'd'))
        for w in self.w_k: unikalne_m_y.add(self._parsuj_rok_miesiac(w[0], 'k'))

        if (0, 0) in unikalne_m_y: unikalne_m_y.remove((0, 0))
        miesiace_posortowane = sorted(list(unikalne_m_y))

        if not miesiace_posortowane:
            miesiace_posortowane = [(datetime.now().year, datetime.now().month)]

        # --- LOGIKA WYŚWIETLANIA ZAKŁADEK ---
        pokaz_kalendarium = False
        pokaz_dso = False

        if self.config_dane:
            # Pokaż kalendarium, jeśli jakiekolwiek zjawisko jest zaznaczone jako True
            pokaz_kalendarium = any(self.config_dane.get('zjawiska', {}).values())
            # Pokaż DSO, jeśli lista wybranych obiektów nie jest pusta
            pokaz_dso = len(self.config_dane.get('obiekty_dso', [])) > 0

        for rok, miesiac in miesiace_posortowane:
            nazwa_zakladki = f"{miesiace_nazwy[miesiac]} {rok}"

            tab_mc = ttk.Frame(self.main_notebook)
            self.main_notebook.add(tab_mc, text=nazwa_zakladki)

            sub_notebook = ttk.Notebook(tab_mc)
            sub_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Słońce i Księżyc (Zawsze widoczne)
            f_slonce = ttk.Frame(sub_notebook)
            sub_notebook.add(f_slonce, text="Słońce i Księżyc")
            tree_s = self.stworz_tabele(f_slonce)
            w_s_mc = [w for w in self.w_s if self._parsuj_rok_miesiac(w[0], 's') == (rok, miesiac)]
            self.wypelnij_tabele(tree_s, self.n_s, w_s_mc)

            # Planety (Zawsze widoczne)
            f_planety = ttk.Frame(sub_notebook)
            sub_notebook.add(f_planety, text="Planety")
            tree_p = self.stworz_tabele(f_planety)
            w_p_mc = [w for w in self.w_p if self._parsuj_rok_miesiac(w[0], 'p') == (rok, miesiac)]
            self.wypelnij_tabele(tree_p, self.n_p, w_p_mc)

            # Kalendarium (Warunkowe)
            if pokaz_kalendarium:
                f_kal = ttk.Frame(sub_notebook)
                sub_notebook.add(f_kal, text="Kalendarium Zjawisk")
                tree_k = self.stworz_tabele(f_kal)
                w_k_mc = [w for w in self.w_k if self._parsuj_rok_miesiac(w[0], 'k') == (rok, miesiac)]
                self.wypelnij_tabele(tree_k, self.n_k, w_k_mc)

            # DSO (Warunkowe)
            if pokaz_dso:
                f_dso = ttk.Frame(sub_notebook)
                sub_notebook.add(f_dso, text="Katalog DSO")
                tree_d = self.stworz_tabele(f_dso)
                w_dso_mc = [w for w in self.w_dso if self._parsuj_rok_miesiac(w[0], 'd') == (rok, miesiac)]
                self.wypelnij_tabele(tree_d, self.n_dso, w_dso_mc)

    def eksportuj_pdf(self):
        plik = filedialog.asksaveasfilename(
            title="Zapisz jako PDF",
            defaultextension=".pdf",
            filetypes=[("Pliki PDF", "*.pdf")],
            initialfile="Raport_Astronomiczny.pdf"
        )
        if not plik:
            return

        try:
            doc = SimpleDocTemplate(plik, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20,
                                    bottomMargin=20)
            elementy = []

            styl_tytulu = ParagraphStyle(
                name='TytulStrony', fontName=self.font_bold, fontSize=24, alignment=1, spaceAfter=15,
                textColor=colors.HexColor('#2c3e50')
            )
            styl_info = ParagraphStyle(
                name='InfoStrony', fontName=self.font_regular, fontSize=12, alignment=1, spaceAfter=8,
                textColor=colors.HexColor('#34495e')
            )
            styl_miesiaca = ParagraphStyle(
                name='Miesiac', fontName=self.font_bold, fontSize=16, alignment=1, spaceAfter=15, spaceBefore=10,
                textColor=colors.HexColor('#2c3e50')
            )
            styl_sekcji = ParagraphStyle(
                name='Sekcja', fontName=self.font_bold, fontSize=12, spaceAfter=8, spaceBefore=12
            )

            # STRONA TYTUŁOWA
            if self.config_dane:
                start_dt = datetime(self.config_dane['rok'], self.config_dane['miesiac'], self.config_dane['dzien'])
                end_dt = start_dt + timedelta(days=self.config_dane['dni_do_analizy'] - 1)
                okres_str = f"na okres: od {start_dt.strftime('%Y-%m-%d')} do {end_dt.strftime('%Y-%m-%d')} ({self.config_dane['dni_do_analizy']} dni)"
                miejsce_str = f"dla miejsca: Szerokość: {self.config_dane['lat_dd']}° | Długość: {self.config_dane['lon_dd']}° | Wysokość: {self.config_dane['elev']} m n.p.m."
                strefa_str = f"Strefa czasowa: {self.config_dane['timezone']}"
            else:
                okres_str = "na okres: Brak danych"
                miejsce_str = "dla miejsca: Brak danych"
                strefa_str = ""

            tytul_elements = [
                Paragraph("KALENDARZ ASTRONOMICZNY", styl_tytulu),
                Spacer(1, 15),
                Paragraph(okres_str, styl_info),
                Spacer(1, 6),
                Paragraph(miejsce_str, styl_info),
            ]
            if strefa_str:
                tytul_elements.extend([Spacer(1, 6), Paragraph(strefa_str, styl_info)])

            t_tytul = Table([[tytul_elements]], colWidths=[800], rowHeights=[530])
            t_tytul.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))
            elementy.append(t_tytul)
            elementy.append(PageBreak())

            def dodaj_sekcje(tytul, naglowki, wiersze):
                if not wiersze: return
                elementy.append(Paragraph(tytul, styl_sekcji))

                dane_tabeli = [naglowki] + [list(w) for w in wiersze]
                rozmiar_fontu = 7 if len(naglowki) > 8 else 9

                t = Table(dane_tabeli)
                styl_tabeli = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), self.font_bold),
                    ('FONTSIZE', (0, 0), (-1, 0), rozmiar_fontu),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('FONTNAME', (0, 1), (-1, -1), self.font_regular),
                    ('FONTSIZE', (0, 1), (-1, -1), rozmiar_fontu),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ])

                for i in range(1, len(dane_tabeli)):
                    bg_color = colors.HexColor('#f2f2f2') if i % 2 == 0 else colors.white
                    styl_tabeli.add('BACKGROUND', (0, i), (-1, i), bg_color)

                t.setStyle(styl_tabeli)
                elementy.append(t)

            miesiace_nazwy = ["", "STYCZEŃ", "LUTY", "MARZEC", "KWIECIEŃ", "MAJ", "CZERWIEC",
                              "LIPIEC", "SIERPIEŃ", "WRZESIEŃ", "PAŹDZIERNIK", "LISTOPAD", "GRUDZIEŃ"]

            unikalne_m_y = set()
            for w in self.w_s: unikalne_m_y.add(self._parsuj_rok_miesiac(w[0], 's'))
            for w in self.w_p: unikalne_m_y.add(self._parsuj_rok_miesiac(w[0], 'p'))
            for w in self.w_dso: unikalne_m_y.add(self._parsuj_rok_miesiac(w[0], 'd'))
            for w in self.w_k: unikalne_m_y.add(self._parsuj_rok_miesiac(w[0], 'k'))

            if (0, 0) in unikalne_m_y: unikalne_m_y.remove((0, 0))
            miesiace_posortowane = sorted(list(unikalne_m_y))

            for idx, (rok, miesiac) in enumerate(miesiace_posortowane):
                if idx > 0:
                    elementy.append(PageBreak())

                tytul_mc = f"------------ {miesiace_nazwy[miesiac]} {rok} ------------"
                elementy.append(Paragraph(tytul_mc, styl_miesiaca))

                w_s_mc = [w for w in self.w_s if self._parsuj_rok_miesiac(w[0], 's') == (rok, miesiac)]
                w_p_mc = [w for w in self.w_p if self._parsuj_rok_miesiac(w[0], 'p') == (rok, miesiac)]
                w_dso_mc = [w for w in self.w_dso if self._parsuj_rok_miesiac(w[0], 'd') == (rok, miesiac)]
                w_k_mc = [w for w in self.w_k if self._parsuj_rok_miesiac(w[0], 'k') == (rok, miesiac)]

                dodaj_sekcje("Słońce oraz Księżyc", self.n_s, w_s_mc)
                dodaj_sekcje("Efemerydy Planetarne", self.n_p, w_p_mc)
                dodaj_sekcje("Katalog Obiektów Messiera", self.n_dso, w_dso_mc)
                dodaj_sekcje("Szczegółowe Kalendarium Zjawisk", self.n_k, w_k_mc)

            doc.build(elementy)
            messagebox.showinfo("Sukces", "Dokument PDF został wygenerowany pomyślnie!")

        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas generowania PDF:\n{e}")

    def eksportuj_csv(self):
        plik_bazowy = filedialog.asksaveasfilename(
            title="Zapisz raporty jako",
            defaultextension=".csv",
            filetypes=[("Pliki CSV", "*.csv")],
            initialfile="Raport_Astronomiczny.csv"
        )
        if not plik_bazowy:
            return

        rdzen, rozszerzenie = os.path.splitext(plik_bazowy)
        dane_do_zapisu = [
            ("_Slonce_i_Ksiezyc", self.n_s, self.w_s),
            ("_Planety", self.n_p, self.w_p),
            ("_Kalendarium", self.n_k, self.w_k),
            ("_DSO", self.n_dso, self.w_dso)
        ]

        try:
            zapisane_pliki = 0
            for sufiks, naglowki, wiersze in dane_do_zapisu:
                if not wiersze: continue
                sciezka = f"{rdzen}{sufiks}{rozszerzenie}"
                with open(sciezka, mode='w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow(naglowki)
                    writer.writerows(wiersze)
                zapisane_pliki += 1
            messagebox.showinfo("Sukces", f"Zapisano {zapisane_pliki} plików CSV!")
        except Exception as e:
            messagebox.showerror("Błąd zapisu", f"Wystąpił błąd:\n{e}")