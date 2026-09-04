import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    REPORTLAB_DOSTEPNY = True
except ImportError:
    REPORTLAB_DOSTEPNY = False


class PanelWynikow(tk.Frame):
    def __init__(self, parent, on_back_callback):
        super().__init__(parent)
        self.on_back_callback = on_back_callback

        self.w_s, self.n_s = [], []
        self.w_p, self.n_p = [], []
        self.w_k, self.n_k = [], []
        self.w_dso, self.n_dso = [], []
        self.config_dane = None

        self.miesiace_nazwy = ["", "STYCZEŃ", "LUTY", "MARZEC", "KWIECIEŃ", "MAJ", "CZERWIEC",
                               "LIPIEC", "SIERPIEŃ", "WRZESIEŃ", "PAŹDZIERNIK", "LISTOPAD", "GRUDZIEŃ"]

        self.setup_ui()

    def setup_ui(self):
        panel_gorny = tk.Frame(self)
        panel_gorny.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        tk.Button(panel_gorny, text="< Wróć do ustawień", command=self.on_back_callback,
                  font=("Helvetica", 10)).pack(side=tk.LEFT)

        tk.Button(panel_gorny, text="Eksportuj do PDF", command=self.eksportuj_pdf,
                  bg="#F44336", fg="white", font=("Helvetica", 10, "bold")).pack(side=tk.RIGHT, padx=5)

        tk.Button(panel_gorny, text="Eksportuj do CSV", command=self.eksportuj_csv,
                  bg="#2196F3", fg="white", font=("Helvetica", 10, "bold")).pack(side=tk.RIGHT, padx=5)

        self.main_notebook = ttk.Notebook(self)
        self.main_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _parsuj_rok_miesiac(self, data_str, typ):
        try:
            # Sprawdzamy czy to format YYYY-MM-DD (Zjawiska)
            if '-' in data_str[:10]:
                parts = data_str[:10].split('-')
                if len(parts) >= 2:
                    return int(parts[0]), int(parts[1])
            # Sprawdzamy czy to format DD.MM.YYYY (Słońce, Planety, DSO)
            elif '.' in data_str[:10]:
                parts = data_str[:10].split('.')
                if len(parts) == 3:
                    return int(parts[2]), int(parts[1])
        except:
            pass
        return 0, 0

    def _pobierz_posortowane_miesiace(self):
        unikalne_m_y = set()
        for w in self.w_s: unikalne_m_y.add(self._parsuj_rok_miesiac(w[0], 's'))
        for w in self.w_p: unikalne_m_y.add(self._parsuj_rok_miesiac(w[0], 'p'))
        for w in self.w_dso: unikalne_m_y.add(self._parsuj_rok_miesiac(w[0], 'd'))
        for w in self.w_k: unikalne_m_y.add(self._parsuj_rok_miesiac(w[0], 'k'))

        if (0, 0) in unikalne_m_y: unikalne_m_y.remove((0, 0))
        miesiace_posortowane = sorted(list(unikalne_m_y))

        if not miesiace_posortowane:
            miesiace_posortowane = [(datetime.now().year, datetime.now().month)]

        return miesiace_posortowane

    def stworz_tabele(self, parent):
        scroll_y = ttk.Scrollbar(parent, orient=tk.VERTICAL)
        scroll_x = ttk.Scrollbar(parent, orient=tk.HORIZONTAL)

        tree = ttk.Treeview(parent, yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set, show="headings")

        scroll_y.config(command=tree.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        scroll_x.config(command=tree.xview)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        return tree

    def wypelnij_tabele(self, tree, naglowki, wiersze):
        tree.delete(*tree.get_children())
        tree["columns"] = naglowki

        tree.tag_configure('parzysty', background='#FFFFFF')
        tree.tag_configure('nieparzysty', background='#F2F2F2')

        for n in naglowki:
            tree.heading(n, text=n)
            tree.column(n, anchor=tk.CENTER, width=120)

        for indeks, w in enumerate(wiersze):
            tag = 'parzysty' if indeks % 2 == 0 else 'nieparzysty'
            tree.insert("", tk.END, values=w, tags=(tag,))

    def zaladuj_dane(self, w_s, n_s, w_p, n_p, w_k, n_k, w_dso, n_dso, config=None):
        self.w_s, self.n_s = w_s, n_s
        self.w_p, self.n_p = w_p, n_p
        self.w_k, self.n_k = w_k, n_k
        self.w_dso, self.n_dso = w_dso, n_dso
        self.config_dane = config

        for tab in self.main_notebook.tabs():
            self.main_notebook.forget(tab)

        miesiace_posortowane = self._pobierz_posortowane_miesiace()

        pokaz_kalendarium = False
        pokaz_dso = False
        if self.config_dane:
            pokaz_kalendarium = any(self.config_dane.get('zjawiska', {}).values())
            pokaz_dso = len(self.config_dane.get('obiekty_dso', [])) > 0

        for rok, miesiac in miesiace_posortowane:
            nazwa_zakladki = f"{self.miesiace_nazwy[miesiac]} {rok}"
            tab_mc = ttk.Frame(self.main_notebook)
            self.main_notebook.add(tab_mc, text=nazwa_zakladki)

            sub_notebook = ttk.Notebook(tab_mc)
            sub_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            f_slonce = ttk.Frame(sub_notebook)
            sub_notebook.add(f_slonce, text="Słońce i Księżyc")
            tree_s = self.stworz_tabele(f_slonce)
            w_s_mc = [w for w in self.w_s if self._parsuj_rok_miesiac(w[0], 's') == (rok, miesiac)]
            self.wypelnij_tabele(tree_s, self.n_s, w_s_mc)

            f_planety = ttk.Frame(sub_notebook)
            sub_notebook.add(f_planety, text="Planety")
            tree_p = self.stworz_tabele(f_planety)
            w_p_mc = [w for w in self.w_p if self._parsuj_rok_miesiac(w[0], 'p') == (rok, miesiac)]
            self.wypelnij_tabele(tree_p, self.n_p, w_p_mc)

            if pokaz_kalendarium:
                f_kal = ttk.Frame(sub_notebook)
                sub_notebook.add(f_kal, text="Kalendarium Zjawisk")
                tree_k = self.stworz_tabele(f_kal)
                w_k_mc = [w for w in self.w_k if self._parsuj_rok_miesiac(w[0], 'k') == (rok, miesiac)]
                self.wypelnij_tabele(tree_k, self.n_k, w_k_mc)

            if pokaz_dso:
                f_dso = ttk.Frame(sub_notebook)
                sub_notebook.add(f_dso, text="Katalog DSO")
                tree_d = self.stworz_tabele(f_dso)
                w_dso_mc = [w for w in self.w_dso if self._parsuj_rok_miesiac(w[0], 'd') == (rok, miesiac)]
                self.wypelnij_tabele(tree_d, self.n_dso, w_dso_mc)

    def eksportuj_csv(self):
        domyslna_nazwa = "raport_astronomiczny"
        if self.w_s:
            data_od = self.w_s[0][0].replace('.', '-')
            data_do = self.w_s[-1][0].replace('.', '-')
            domyslna_nazwa = f"raport_astronomiczny_{data_od}_do_{data_do}"

        plik = filedialog.asksaveasfilename(
            title="Zapisz raport CSV jako",
            initialfile=domyslna_nazwa,
            defaultextension=".csv",
            filetypes=[("Plik CSV", "*.csv")]
        )
        if not plik: return
        try:
            with open(plik, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')

                miesiace_posortowane = self._pobierz_posortowane_miesiace()

                for rok, miesiac in miesiace_posortowane:
                    nazwa_mc = f"----- {self.miesiace_nazwy[miesiac]} {rok} -----"
                    writer.writerow([nazwa_mc])

                    w_s_mc = [w for w in self.w_s if self._parsuj_rok_miesiac(w[0], 's') == (rok, miesiac)]
                    w_p_mc = [w for w in self.w_p if self._parsuj_rok_miesiac(w[0], 'p') == (rok, miesiac)]
                    w_k_mc = [w for w in self.w_k if self._parsuj_rok_miesiac(w[0], 'k') == (rok, miesiac)]
                    w_dso_mc = [w for w in self.w_dso if self._parsuj_rok_miesiac(w[0], 'd') == (rok, miesiac)]

                    if w_s_mc:
                        writer.writerow(["--- SŁOŃCE I KSIĘŻYC ---"])
                        writer.writerow(self.n_s)
                        writer.writerows(w_s_mc)
                        writer.writerow([])

                    if w_p_mc:
                        writer.writerow(["--- PLANETY ---"])
                        writer.writerow(self.n_p)
                        writer.writerows(w_p_mc)
                        writer.writerow([])

                    if w_k_mc:
                        writer.writerow(["--- KALENDARIUM ZJAWISK ---"])
                        writer.writerow(self.n_k)
                        writer.writerows(w_k_mc)
                        writer.writerow([])

                    if w_dso_mc:
                        writer.writerow(["--- KATALOG DSO ---"])
                        writer.writerow(self.n_dso)
                        writer.writerows(w_dso_mc)
                        writer.writerow([])

                    writer.writerow([])

            messagebox.showinfo("Sukces", "Dane zapisane do pliku CSV.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać CSV: {e}")

    def eksportuj_pdf(self):
        if not REPORTLAB_DOSTEPNY:
            messagebox.showerror("Brak biblioteki", "Zainstaluj ReportLab:\npip install reportlab")
            return

        data_od_str = self.w_s[0][0] if self.w_s else "Brak danych"
        data_do_str = self.w_s[-1][0] if self.w_s else "Brak danych"
        domyslna_nazwa = f"raport_astronomiczny_{data_od_str.replace('.', '-')}_do_{data_do_str.replace('.', '-')}"

        plik = filedialog.asksaveasfilename(
            title="Zapisz raport PDF jako",
            initialfile=domyslna_nazwa,
            defaultextension=".pdf",
            filetypes=[("Plik PDF", "*.pdf")]
        )
        if not plik: return

        try:
            try:
                pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
                pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))
                font_reg = 'Arial'
                font_bld = 'Arial-Bold'
            except Exception:
                font_reg = 'Helvetica'
                font_bld = 'Helvetica-Bold'

            doc = SimpleDocTemplate(plik, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20,
                                    bottomMargin=20)
            elementy = []
            styles = getSampleStyleSheet()

            styl_tytulu = styles['Heading2']
            styl_tytulu.fontName = font_bld

            styl_okladka_tytul = ParagraphStyle(
                'OkladkaTytul',
                parent=styles['Title'],
                fontName=font_bld,
                fontSize=32,
                leading=40,
                alignment=TA_CENTER,
                spaceAfter=30
            )

            styl_okladka_tekst = ParagraphStyle(
                'OkladkaTekst',
                parent=styles['Normal'],
                fontName=font_reg,
                fontSize=18,
                leading=26,
                alignment=TA_CENTER,
                spaceAfter=40
            )

            styl_miesiaca = ParagraphStyle(
                'MiesiacTytul',
                parent=styles['Heading1'],
                fontName=font_bld,
                fontSize=18,
                alignment=TA_CENTER,
                spaceBefore=25,
                spaceAfter=15,
                textColor=colors.HexColor("#2C3E50")
            )

            lat_val = self.config_dane.get("lat_dd", 0.0) if self.config_dane else 0.0
            lon_val = self.config_dane.get("lon_dd", 0.0) if self.config_dane else 0.0

            lat_format = f"{abs(lat_val):.4f}° {'N' if lat_val >= 0 else 'S'}"
            lon_format = f"{abs(lon_val):.4f}° {'E' if lon_val >= 0 else 'W'}"

            elementy.append(Spacer(1, 100))
            elementy.append(Paragraph("Raport Astronomiczny", styl_okladka_tytul))
            elementy.append(
                Paragraph(f"dla dat z zakresu:<br/><b>{data_od_str}  -  {data_do_str}</b>", styl_okladka_tekst))
            elementy.append(Paragraph(f"dla miejsca:<br/><b>Szerokość: {lat_format}<br/>Długość: {lon_format}</b>",
                                      styl_okladka_tekst))

            elementy.append(PageBreak())

            def dodaj_tabele(naglowki, wiersze, tytul, max_kolumn=6):
                if not naglowki or not wiersze: return

                def zrob_tabele(dane):
                    t = Table(dane)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), font_bld),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('FONTNAME', (0, 1), (-1, -1), font_reg),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ]))
                    return t

                if len(naglowki) <= max_kolumn + 1:
                    elementy.append(Paragraph(tytul, styl_tytulu))
                    elementy.append(zrob_tabele([naglowki] + wiersze))
                    elementy.append(Spacer(1, 20))
                else:
                    for i in range(1, len(naglowki), max_kolumn):
                        frag_naglowkow = [naglowki[0]] + naglowki[i:i + max_kolumn]
                        frag_wierszy = [[w[0]] + list(w[i:i + max_kolumn]) for w in wiersze]

                        czesc = (i // max_kolumn) + 1
                        elementy.append(Paragraph(f"{tytul} (cz. {czesc})", styl_tytulu))
                        elementy.append(zrob_tabele([frag_naglowkow] + frag_wierszy))
                        elementy.append(Spacer(1, 20))

            miesiace_posortowane = self._pobierz_posortowane_miesiace()

            for index, (rok, miesiac) in enumerate(miesiace_posortowane):
                if index > 0:
                    elementy.append(PageBreak())

                nazwa_mc = f"----- {self.miesiace_nazwy[miesiac]} {rok} -----"
                elementy.append(Paragraph(nazwa_mc, styl_miesiaca))

                w_s_mc = [w for w in self.w_s if self._parsuj_rok_miesiac(w[0], 's') == (rok, miesiac)]
                w_p_mc = [w for w in self.w_p if self._parsuj_rok_miesiac(w[0], 'p') == (rok, miesiac)]
                w_k_mc = [w for w in self.w_k if self._parsuj_rok_miesiac(w[0], 'k') == (rok, miesiac)]
                w_dso_mc = [w for w in self.w_dso if self._parsuj_rok_miesiac(w[0], 'd') == (rok, miesiac)]

                if w_s_mc: dodaj_tabele(self.n_s, w_s_mc, "Słońce i Księżyc", max_kolumn=10)
                if w_p_mc: dodaj_tabele(self.n_p, w_p_mc, "Planety", max_kolumn=10)
                if w_k_mc: dodaj_tabele(self.n_k, w_k_mc, "Kalendarium Zjawisk", max_kolumn=10)
                if w_dso_mc: dodaj_tabele(self.n_dso, w_dso_mc, "Katalog DSO", max_kolumn=8)

            doc.build(elementy)
            messagebox.showinfo("Sukces", "Dokument PDF został wygenerowany pomyślnie.")

        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił problem z generowaniem PDF:\n{e}")