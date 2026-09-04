import tkinter as tk
from StartPanel import StartPanel
from PanelWynikow import PanelWynikow
from PanelKosmogramu import PanelKosmogramu
import oblicznie_planet
import obliczanie_kosmogramu


class GlownaAplikacja:
    def __init__(self, root):
        self.root = root
        self.root.title("Kalkulator Astronomiczny i Astrologiczny")
        self.root.geometry("1100x800")

        self.panel_startowy = StartPanel(self.root, self.odbierz_dane_z_gui)
        self.panel_wynikow = PanelWynikow(self.root, self.wroc_do_startu)
        self.panel_kosmogramu = PanelKosmogramu(self.root, self.wroc_do_startu)

        self.panel_startowy.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def odbierz_dane_z_gui(self, config):
        if config.get("tryb") == "kosmogram":

            planety, domy, aspekty = obliczanie_kosmogramu.generuj_kosmogram(config)

            self.panel_startowy.pack_forget()
            self.panel_kosmogramu.zaladuj_dane(planety, domy, aspekty)
            self.panel_kosmogramu.pack(fill=tk.BOTH, expand=True)

        else:
            # --- TRYB EFEMERYD ---
            geopos = (config['lon_dd'], config['lat_dd'], config['elev'])

            w_s, n_s, w_p, n_p, w_k, n_k, w_dso, n_dso = oblicznie_planet.generuj_raport(
                geopos, config['rok'], config['miesiac'], config['dzien'],
                config['dni_do_analizy'], config['timezone'], config['krok_planety'],
                config['obiekty_dso'], config['okienko_koniunkcji'], config['zjawiska']
            )

            self.panel_startowy.pack_forget()
            self.panel_wynikow.zaladuj_dane(w_s, n_s, w_p, n_p, w_k, n_k, w_dso, n_dso, config)
            self.panel_wynikow.pack(fill=tk.BOTH, expand=True)

    def wroc_do_startu(self):
        self.panel_wynikow.pack_forget()
        self.panel_kosmogramu.pack_forget()
        self.panel_startowy.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)


if __name__ == "__main__":
    root = tk.Tk()
    app = GlownaAplikacja(root)
    root.mainloop()