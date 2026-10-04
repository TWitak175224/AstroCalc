"""
Główny moduł uruchomieniowy (Entry Point) aplikacji astronomiczno-astrologicznej.
Zaprojektowany w oparciu o wzorzec architektoniczny MVC (Model-View-Controller),
gdzie klasa GlownaAplikacja pełni rolę Kontrolera (Controller)[cite: 10].
Zarządza cyklem życia okien, przełączaniem widoków (Views) oraz deleguje
obliczenia do odpowiednich silników matematycznych (Models)[cite: 10].
"""

import tkinter as tk
from StartPanel import StartPanel
from PanelWynikow import PanelWynikow
from PanelKosmogramu import PanelKosmogramu
import oblicznie_planet
import obliczanie_kosmogramu


class GlownaAplikacja:
    """
    Główna klasa orkiestrująca działanie programu[cite: 10].
    Odpowiada za inicjalizację głównego okna Tkinter, przetrzymywanie instancji
    paneli interfejsu użytkownika oraz implementację logiki przełączania
    między ekranami za pomocą menedżera geometrii (pack/pack_forget)[cite: 10].
    """

    def __init__(self, root):
        """
        Konstruktor inicjalizujący główne okno programu oraz ładujący widoki[cite: 10].
        Widoki (StartPanel, PanelWynikow, PanelKosmogramu) otrzymują w parametrach
        wskaźniki do metod zwrotnych (callbacks), co zapobiega ścisłemu powiązaniu
        (tight coupling) między komponentami interfejsu[cite: 10].
        """
        self.root = root
        self.root.title("Kalkulator Astronomiczny i Astrologiczny")
        self.root.geometry("1100x800")

        # Inicjalizacja paneli z przekazaniem funkcji zwrotnych (callbacks)[cite: 10]
        self.panel_startowy = StartPanel(self.root, self.odbierz_dane_z_gui)
        self.panel_wynikow = PanelWynikow(self.root, self.wroc_do_startu)
        self.panel_kosmogramu = PanelKosmogramu(self.root, self.wroc_do_startu)

        # Wyświetlenie ekranu domyślnego[cite: 10]
        self.panel_startowy.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def odbierz_dane_z_gui(self, config):
        """
        Główny router (dyspozytor) aplikacji[cite: 10].
        Odbiera zebrany słownik konfiguracyjny ze StartPanelu, weryfikuje tryb
        działania (efemerydy vs kosmogram), uruchamia odpowiedni silnik obliczeniowy,
        a po wyliczeniu danych - przełącza aktywny widok na ekran wyników[cite: 10].

        Uwaga na współbieżność: Metoda ta jest bezpiecznie wywoływana przez
        moduł threading ze StartPanelu, co zapobiega zjawisku "zamarzania" GUI.
        """
        if config.get("tryb") == "kosmogram":
            # Uruchomienie silnika astrologicznego[cite: 10]
            planety, domy, aspekty = obliczanie_kosmogramu.generuj_kosmogram(config)

            # Przełączenie kontekstu wizualnego na widok kosmogramu[cite: 10]
            self.panel_startowy.pack_forget()
            self.panel_kosmogramu.zaladuj_dane(planety, domy, aspekty)
            self.panel_kosmogramu.pack(fill=tk.BOTH, expand=True)

        else:
            # --- TRYB EFEMERYD ---
            geopos = (config['lon_dd'], config['lat_dd'], config['elev'])

            # Uruchomienie silnika astronomicznego[cite: 10]
            w_s, n_s, w_p, n_p, w_k, n_k, w_dso, n_dso = oblicznie_planet.generuj_raport(
                geopos, config['rok'], config['miesiac'], config['dzien'],
                config['dni_do_analizy'], config['timezone'], config['krok_planety'],
                config['obiekty_dso'], config['okienko_koniunkcji'], config['zjawiska']
            )

            # Przełączenie kontekstu wizualnego na tabele efemeryd[cite: 10]
            self.panel_startowy.pack_forget()
            self.panel_wynikow.zaladuj_dane(w_s, n_s, w_p, n_p, w_k, n_k, w_dso, n_dso, config)
            self.panel_wynikow.pack(fill=tk.BOTH, expand=True)

    def wroc_do_startu(self):
        """
        Metoda zwrotna (callback) przywracająca aplikację do stanu początkowego[cite: 10].
        Ukrywa aktywne panele wynikowe i ponownie ładuje panel startowy[cite: 10].
        """
        self.panel_wynikow.pack_forget()
        self.panel_kosmogramu.pack_forget()
        self.panel_startowy.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)


if __name__ == "__main__":
    # Inicjalizacja środowiska graficznego Tkinter i pętli zdarzeń (Event Loop)[cite: 10]
    root = tk.Tk()
    app = GlownaAplikacja(root)
    root.mainloop()