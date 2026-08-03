import tkinter as tk
import StartPanel
import oblicznie_planet


class GlownaAplikacja:
    def __init__(self, root):
        self.root = root
        self.root.title("AstroKalkulator")
        self.root.geometry("400x350")

        # Inicjalizacja panelu z przekazaniem metody odbiorczej (callback)
        self.panel_startowy = StartPanel.StartPanel(self.root, self.odbierz_dane_z_gui)
        self.panel_startowy.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def odbierz_dane_z_gui(self, config):
        """Ta funkcja zostanie wywołana przez przycisk w StartPanel"""
        print("--- Odebrano dane z GUI ---")
        print(f"Data startu: {config['rok']}-{config['miesiac']}-{config['dzien']}")
        print(f"Czasokres: {config['dni_do_analizy']} dni")
        print(f"Koordynaty DD: Lat={config['lat_dd']:.4f}, Lon={config['lon_dd']:.4f}")

        # Tutaj wywołujesz swój silnik obliczeniowy, np.:
        geopos = (config['lon_dd'], config['lat_dd'], 100.0) # Kolejność pyswisseph!
        wyniki = oblicznie_planet.generuj_raport(geopos,config['rok'],config['miesiac'],config['dzien'],config['dni_do_analizy'])

        # Opcjonalnie: przejście do następnego widoku (np. tabeli wyników)
        # self.panel_startowy.pack_forget()
        # self.pokaz_panel_wynikow(wyniki)


if __name__ == "__main__":
    root = tk.Tk()
    app = GlownaAplikacja(root)
    root.mainloop()