"""
interfejs.py

Funkcje Kalkulatora Rozruchu wywoływane z okna (ui/app.js przez window.pywebview.api):
projekt, obliczenia na bieżąco, raport DOCX, baza urządzeń, aktualizacje, zgłoszenia.
"""
import base64
import json
import mimetypes
import os
import subprocess
import tempfile
import threading
import urllib.error
import urllib.request
from datetime import datetime

import webview

import obliczenia
import raport_docx
import re

from baza import Baza, KATALOG_DANYCH, KATALOG_PLIKOW, POLA_URZADZEN, PLIKI
from konto import Konto
import konto
from konfiguracja_app import VERSION, BUILD_DATE, CHANGELOG, GITHUB_REPO, NAZWA_PROGRAMU, URL_ZGLOSZEN, URL_BAZY

PLIK_USTAWIEN = os.path.join(KATALOG_DANYCH, "ustawienia.json")
NAGLOWKI = {"User-Agent": f"Diamel-{NAZWA_PROGRAMU}/{VERSION}"}
INSTALATOR = os.path.join(tempfile.gettempdir(), "Aktualizacja_Rozruch_Instalator.exe")
OSTATNIE_MAX = 8
OBRAZ_MAX_MB = 15
OBRAZY = ("curve", "batt", "diagram", "charger")

USTAWIENIA_PROGRAMU = {
    "motyw": "system",       # jasny / ciemny / system
    "rozmiar": "normalny",   # maly / normalny / duzy
    "autor": "MK",           # inicjały w nowym projekcie
    "jezyk": "English",      # język raportu w nowym projekcie
    "otworz_raport": True,   # otwórz raport w Wordzie po zapisaniu
    "ostatnie": [],          # ostatnio otwierane projekty
    "folder_raportow": "",   # ostatni folder zapisu raportu (gdy projekt nie jest zapisany)
    "szablon": "",           # plik .docx z nagłówkiem / stopką raportu (pusty = stopka programu)
    "cca_tolerancja": 10,    # dopuszczalny niedobór CCA względem karty silnika [%]
}

# Pola liczbowe projektu i wartości w nowym projekcie (jak w wersjach 1.x)
DOMYSLNE_POLA = {
    "system_v": "24", "starter_model": "", "starter_normal": "", "starter_peak": "", "starter_qty": "3", "crank_v": "16", "min_v": "",
    "batt_model": "", "batt_type": "Lead-Acid", "batt_v": "12", "batt_ah": "", "batt_cca": "", "batt_cca_norma": "", "batt_series": "2", "batt_parallel": "4",
    "cable_l": "12.5", "cable_a": "95", "cable_cores": "2", "time_s": "10", "attempts": "5", "charge_h": "3",
    "zestawy": "1", "zmiana_co": "",
    "r_test_mohm": "", "batt_rint_mohm": "",  # rezystancja obwodu testowego z karty rozrusznika, rezystancja wewnętrzna 1 akumulatora
    "cca_znane": "", "cca_silnika": "", "cca_silnika_norma": "",  # wymagane CCA z karty katalogowej silnika (pole wyboru + wartość)  # redundancja: liczba jednakowych zestawów (akumulatory + ładowarka), zmiana zestawu co N rozruchów
}


def wez_krotke(v):
    return tuple(map(int, (v.lstrip("vV").split(" ")[0]).split(".")))


def pobierz_json(url, timeout=6.0):
    req = urllib.request.Request(url, headers=NAGLOWKI)
    with urllib.request.urlopen(req, timeout=timeout) as odp:
        return json.loads(odp.read().decode("utf-8"))


