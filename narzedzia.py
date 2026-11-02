import os
import json
import urllib.request
import threading
import subprocess
import tempfile
import smtplib
import shutil
from email.message import EmailMessage
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from konfiguracja_app import VERSION, DB_VERSION, EMAIL_NADAWCY, HASLO_NADAWCY, EMAIL_ODBIORCY, SMTP_SERVER, SMTP_PORT

# ----------------- AKTUALIZACJE PROGRAMU -----------------
def sprawdz_aktualizacje(root, tryb="recznie"):
    def task():
        url_json = "https://diamel.pl/kalkulator_rozruchu/changelog/wersja.json"
        try:
            req = urllib.request.Request(url_json, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4.0) as response:
                dane = json.loads(response.read().decode('utf-8'))
                wersja_serwera = dane.get("najnowszawersja", "0.0.0")
                changelog = dane.get("changelog", "Brak informacji o nowościach.")
                link = dane.get("link", "")
                
                def wez_krotke(v): return tuple(map(int, (v.split(" ")[0]).split(".")))
                    
                if wez_krotke(wersja_serwera) > wez_krotke(VERSION) and link:
                    root.after(0, lambda: pokaz_monit_aktualizacji(root, wersja_serwera, link, changelog))
                elif tryb == "recznie":
                    msg = f"Posiadasz najnowszą dostępną wersję programu!\n\nTwoja wersja: {VERSION}\nWersja na serwerze: {wersja_serwera}"
                    root.after(0, lambda: messagebox.showinfo("Aktualizacje Programu", msg, parent=root))
        except Exception as e:
            if tryb == "recznie":
                root.after(0, lambda: messagebox.showerror("Błąd połączenia", f"Nie udało się połączyć z serwerem.\nSzczegóły: {e}", parent=root))
    threading.Thread(target=task, daemon=True).start()

def pokaz_monit_aktualizacji(root, nowa_wersja, link, changelog):
    odp = messagebox.askyesno("Nowa wersja programu!", f"Dostępna jest nowa wersja programu: {nowa_wersja} (Twoja: {VERSION})\n\nCO NOWEGO:\n{changelog}\n\nCzy chcesz pobrać i zainstalować aktualizację?", parent=root)
    if odp: pobierz_i_zainstaluj(root, link)

def pobierz_i_zainstaluj(root, link):
    okno_pob = tk.Toplevel(root)
    okno_pob.title("Aktualizacja Kalkulatora")
    okno_pob.geometry("400x180")
    okno_pob.grab_set()

    lbl = tk.Label(okno_pob, text="Trwa pobieranie aktualizacji...", font=("Arial", 10, "bold"))
    lbl.pack(pady=15)
    
    pasek = ttk.Progressbar(okno_pob, mode='indeterminate', length=300)
    pasek.pack(pady=5)
    pasek.start()

    def start_update():
        sciezka_temp = os.path.join(tempfile.gettempdir(), "Aktualizacja_Rozruch_Instalator.exe")
        try:
            subprocess.run(['powershell', '-Command', f'Unblock-File -Path \'{sciezka_temp}\''], shell=True)
            subprocess.Popen([sciezka_temp, "/FORCECLOSEAPPLICATIONS", "/NOCANCEL"])
            os._exit(0)
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się uruchomić instalatora: {e}", parent=okno_pob)

    btn_start = tk.Button(okno_pob, text="URUCHOM INSTALATOR", command=start_update, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), height=2)

    def download_thread():
        try:
            sciezka_temp = os.path.join(tempfile.gettempdir(), "Aktualizacja_Rozruch_Instalator.exe")
            urllib.request.urlretrieve(link, sciezka_temp)
            def pokaz_przycisk():
                pasek.stop()
                pasek.pack_forget()
                lbl.config(text="Aktualizacja pobrana pomyślnie!")
                btn_start.pack(pady=15, fill="x", padx=40)
            okno_pob.after(0, pokaz_przycisk)
        except Exception as e:
            okno_pob.after(0, lambda: messagebox.showerror("Błąd", f"Nie udało się pobrać aktualizacji: {e}", parent=okno_pob))
            okno_pob.after(0, okno_pob.destroy)

    threading.Thread(target=download_thread, daemon=True).start()


