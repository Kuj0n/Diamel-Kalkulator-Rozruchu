"""
konto.py

Konto Diamel w Kalkulatorze (nieobowiązkowe): po zalogowaniu raporty dostają szablon firmy użytkownika (papier firmowy
- nagłówek i stopka) i inicjały z imienia i nazwiska. Konto i dostęp do programu nadaje administrator w panelu diamel.pl.
Token zaszyfrowany Windows DPAPI (tylko ten użytkownik Windows go odczyta), szablon w kopii lokalnej - raporty działają
też bez internetu. Wylogowanie usuwa token i kopię szablonu.
"""
import base64
import ctypes
import ctypes.wintypes
import json
import os
import platform
import urllib.error
import urllib.request

from baza import KATALOG_DANYCH
from konfiguracja_app import VERSION, NAZWA_PROGRAMU, URL_KONTA

PROGRAM = "rozruch"  # klucz programu w panelu (DIAMEL_PROGRAMY w lib/hr.php)
PLIK_TOKENU = os.path.join(KATALOG_DANYCH, "sesja.dat")
PLIK_KONTA = os.path.join(KATALOG_DANYCH, "konto.json")      # ostatnie dane konta (praca bez internetu)
PLIK_SZABLONU = os.path.join(KATALOG_DANYCH, "szablon_firmy.docx")
NAGLOWKI = {"User-Agent": f"Diamel-{NAZWA_PROGRAMU}/{VERSION}", "Content-Type": "application/json"}


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _dpapi(dane, szyfruj):
    bufor = ctypes.create_string_buffer(dane, len(dane))
    wej = _DATA_BLOB(len(dane), ctypes.cast(bufor, ctypes.POINTER(ctypes.c_char)))
    wyj = _DATA_BLOB()
    funkcja = ctypes.windll.crypt32.CryptProtectData if szyfruj else ctypes.windll.crypt32.CryptUnprotectData
    if not funkcja(ctypes.byref(wej), None, None, None, None, 0, ctypes.byref(wyj)):
        raise OSError("Błąd szyfrowania DPAPI")
    try:
        return ctypes.string_at(wyj.pbData, wyj.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(wyj.pbData)


def _usun(sciezka):
    try:
        os.remove(sciezka)
    except OSError:
        pass


def token():
    """Token zalogowanego konta (pliki producentów z bazy) albo None."""
    return _czytaj_token()


def _czytaj_token():
    try:
        with open(PLIK_TOKENU, "rb") as f:
            return _dpapi(f.read(), szyfruj=False).decode("ascii")
    except Exception:
        return None


def _zapytanie(dane, timeout=12.0):
    """Zapytanie do diamel.pl/api/konto.php. Odpowiedź serwera (także z kodem błędu) jako słownik; brak sieci -> wyjątek."""
    req = urllib.request.Request(URL_KONTA, data=json.dumps({**dane, "program": PROGRAM}).encode("utf-8"), headers=NAGLOWKI)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as odp:
            return json.loads(odp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            raise e


class Konto:
    def __init__(self):
        self.dane = None  # konto z serwera: login, nazwa, inicjaly, firma, szablon
        try:
            with open(PLIK_KONTA, encoding="utf-8") as f:
                self.dane = json.load(f) if _czytaj_token() else None
        except Exception:
            self.dane = None

    @property
    def szablon(self):
        """Ścieżka kopii szablonu firmy albo '' (brak konta / firma bez szablonu)."""
        return PLIK_SZABLONU if self.dane and self.dane.get("szablon") and os.path.isfile(PLIK_SZABLONU) else ""

    def stan(self):
        d = self.dane or {}
        return {"zalogowany": bool(self.dane), "login": d.get("login", ""), "nazwa": d.get("nazwa", ""), "inicjaly": d.get("inicjaly", ""),
                "firma": (d.get("firma") or {}).get("nazwa", ""), "szablon": (d.get("szablon") or {}).get("nazwa", "") if self.szablon else ""}

    def _zapisz(self, konto):
        """Dane konta + szablon firmy (pobierany tylko gdy zmieniła się jego wersja)."""
        stare = (self.dane or {}).get("szablon") or {}
        nowe = konto.get("szablon") or {}
        if not nowe:
            _usun(PLIK_SZABLONU)
        elif nowe.get("wersja") != stare.get("wersja") or not os.path.isfile(PLIK_SZABLONU):
            token = _czytaj_token()
            odp = _zapytanie({"akcja": "szablon", "token": token}, timeout=30.0)
            if odp.get("ok"):
                os.makedirs(KATALOG_DANYCH, exist_ok=True)
                with open(PLIK_SZABLONU + ".tmp", "wb") as f:
                    f.write(base64.b64decode(odp["plik"]))
                os.replace(PLIK_SZABLONU + ".tmp", PLIK_SZABLONU)
        self.dane = konto
        os.makedirs(KATALOG_DANYCH, exist_ok=True)
        with open(PLIK_KONTA, "w", encoding="utf-8") as f:
            json.dump(konto, f, ensure_ascii=False, indent=2)

    def zaloguj(self, login, haslo, zapamietaj=True):
        try:
            odp = _zapytanie({"akcja": "zaloguj", "login": login.strip(), "haslo": haslo, "zapamietaj": bool(zapamietaj), "komputer": platform.node()})
        except Exception as e:
            return {"ok": False, "blad": f"Brak połączenia z serwerem diamel.pl: {e}"}
        if not odp.get("ok"):
            return {"ok": False, "blad": odp.get("blad") or "Logowanie nie powiodło się."}
        os.makedirs(KATALOG_DANYCH, exist_ok=True)
        with open(PLIK_TOKENU, "wb") as f:
            f.write(_dpapi(odp["token"].encode("ascii"), szyfruj=True))
        try:
            self._zapisz(odp["konto"])
        except Exception as e:
            self.dane = odp["konto"]
            return {"ok": True, "stan": self.stan(), "uwaga": f"Nie udało się pobrać szablonu raportu: {e}"}
        return {"ok": True, "stan": self.stan()}

    def odswiez(self):
        """Przy starcie: aktualne dane konta i szablon (nowa wersja z panelu). Bez internetu - ostatnie zapisane."""
        token = _czytaj_token()
        if not token:
            self.dane = None
            return {"ok": True, "stan": self.stan()}
        try:
            odp = _zapytanie({"akcja": "dane", "token": token})
        except Exception:
            return {"ok": True, "stan": self.stan(), "offline": True}
        if odp.get("zaloguj"):  # sesja wygasła, konto zablokowane albo odebrany dostęp do programu
            self.wyloguj(lokalnie=True)
            return {"ok": True, "stan": self.stan(), "wylogowano": odp.get("blad", "")}
        if odp.get("ok"):
            try:
                self._zapisz(odp["konto"])
            except Exception:
                pass
        return {"ok": True, "stan": self.stan()}

    def wyloguj(self, lokalnie=False):
        token = _czytaj_token()
        if token and not lokalnie:
            try:
                _zapytanie({"akcja": "wyloguj", "token": token}, timeout=5.0)
            except Exception:
                pass
        for p in (PLIK_TOKENU, PLIK_KONTA, PLIK_SZABLONU):
            _usun(p)
        self.dane = None
        return {"ok": True, "stan": self.stan()}