def wyslij_json(url, dane, timeout=15.0):
    """POST z JSON; odpowiedź serwera (także z kodem błędu) jako słownik; brak sieci -> wyjątek."""
    req = urllib.request.Request(url, data=json.dumps(dane).encode("utf-8"), headers={**NAGLOWKI, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as odp:
            return json.loads(odp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            raise e


ZALACZNIKI_MAX_MB = 5  # limit serwera zgłoszeń (diamel.pl/api/zgloszenie.php)
ZALACZNIKI_TYPY = ("Pliki (*.pdf;*.png;*.jpg;*.jpeg;*.doc;*.docx;*.xls;*.xlsx;*.txt;*.zip)",)


def _czytaj_json(sciezka, domyslnie):
    try:
        with open(sciezka, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return domyslnie


def _zapisz_json(sciezka, dane):
    os.makedirs(os.path.dirname(sciezka), exist_ok=True)
    tymczasowy = sciezka + ".tmp"
    with open(tymczasowy, "w", encoding="utf-8") as f:
        json.dump(dane, f, ensure_ascii=False, indent=4)
    os.replace(tymczasowy, sciezka)


def _tekst(v):
    return "" if v is None else (f"{v:g}" if isinstance(v, float) else str(v))


class Api:
    def __init__(self):
        self._okno = None
        self._baza = Baza()
        self._konto = Konto()
        self.program = {**USTAWIENIA_PROGRAMU, **_czytaj_json(PLIK_USTAWIEN, {}).get("program", {})}
        self.ui_gotowe = threading.Event()
        self._niezapisane = False
        self._zamykam = False

    # ------------------------------------------------------------------ start, ustawienia

    def informacje(self):
        self.ui_gotowe.set()  # okno działa - awaryjne okienko aktualizacji (aplikacja.py) niepotrzebne
        return {"wersja": VERSION, "data": BUILD_DATE[:10], "program": self.program, "changelog": CHANGELOG.strip(),
                "baza": self.baza(), "pola_urzadzen": POLA_URZADZEN, "projekt": self.nowy_projekt(),
                "przeniesiono_baze": self._baza.przeniesiono_z, "konto": self._konto.stan()}

    # ------------------------------------------------------------------ konto Diamel (nieobowiązkowe)

    def konto_odswiez(self):
        return self._konto.odswiez()

    def konto_zaloguj(self, login, haslo, zapamietaj=True):
        return self._konto.zaloguj(login, haslo, zapamietaj)

    def zakoncz_sesje(self):
        self._konto.zakoncz_sesje()

    def konto_przypomnij(self, login):
        return self._konto.przypomnij(login)

    def konto_wyloguj(self):
        return self._konto.wyloguj()

    def _szablon(self):
        """Szablon raportu: własny z Ustawień (zastępuje firmowy) albo szablon firmy zalogowanego użytkownika; '' = stopka programu."""
        return self.program["szablon"] or self._konto.szablon

    def ustaw_program(self, klucz, wartosc):
        if klucz in USTAWIENIA_PROGRAMU:
            self.program[klucz] = wartosc
            _zapisz_json(PLIK_USTAWIEN, {"program": self.program})
        return self.program

    def _dodaj_ostatni(self, sciezka):
        lista = [p for p in self.program["ostatnie"] if os.path.normcase(p) != os.path.normcase(sciezka)]
        self.ustaw_program("ostatnie", [sciezka] + lista[:OSTATNIE_MAX - 1])

    def ostatnie(self):
        return [{"sciezka": p, "nazwa": os.path.basename(p), "folder": os.path.dirname(p),
                 "data": datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M")}
                for p in self.program["ostatnie"] if os.path.isfile(p)]

    # ------------------------------------------------------------------ aktualizacje programu

    def sprawdz_aktualizacje(self):
        """Wersja zalecana = wydanie oznaczone na GitHub jako najnowsze; starsza od zainstalowanej = wycofanie wadliwej wersji."""
        try:
            dane = pobierz_json(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest", timeout=4.0)
        except Exception as e:
            return {"ok": False, "blad": str(e)}
        wersja = dane.get("tag_name", "0.0.0").lstrip("vV")
        link = next((a["browser_download_url"] for a in dane.get("assets", []) if a["name"].lower().endswith(".exe")), "")
        try:
            nowsza = bool(link) and wez_krotke(wersja) > wez_krotke(VERSION)
            wycofana = bool(link) and wez_krotke(wersja) < wez_krotke(VERSION)
        except ValueError:
            nowsza = wycofana = False
        return {"ok": True, "nowsza": nowsza, "wycofana": wycofana, "do_instalacji": nowsza or wycofana,
                "wersja": wersja, "opis": dane.get("body") or "", "link": link}

    def pobierz_aktualizacje(self, link):
        """Pobiera instalator w tle; postęp: window.postepAktualizacji(procent), koniec: window.aktualizacjaPobrana(ok, tekst)."""
        def postep(bloki, rozmiar_bloku, calosc):
            if calosc > 0 and self._okno:
                self._okno.evaluate_js(f"window.postepAktualizacji && window.postepAktualizacji({min(100, int(bloki * rozmiar_bloku * 100 / calosc))})")

        def watek():
            try:
                urllib.request.urlretrieve(link, INSTALATOR, postep)
                self._okno.evaluate_js("window.aktualizacjaPobrana(true, '')")
            except Exception as e:
                self._okno.evaluate_js(f"window.aktualizacjaPobrana(false, {json.dumps(str(e))})")
        threading.Thread(target=watek, daemon=True).start()
        return {"ok": True}

    def uruchom_instalator(self):
        subprocess.run(["powershell", "-NoProfile", "-Command", f"Unblock-File -Path '{INSTALATOR}'"], shell=True)
        subprocess.Popen([INSTALATOR, "/FORCECLOSEAPPLICATIONS", "/NOCANCEL"])
        os._exit(0)

    # ------------------------------------------------------------------ baza urządzeń

    def baza(self):
        b = self._baza
        return {"wersja": b.wersja, **{r: b.urzadzenia(r) for r in PLIKI}, "zrodla": {r: b.zrodla(r) for r in PLIKI}}

    def sprawdz_baze(self):
        """Wersja bazy w panelu diamel.pl (numer zwiększany przy każdej zmianie) - inna niż lokalna = do pobrania."""
        try:
            dane = wyslij_json(URL_BAZY, {"akcja": "wersja", "lokalna": str(self._baza.wersja), **({"token": konto.token()} if konto.token() else {})}, timeout=6.0)
        except Exception as e:
            return {"ok": False, "blad": str(e)}
        if not dane.get("ok"):
            return {"ok": False, "blad": dane.get("blad", "Serwer bazy nie odpowiada.")}
        wersja = str(dane.get("wersja", ""))
        return {"ok": True, "nowsza": bool(wersja) and wersja != str(self._baza.wersja), "wersja": wersja, "lokalna": self._baza.wersja,
                "opis": f"Zmieniono {dane.get('zmieniono', '')}: {dane.get('opis', '')}".strip(": ")}

    def aktualizuj_baze(self):
        """
        Pełna aktualizacja bazy globalnej z serwera (jak lista pracowników w HR): pobrana baza zastępuje poprzednią,
        wpisy własne zostają. Przed zmianą kopia w kopie_bazy.
        """
        try:
            odp = wyslij_json(URL_BAZY, {"akcja": "baza", **({"token": konto.token()} if konto.token() else {})}, timeout=20.0)  # konto - do dziennika panelu
        except Exception as e:
            return {"ok": False, "blad": f"Nie udało się pobrać bazy: {e}"}
        wersja = str(odp.get("wersja", ""))
        nowe = {r: odp.get(r) for r in PLIKI}
        if not odp.get("ok") or not wersja or not all(isinstance(v, dict) for v in nowe.values()) or not nowe["starters"]:
            return {"ok": False, "blad": "Pobrana baza jest niepełna - zostaje dotychczasowa."}
        poprzednia = self._baza.wersja
        kopia = self._baza.kopia()
        zmiany = self._baza.zastap_globalna(nowe, wersja)
        return {"ok": True, "zmiany": zmiany, "kopia": kopia, "baza": self.baza(), "bylo": poprzednia, "jest": wersja}

    def zapisz_urzadzenie(self, rodzaj, stara_nazwa, nazwa, dane):
        if not nazwa.strip():
            return {"ok": False, "blad": "Podaj nazwę modelu."}
        if nazwa.strip() != stara_nazwa and nazwa.strip() in self._baza.urzadzenia(rodzaj):
            return {"ok": False, "blad": "Urządzenie o tej nazwie już jest w bazie."}
        wynik = {}
        for klucz, opis, _, liczbowe in POLA_URZADZEN[rodzaj]:
            v = dane.get(klucz, "")
            if liczbowe:
                if str(v).strip() == "":
                    wynik[klucz] = 0
                    continue
                try:
                    wynik[klucz] = obliczenia.liczba(v)
                except ValueError:
                    return {"ok": False, "blad": f"{opis}: wpisz liczbę."}
            else:
                wynik[klucz] = str(v).strip()
        self._baza.zapisz_urzadzenie(rodzaj, stara_nazwa, nazwa, wynik)
        return {"ok": True, "baza": self.baza()}

    def usun_urzadzenie(self, rodzaj, nazwa):
        self._baza.usun_urzadzenie(rodzaj, nazwa)
        return {"ok": True, "baza": self.baza()}

    def plik_bazy(self, id_):
        """Plik producenta z bazy (krzywa, karta katalogowa): kopia lokalna albo pobranie z serwera (wymaga zalogowania)."""
        if not re.fullmatch(r"[0-9a-f]{16}\.(pdf|png|jpg|jpeg)", str(id_)):
            return {"ok": False, "blad": "Nieprawidłowy plik."}
        sciezka = os.path.join(KATALOG_PLIKOW, id_)
        if os.path.isfile(sciezka):
            return {"ok": True, "sciezka": sciezka}
        token = konto.token()
        if not token:
            return {"ok": False, "zaloguj": True, "blad": "Pliki producentów z bazy są dostępne po zalogowaniu (Ustawienia - Konto Diamel)."}
        try:
            odp = wyslij_json(URL_BAZY, {"akcja": "plik", "id": id_, "token": token}, timeout=60.0)
        except Exception as e:
            return {"ok": False, "blad": f"Brak połączenia z serwerem: {e}"}
        if not odp.get("ok"):
            return {"ok": False, "zaloguj": bool(odp.get("zaloguj")), "blad": odp.get("blad", "Nie udało się pobrać pliku.")}
        os.makedirs(KATALOG_PLIKOW, exist_ok=True)
        with open(sciezka + ".tmp", "wb") as f:
            f.write(base64.b64decode(odp["plik"]))
        os.replace(sciezka + ".tmp", sciezka)
        return {"ok": True, "sciezka": sciezka}

    def otworz_plik_bazy(self, id_):
        wynik = self.plik_bazy(id_)
        if wynik["ok"]:
            os.startfile(wynik["sciezka"])
        return wynik

    def folder_bazy(self):
        os.startfile(os.path.join(KATALOG_DANYCH, "data"))
        return {"ok": True}

    # ------------------------------------------------------------------ projekt

    def nowy_projekt(self):
        autor = self._konto.stan()["inicjaly"] or self.program["autor"]  # inicjały z konta (imię i nazwisko w panelu)
        return {"project_no": "", "client": "", "genset": "", "engine": "", "author": autor,
                "language": self.program["jezyk"], **DOMYSLNE_POLA,
                "revisions": [{"rev": "0", "desc": "Wydanie początkowe / Initial Issue", "drawn": autor,
                               "check": "Appr.", "date": datetime.now().strftime("%d%b%y").upper()}],
                "images": {k: "" for k in OBRAZY}, "_plik": ""}

    @staticmethod
    def _z_pliku(stan):
        """Projekt z pliku .json - także z wersji 1.x (napięcie rozrusznika = napięcie układu, kręcenie 16 V)."""
        wynik = {**DOMYSLNE_POLA}
        if "system_v" not in stan:
            wynik["system_v"] = _tekst(stan.get("starter_v")) or "24"
            wynik["crank_v"] = "16"
        for k in ("project_no", "client", "genset", "engine", "author", "language", *DOMYSLNE_POLA):
            if k in stan:
                wynik[k] = _tekst(stan[k])
        wynik["language"] = wynik.get("language") if wynik.get("language") in ("English", "Polski") else "English"
        wynik["revisions"] = [{k: _tekst(r.get(k, "")) for k in ("rev", "desc", "drawn", "check", "date")} for r in stan.get("revisions", [])]
        wynik["images"] = {k: (stan.get("images") or {}).get(k, "") for k in OBRAZY}
        return wynik

    def wczytaj_projekt(self, sciezka=""):
        if not sciezka:
            wybor = self._okno.create_file_dialog(webview.FileDialog.OPEN, file_types=("Projekt kalkulatora (*.json)", "Wszystkie pliki (*.*)"))
            if not wybor:
                return {"ok": False, "anulowano": True}
            sciezka = wybor[0]
        try:
            stan = self._z_pliku(_czytaj_json(sciezka, None) or {})
        except Exception as e:
            return {"ok": False, "blad": f"Nie udało się wczytać projektu: {e}"}
        stan["_plik"] = sciezka
        self._dodaj_ostatni(sciezka)
        brakujace = [os.path.basename(p) for p in stan["images"].values() if p and not os.path.isfile(p)]
        return {"ok": True, "projekt": stan, "brakujace": brakujace}

    def zapisz_projekt(self, stan, jako=False):
        sciezka = stan.get("_plik") or ""
        if jako or not sciezka:
            nazwa = f"{stan.get('project_no') or 'Projekt'}_rozruch.json"
            wybor = self._okno.create_file_dialog(webview.FileDialog.SAVE, directory=os.path.dirname(sciezka) if sciezka else "",
                                                  save_filename=nazwa, file_types=("Projekt kalkulatora (*.json)",))
            if not wybor:
                return {"ok": False, "anulowano": True}
            sciezka = wybor if isinstance(wybor, str) else wybor[0]
            if not sciezka.lower().endswith(".json"):
                sciezka += ".json"
        dane = {k: v for k, v in stan.items() if not k.startswith("_")}
        dane["starter_v"] = dane.get("system_v", "")  # zgodność: wersje 1.x czytają napięcie rozrusznika z tego pola
        try:
            _zapisz_json(sciezka, dane)
        except PermissionError:
            return {"ok": False, "blad": "Brak dostępu do pliku - wybierz inny folder."}
        self._dodaj_ostatni(sciezka)
        return {"ok": True, "plik": sciezka}

    def ustaw_niezapisane(self, wartosc):
        self._niezapisane = bool(wartosc)
        return True

    def zamknij(self):
        """Zamknięcie okna po decyzji użytkownika (zapisz / nie zapisuj)."""
        self._zamykam = True
        threading.Thread(target=self._okno.destroy, daemon=True).start()
        return True

    # ------------------------------------------------------------------ obliczenia i raport

    def oblicz(self, stan):
        return obliczenia.oblicz({**stan, "cca_tolerancja": self.program["cca_tolerancja"]})

    def wybierz_obraz(self):
        wybor = self._okno.create_file_dialog(webview.FileDialog.OPEN, file_types=("Obrazy (*.png;*.jpg;*.jpeg;*.bmp)",))
        return wybor[0] if wybor else ""

    def obraz(self, sciezka):
        """Podgląd załącznika w oknie (data URI). Ścieżki z bazy mogą być względne."""
        pelna = self._baza.sciezka_obrazu(sciezka)
        if not pelna:
            return {"ok": False, "blad": "Nie znaleziono pliku"}
        if os.path.getsize(pelna) > OBRAZ_MAX_MB * 1024 * 1024:
            return {"ok": True, "sciezka": pelna, "podglad": ""}
        typ = mimetypes.guess_type(pelna)[0] or "image/png"
        return {"ok": True, "sciezka": pelna, "podglad": f"data:{typ};base64,{base64.b64encode(open(pelna, 'rb').read()).decode('ascii')}"}

    def wybierz_szablon(self):
        wybor = self._okno.create_file_dialog(webview.FileDialog.OPEN, file_types=("Dokument Word (*.docx)",))
        if wybor:
            self.ustaw_program("szablon", wybor[0])
        return self.program

    def generuj_raport(self, stan, format_="pdf"):
        """Raport PDF (przez Microsoft Word) albo DOCX; nagłówek i stopka z szablonu z ustawień."""
        wyniki = obliczenia.oblicz({**stan, "cca_tolerancja": self.program["cca_tolerancja"]})
        if not wyniki["ok"]:
            return {"ok": False, "blad": "Uzupełnij dane: " + "; ".join(wyniki["bledy"].values())}
        rozszerzenie = ".pdf" if format_ == "pdf" else ".docx"
        plik_projektu = stan.get("_plik") or ""
        folder = os.path.dirname(plik_projektu) if plik_projektu else self.program["folder_raportow"]
        wybor = self._okno.create_file_dialog(webview.FileDialog.SAVE, directory=folder or "",
                                              save_filename=f"Starting_System_{stan.get('project_no') or 'Projekt'}{rozszerzenie}",
                                              file_types=("Dokument PDF (*.pdf)",) if format_ == "pdf" else ("Dokument Word (*.docx)",))
        if not wybor:
            return {"ok": False, "anulowano": True}
        sciezka = wybor if isinstance(wybor, str) else wybor[0]
        if not sciezka.lower().endswith(rozszerzenie):
            sciezka += rozszerzenie
        obrazy = raport_docx.istniejace({k: self._baza.sciezka_obrazu(v) for k, v in (stan.get("images") or {}).items()})
        szablon = self._szablon()
        if szablon and not os.path.isfile(szablon):
            return {"ok": False, "blad": f"Nie znaleziono szablonu raportu: {szablon} - wybierz go ponownie w Ustawieniach albo usuń."}
        try:
            if format_ == "pdf":
                tymczasowy = os.path.join(tempfile.gettempdir(), f"raport_rozruch_{os.getpid()}.docx")
                raport_docx.generuj(tymczasowy, stan, wyniki, obrazy, szablon)
                try:
                    raport_docx.zapisz_pdf(tymczasowy, sciezka)
                finally:
                    os.remove(tymczasowy)
            else:
                raport_docx.generuj(sciezka, stan, wyniki, obrazy, szablon)
        except PermissionError:
            return {"ok": False, "blad": "Plik raportu jest otwarty w innym programie - zamknij go i spróbuj ponownie."}
        except RuntimeError as e:
            return {"ok": False, "blad": str(e)}
        except Exception as e:
            return {"ok": False, "blad": f"Nie udało się utworzyć raportu: {e}"}
        if not plik_projektu:
            self.ustaw_program("folder_raportow", os.path.dirname(sciezka))
        if self.program["otworz_raport"]:
            os.startfile(sciezka)
        return {"ok": True, "plik": sciezka, "pominiete": [k for k, v in (stan.get("images") or {}).items() if v and k not in obrazy]}

    # ------------------------------------------------------------------ pliki, strony, zgłoszenia

    def otworz_plik(self, sciezka):
        if os.path.isfile(sciezka):
            os.startfile(sciezka)
        return {"ok": True}

    def otworz_folder(self, sciezka):
        if os.path.isfile(sciezka):
            subprocess.Popen(["explorer", "/select,", os.path.normpath(sciezka)])
        elif os.path.isdir(sciezka):
            os.startfile(sciezka)
        return {"ok": True}

    def otworz_strone(self, adres):
        import webbrowser
        webbrowser.open(adres)
        return {"ok": True}

    def wybierz_zalaczniki(self):
        wybor = self._okno.create_file_dialog(webview.FileDialog.OPEN, allow_multiple=True, file_types=ZALACZNIKI_TYPY)
        return [{"sciezka": p, "nazwa": os.path.basename(p), "kb": max(1, round(os.path.getsize(p) / 1024))} for p in (wybor or []) if os.path.isfile(p)]

    def zglos(self, email, kategoria, nazwa, opis, projekt=None, zalaczniki=()):
        """
        Prośba o dodanie sprzętu do bazy albo zgłoszenie błędu - formularz na diamel.pl (program nie zawiera haseł).
        projekt: bieżący projekt dołączany jako plik .json (przy zgłoszeniu błędu).
        """
        zgloszenie = {"program": NAZWA_PROGRAMU, "wersja": VERSION, "email": email, "kategoria": kategoria, "nazwa": nazwa, "opis": opis}
        if projekt:
            tresc = json.dumps({k: v for k, v in projekt.items() if not k.startswith("_")}, ensure_ascii=False, indent=4).encode("utf-8")
            zgloszenie["zalaczniki"] = [{"nazwa": f"{projekt.get('project_no') or 'projekt'}_rozruch.json", "dane": base64.b64encode(tresc).decode("ascii")}]
        pliki = [p for p in dict.fromkeys(zalaczniki or []) if p and os.path.isfile(p)]
        if sum(os.path.getsize(p) for p in pliki) > ZALACZNIKI_MAX_MB * 1048576:
            return {"ok": False, "blad": f"Załączniki są większe niż {ZALACZNIKI_MAX_MB} MB razem - wybierz mniejsze pliki."}
        zgloszenie.setdefault("zalaczniki", []).extend(
            {"nazwa": os.path.basename(p), "dane": base64.b64encode(open(p, "rb").read()).decode("ascii")} for p in pliki)
        req = urllib.request.Request(URL_ZGLOSZEN, data=json.dumps(zgloszenie).encode("utf-8"), headers={**NAGLOWKI, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as odp:
                wynik = json.loads(odp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                wynik = json.loads(e.read().decode("utf-8"))
            except Exception:
                return {"ok": False, "blad": str(e)}
        except Exception as e:
            return {"ok": False, "blad": f"Brak połączenia z serwerem: {e}"}
        return {"ok": bool(wynik.get("ok")), "blad": wynik.get("blad", "")}