# ----------------- AKTUALIZACJE BAZY DANYCH -----------------
def sprawdz_aktualizacje_bazy(root, controller, tryb="recznie"):
    def task():
        url_json = "https://diamel.pl/kalkulator_rozruchu/changelog/wersja.json"
        try:
            req = urllib.request.Request(url_json, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4.0) as response:
                dane = json.loads(response.read().decode('utf-8'))
                wersja_bazy_serwera = dane.get("wersja_bazy", "0.0.0")
                changelog_bazy = dane.get("changelog_bazy", "Brak informacji.")
                
                def wez_krotke(v): return tuple(map(int, (v.split(" ")[0]).split(".")))
                    
                if wez_krotke(wersja_bazy_serwera) > wez_krotke(DB_VERSION):
                    root.after(0, lambda: pokaz_monit_bazy(root, controller, wersja_bazy_serwera, changelog_bazy))
                elif tryb == "recznie":
                    msg = f"Posiadasz najnowszą bazę danych!\n\nTwoja wersja: {DB_VERSION}\nWersja na serwerze: {wersja_bazy_serwera}"
                    root.after(0, lambda: messagebox.showinfo("Aktualizacje Bazy", msg, parent=root))
        except Exception as e:
            if tryb == "recznie":
                root.after(0, lambda: messagebox.showerror("Błąd połączenia", f"Nie udało się połączyć z serwerem.\nSzczegóły: {e}", parent=root))
    threading.Thread(target=task, daemon=True).start()

def pokaz_monit_bazy(root, controller, nowa_wersja, changelog):
    odp = messagebox.askyesno("Nowa wersja Bazy Danych!", f"Wydano nową bazę danych: {nowa_wersja} (Twoja: {DB_VERSION})\n\nZMIANY W BAZIE:\n{changelog}\n\nCzy chcesz pobrać i scalić nową bazę z Twoimi danymi?", parent=root)
    if odp: 
        chce_kopie = messagebox.askyesno("Kopia zapasowa", "Zanim zaktualizuję dane, czy chcesz utworzyć kopię zapasową swojej obecnej bazy danych?", parent=root)
        pobierz_i_scal_baze(root, controller, chce_kopie)

def pobierz_i_scal_baze(root, controller, zrob_kopie):
    def task():
        try:
            url_starters = "https://diamel.pl/kalkulator_rozruchu/aplikacja/data/starters.json"
            url_batteries = "https://diamel.pl/kalkulator_rozruchu/aplikacja/data/batteries.json"
            
            nowe_starters, nowe_batteries = {}, {}
            
            try:
                req_s = urllib.request.Request(url_starters, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req_s, timeout=10.0) as resp:
                    nowe_starters = json.loads(resp.read().decode('utf-8')).get("starters", {})
            except: pass
            
            try:
                req_b = urllib.request.Request(url_batteries, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req_b, timeout=10.0) as resp:
                    nowe_batteries = json.loads(resp.read().decode('utf-8')).get("batteries", {})
            except: pass

            db_model = controller.db_model
            bkp_name = ""
            
            if zrob_kopie:
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                if os.path.exists(db_model.starters_file):
                    shutil.copy(db_model.starters_file, db_model.starters_file + f".{ts}.bak")
                    bkp_name += f"starters.json.{ts}.bak\n"
                if os.path.exists(db_model.batteries_file):
                    shutil.copy(db_model.batteries_file, db_model.batteries_file + f".{ts}.bak")
                    bkp_name += f"batteries.json.{ts}.bak\n"
            
            if nowe_starters: db_model.starters.update(nowe_starters)
            if nowe_batteries: db_model.batteries.update(nowe_batteries)
                
            db_model.save_starters()
            db_model.save_batteries()
            
            root.after(0, lambda: controller.view.cb_starters.config(values=list(db_model.starters.keys())))
            root.after(0, lambda: controller.view.cb_batteries.config(values=list(db_model.batteries.keys())))
            
            komunikat = "Baza danych została pomyślnie zaktualizowana i scalona!"
            if zrob_kopie and bkp_name:
                komunikat += f"\n\nUtworzono pliki kopii zapasowych:\n{bkp_name}"
                
            root.after(0, lambda: messagebox.showinfo("Sukces", komunikat, parent=root))
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Błąd", f"Aktualizacja bazy nie powiodła się:\n{e}", parent=root))
    threading.Thread(target=task, daemon=True).start()


