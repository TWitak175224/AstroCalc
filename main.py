import tkinter as tk
from StartPanel import StartPanel
from PanelWynikow import PanelWynikow
import oblicznie_planet

class GlownaAplikacja:
    def __init__(self, root):
        self.root = root
        self.root.title("Kalkulator Astronomiczny")
        self.root.geometry("1100x700")

        self.panel_startowy = StartPanel(self.root, self.odbierz_dane_z_gui)
        self.panel_wynikow = PanelWynikow(self.root, self.wroc_do_startu)

        self.panel_startowy.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def odbierz_dane_z_gui(self, config):
        geopos = (config['lon_dd'], config['lat_dd'], config['elev'])

        w_s, n_s, w_p, n_p, w_k, n_k, w_dso, n_dso = oblicznie_planet.generuj_raport(
            geopos, config['rok'], config['miesiac'], config['dzien'],
            config['dni_do_analizy'], config['timezone'], config['krok_planety'],
            config['obiekty_dso'] # <-- Lecą nasze emki!
        )

        self.pokaz_panel_wynikow(w_s, n_s, w_p, n_p, w_k, n_k, w_dso, n_dso)

    def pokaz_panel_wynikow(self, w_s, n_s, w_p, n_p, w_k, n_k, w_dso, n_dso):
        self.panel_startowy.pack_forget()
        self.panel_wynikow.zaladuj_dane(w_s, n_s, w_p, n_p, w_k, n_k, w_dso, n_dso)
        self.panel_wynikow.pack(fill=tk.BOTH, expand=True)

    def wroc_do_startu(self):
        self.panel_wynikow.pack_forget()
        self.panel_startowy.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = GlownaAplikacja(root)
    root.mainloop()