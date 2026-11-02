import os
import ctypes
import tkinter as tk
from tkinter import ttk
from konfiguracja_app import sciezka_do_zasobu, VERSION
from narzedzia import sprawdz_aktualizacje, sprawdz_aktualizacje_bazy
from modele import DatabaseModel
from widoki import MainView
from kontrolery import MainController

def pokaz_splash_screen(root, po_zakonczeniu_callback):
    root.withdraw()
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.configure(bg="white")
    
    splash_w, splash_h = 500, 250
    screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
    x = (screen_w // 2) - (splash_w // 2)
    y = (screen_h // 2) - (splash_h // 2)
    splash.geometry(f"{splash_w}x{splash_h}+{x}+{y}")
    
    lbl_title = tk.Label(splash, text="KALKULATOR ROZRUCHU\nDIAMEL", font=("Arial", 20, "bold"), bg="white", fg="#2196F3")
    lbl_title.pack(expand=True)
        
    style = ttk.Style()
    if 'clam' in style.theme_names():
        style.theme_use('clam')
    style.configure("TProgressbar", thickness=6)
    
    progress = ttk.Progressbar(splash, orient="horizontal", length=400, mode="determinate", style="TProgressbar")
    progress.pack(side="bottom", pady=(15, 20))
    
    lbl_status = tk.Label(splash, text="Inicjalizacja środowiska bazowego...", font=("Arial", 10, "italic"), bg="white", fg="gray")
    lbl_status.pack(side="bottom")
    
    komunikaty = [
        (0, "Inicjalizacja środowiska bazowego..."),
        (30, "Ładowanie logiki spadków napięć..."),
        (60, "Wczytywanie bazy JSON rozruszników i baterii..."),
        (100, "Uruchamianie interfejsu MVC...")
    ]
    
    def aktualizuj_postep(krok=0):
        if krok <= 100:
            progress['value'] = krok
            for prog, text in reversed(komunikaty):
                if krok >= prog:
                    lbl_status.config(text=text)
                    break
            splash.after(20, aktualizuj_postep, krok + 1)
        else:
            splash.destroy()
            root.deiconify()
            po_zakonczeniu_callback()

    aktualizuj_postep(0)

def start_aplikacji(root):
    root.title(f"Kalkulator Układów Rozruchowych (Baterii) v{VERSION}")
    root.geometry("800x650")
    
    db_model = DatabaseModel()
    view = MainView(root, db_model)
    controller = MainController(view, db_model)
    
    sprawdz_aktualizacje(root, tryb="w_tle")
    sprawdz_aktualizacje_bazy(root, controller, tryb="w_tle")

if __name__ == "__main__":
    try:
        myappid = "diamel.kalkulator_rozruchu.main"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    root = tk.Tk()
    pokaz_splash_screen(root, lambda: start_aplikacji(root))
    root.mainloop()