# ----------------- PROŚBA O DODANIE SPRZĘTU DO BAZY -----------------
def pokaz_okno_zgloszenia_sprzetu(root):
    pop = tk.Toplevel(root)
    pop.title("Zgłoś prośbę o dodanie sprzętu do Bazy Danych")
    pop.geometry("500x550")
    pop.grab_set()

    tk.Label(pop, text="Twój e-mail (DO KONTAKTU):", font=("Arial", 9, "bold")).pack(pady=(15, 2), anchor="w", padx=20)
    v_email = tk.StringVar()
    tk.Entry(pop, textvariable=v_email, width=45).pack(padx=20, anchor="w")

    tk.Label(pop, text="Kategoria:", font=("Arial", 9, "bold")).pack(pady=(10, 2), anchor="w", padx=20)
    v_typ = tk.StringVar(value="Rozrusznik")
    ttk.Combobox(pop, textvariable=v_typ, values=["Rozrusznik", "Akumulator"], state="readonly", width=42).pack(padx=20, anchor="w")

    tk.Label(pop, text="Producent i Model:", font=("Arial", 9, "bold")).pack(pady=(10, 2), anchor="w", padx=20)
    v_nazwa = tk.StringVar()
    tk.Entry(pop, textvariable=v_nazwa, width=45).pack(padx=20, anchor="w")

    tk.Label(pop, text="Dodatkowy opis (link do karty produktu, kluczowe parametry):", font=("Arial", 9, "bold")).pack(pady=(10, 2), anchor="w", padx=20)
    txt_opis = tk.Text(pop, width=50, height=8, font=("Arial", 9))
    txt_opis.pack(padx=20, anchor="w")

    def wyslij():
        e, n, t, o = v_email.get().strip(), v_nazwa.get().strip(), v_typ.get(), txt_opis.get("1.0", tk.END).strip()
        if not e or "@" not in e: return messagebox.showerror("Błąd", "Podaj poprawny e-mail!", parent=pop)
        if not n: return messagebox.showerror("Błąd", "Podaj nazwę modelu!", parent=pop)

        btn_wyslij.config(state="disabled", text="Wysyłanie zgłoszenia. Proszę czekać...")
        
        def task():
            try:
                msg = EmailMessage()
                msg['Subject'] = f"Prośba o dodanie do Bazy ({t}) - Kalkulator Rozruchu"
                msg['From'] = EMAIL_NADAWCY
                msg['To'] = EMAIL_ODBIORCY
                msg['Cc'] = e
                
                tresc = f"Nowa prośba o analizę i dodanie do globalnej bazy kalkulatora rozruchu:\n\n" \
                        f"Zgłaszający: {e}\n" \
                        f"Kategoria: {t}\n" \
                        f"Nazwa elementu: {n}\n\n" \
                        f"--- DODATKOWY OPIS / LINKI ---\n" \
                        f"{o}"
                        
                msg.set_content(tresc)

                with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                    server.login(EMAIL_NADAWCY, HASLO_NADAWCY)
                    server.send_message(msg)

                pop.after(0, lambda: messagebox.showinfo("Wysłano", "Prośba o dodanie sprzętu została przekazana inżynierowi. Kopia powędrowała do Ciebie na maila.\n\nDziękujemy!", parent=pop))
                pop.after(0, pop.destroy)
            except Exception as exc:
                pop.after(0, lambda: messagebox.showerror("Błąd", f"Nie udało się wysłać:\n{exc}", parent=pop))
                pop.after(0, lambda: btn_wyslij.config(state="normal", text="Wyślij do weryfikacji przez inżyniera"))
                
        threading.Thread(target=task, daemon=True).start()

    btn_wyslij = tk.Button(pop, text="Wyślij do weryfikacji przez inżyniera", command=wyslij, bg="#2196F3", fg="white", font=("Arial", 10, "bold"), height=2)
    btn_wyslij.pack(pady=25, fill="x", padx=20)