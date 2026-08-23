import tkinter as tk
from StartPanel import StartPanel
from PanelWynikow import PanelWynikow
import oblicznie_planet


class GlownaAplikacja:
    def __init__(self, root):
        self.root = root
        self.root.title("Kalkulator Astronomiczny")
        # Powiększamy okno startowe, żeby wygodnie czytać tabele
        self.root.geometry("1000x500")

        self.panel_startowy = StartPanel(self.root, self.odbierz_dane_z_gui)
        self.panel_wynikow = PanelWynikow(self.root, self.wroc_do_startu)

        self.panel_startowy.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def odbierz_dane_z_gui(self, config):
        geopos = (config['lon_dd'], config['lat_dd'], config['elev'])

        # Rozpakowujemy krotkę z dwoma elementami zwracaną przez nową funkcję
        wyniki, naglowki = oblicznie_planet.generuj_raport(geopos, config['rok'], config['miesiac'], config['dzien'],
                                                           config['dni_do_analizy'])

        self.pokaz_panel_wynikow(wyniki, naglowki)

    def pokaz_panel_wynikow(self, wyniki, naglowki):
        self.panel_startowy.pack_forget()
        self.panel_wynikow.zaladuj_dane(wyniki, naglowki)
        self.panel_wynikow.pack(fill=tk.BOTH, expand=True)

    def wroc_do_startu(self):
        self.panel_wynikow.pack_forget()
        self.panel_startowy.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def odbierz_dane_z_gui(self, config):
        geopos = (config['lon_dd'], config['lat_dd'], config['elev'])

        wyniki_s, naglowki_s, wyniki_p, naglowki_p = oblicznie_planet.generuj_raport(
            geopos, config['rok'], config['miesiac'], config['dzien'], config['dni_do_analizy']
        )

        self.pokaz_panel_wynikow(wyniki_s, naglowki_s, wyniki_p, naglowki_p)

    def pokaz_panel_wynikow(self, w_s, n_s, w_p, n_p):
        self.panel_startowy.pack_forget()
        self.panel_wynikow.zaladuj_dane(w_s, n_s, w_p, n_p)
        self.panel_wynikow.pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = GlownaAplikacja(root)
    root.mainloop()