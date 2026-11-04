"""
baza.py

Baza rozruszników i akumulatorów - jak lista pracowników w Korektorze HR:
- baza globalna Diamel (repozytorium GitHub) pobierana w całości i zastępowana przy każdej aktualizacji
  (wpisy usunięte z bazy globalnej znikają także u użytkownika),
- wpisy własne użytkownika (nowe albo zmienione urządzenia z bazy globalnej) trzymane osobno - aktualizacja ich nie rusza.
Pliki: %APPDATA%\\Diamel\\Kalkulator Rozruchu\\data: starters.json, batteries.json (kopia bazy globalnej), wlasne.json.
"""
import json
import os
import shutil
import sys
from datetime import datetime

from konfiguracja_app import DB_VERSION, URL_BAZY, sciezka_do_zasobu

KATALOG_DANYCH = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Diamel", "Kalkulator Rozruchu")
KATALOG_BAZY = os.path.join(KATALOG_DANYCH, "data")
KATALOG_KOPII = os.path.join(KATALOG_DANYCH, "kopie_bazy")
PLIK_WLASNYCH = os.path.join(KATALOG_BAZY, "wlasne.json")
PLIKI = {"starters": "starters.json", "batteries": "batteries.json"}
KOPIE_MAX = 10

# Pola urządzeń: (klucz, opis, jednostka, liczba). Edytor zachowuje też pola spoza tej listy.
POLA_URZADZEN = {
    "starters": [
        ("voltage_v", "Napięcie znamionowe", "V", True),
        ("power_kw", "Moc", "kW", True),
        ("normal_current_a", "Prąd znamionowy", "A", True),
        ("peak_current_a", "Prąd szczytowy", "A", True),
        ("crank_voltage_v", "Napięcie kręcenia", "V", True),
        ("min_voltage_v", "Napięcie minimalne", "V", True),
        ("test_res_ohm", "Rezystancja obwodu testowego", "Ω", True),
        ("curve_path", "Krzywa rozrusznika (obraz)", "", False),
    ],
    "batteries": [
        ("type", "Technologia", "", False),
        ("voltage_v", "Napięcie", "V", True),
        ("capacity_ah", "Pojemność", "Ah", True),
        ("cca_a", "Prąd rozruchowy CCA", "A", True),
        ("mca_a", "Prąd MCA", "A", True),
        ("internal_res_ohm", "Rezystancja wewnętrzna", "Ω", True),
        ("ocv_v", "Napięcie spoczynkowe", "V", True),
        ("reserve_capacity_min", "Rezerwa pojemności", "min", True),
        ("part_number", "Numer katalogowy", "", False),
        ("weight_kg", "Masa", "kg", True),
        ("dimensions_mm", "Wymiary", "mm", False),
        ("batt_path", "Karta katalogowa (obraz)", "", False),
    ],
}


def _czytaj(sciezka, domyslnie=None):
    try:
        with open(sciezka, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return domyslnie


def _zapisz(sciezka, dane):
    os.makedirs(os.path.dirname(sciezka), exist_ok=True)
    tymczasowy = sciezka + ".tmp"
    with open(tymczasowy, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4, ensure_ascii=False)
    os.replace(tymczasowy, sciezka)


def _wbudowana(rodzaj):
    return (_czytaj(sciezka_do_zasobu(os.path.join("data", PLIKI[rodzaj])), {}) or {}).get(rodzaj, {})


def _stare_miejsca():
    """Bazy z wcześniejszych wersji: folder data obok programu (1.x) i wcześniejszy zapis w AppData (wspólna baza bez podziału)."""
    miejsca = [os.path.join(os.path.dirname(sys.executable), "data"), os.path.join(os.path.abspath("."), "data")]
    return [KATALOG_BAZY] + [m for m in dict.fromkeys(miejsca) if os.path.normcase(m) != os.path.normcase(KATALOG_BAZY)]


def url_bazy(plik):
    return URL_BAZY + plik


class Baza:
    def __init__(self):
        self.globalna = {"starters": {}, "batteries": {}}
        self.wlasne = {"starters": {}, "batteries": {}}
        self.wersja = DB_VERSION
        self.przeniesiono_z = ""
        self._przygotuj()
        self.wczytaj()

    def _plik(self, rodzaj):
        return os.path.join(KATALOG_BAZY, PLIKI[rodzaj])

    def _przygotuj(self):
        """
        Pierwsze uruchomienie tej wersji: wpisy własne wydzielone ze starej (wspólnej) bazy - urządzenia, których nie ma
        w bazie wbudowanej albo mają inne parametry. Kopia bazy globalnej = baza wbudowana (aktualizacja pobierze nowszą).
        """
        if os.path.exists(PLIK_WLASNYCH):
            return
        os.makedirs(KATALOG_BAZY, exist_ok=True)
        wlasne = {r: {} for r in PLIKI}
        for stare in _stare_miejsca():
            dane = {r: (_czytaj(os.path.join(stare, p), {}) or {}).get(r) for r, p in PLIKI.items()}
            if all(isinstance(v, dict) for v in dane.values()):
                for rodzaj, wpisy in dane.items():
                    wbud = _wbudowana(rodzaj)
                    wlasne[rodzaj] = {n: v for n, v in wpisy.items() if wbud.get(n) != v}
                if any(wlasne.values()) and stare != KATALOG_BAZY:
                    self.przeniesiono_z = stare
                break
        for rodzaj, p in PLIKI.items():
            wbudowany = sciezka_do_zasobu(os.path.join("data", p))
            if os.path.exists(wbudowany):
                shutil.copy(wbudowany, self._plik(rodzaj))
        _zapisz(PLIK_WLASNYCH, wlasne)

    def wczytaj(self):
        for rodzaj in PLIKI:
            dane = _czytaj(self._plik(rodzaj)) or _czytaj(sciezka_do_zasobu(os.path.join("data", PLIKI[rodzaj])), {})
            self.globalna[rodzaj] = dane.get(rodzaj, {})
            if rodzaj == "starters":
                self.wersja = dane.get("version", self.wersja)
        wlasne = _czytaj(PLIK_WLASNYCH, {}) or {}
        self.wlasne = {r: wlasne.get(r, {}) for r in PLIKI}

    # -------------------------------------------------------------- odczyt

    def urzadzenia(self, rodzaj):
        """Baza globalna + wpisy własne (własny wpis o tej samej nazwie zastępuje globalny)."""
        return {**self.globalna[rodzaj], **self.wlasne[rodzaj]}

    def zrodla(self, rodzaj):
        """nazwa -> 'globalna' / 'wlasna' (nie ma w bazie globalnej) / 'zmieniona' (własna wersja urządzenia z bazy globalnej)."""
        wynik = {n: "globalna" for n in self.globalna[rodzaj]}
        for n in self.wlasne[rodzaj]:
            wynik[n] = "zmieniona" if n in self.globalna[rodzaj] else "wlasna"
        return wynik

    # -------------------------------------------------------------- wpisy własne

    def _zapisz_wlasne(self):
        _zapisz(PLIK_WLASNYCH, self.wlasne)

    def zapisz_urzadzenie(self, rodzaj, stara_nazwa, nazwa, dane):
        """Zapis z edytora - zawsze jako wpis własny. Pola nieznane edytorowi (np. dodane w nowszej bazie) zostają."""
        nazwa = nazwa.strip()
        poprzednie = self.urzadzenia(rodzaj).get(stara_nazwa, {}) if stara_nazwa else {}
        if stara_nazwa and stara_nazwa != nazwa:
            self.wlasne[rodzaj].pop(stara_nazwa, None)  # zmiana nazwy - urządzenie z bazy globalnej pod starą nazwą zostaje
        nowe = {**poprzednie, **dane}
        if self.globalna[rodzaj].get(nazwa) == nowe:
            self.wlasne[rodzaj].pop(nazwa, None)  # bez różnic względem bazy globalnej - nie trzeba własnej wersji
        else:
            self.wlasne[rodzaj][nazwa] = nowe
        self._zapisz_wlasne()

    def usun_urzadzenie(self, rodzaj, nazwa):
        """Usuwa wpis własny. Urządzenie z bazy globalnej wraca do wartości z bazy (tego nie da się usunąć - jak pracowników w HR)."""
        self.wlasne[rodzaj].pop(nazwa, None)
        self._zapisz_wlasne()

    # -------------------------------------------------------------- aktualizacja z serwera

    def kopia(self):
        """Kopia bazy przed aktualizacją (ostatnie KOPIE_MAX). Zwraca folder kopii."""
        cel = os.path.join(KATALOG_KOPII, datetime.now().strftime("%Y-%m-%d_%H%M%S"))
        os.makedirs(cel, exist_ok=True)
        for p in list(PLIKI.values()) + [os.path.basename(PLIK_WLASNYCH)]:
            if os.path.exists(os.path.join(KATALOG_BAZY, p)):
                shutil.copy(os.path.join(KATALOG_BAZY, p), cel)
        for stara in sorted(os.listdir(KATALOG_KOPII))[:-KOPIE_MAX]:
            shutil.rmtree(os.path.join(KATALOG_KOPII, stara), ignore_errors=True)
        return cel

    def zastap_globalna(self, nowe, nowa_wersja):
        """Pełna aktualizacja: baza globalna zastąpiona pobraną. Zwraca zmiany {rodzaj: {nowe, zmienione, usuniete}}."""
        zmiany = {}
        for rodzaj, wpisy in nowe.items():
            stare = self.globalna[rodzaj]
            zmiany[rodzaj] = {"nowe": sorted(set(wpisy) - set(stare)), "usuniete": sorted(set(stare) - set(wpisy)),
                              "zmienione": sorted(n for n in set(wpisy) & set(stare) if wpisy[n] != stare[n])}
            self.globalna[rodzaj] = wpisy
            _zapisz(self._plik(rodzaj), {"version": nowa_wersja, rodzaj: wpisy})
        self.wersja = nowa_wersja
        # własna wersja identyczna z nową globalną (np. urządzenie zgłoszone i dodane do bazy) - już niepotrzebna
        for rodzaj in PLIKI:
            for n in [n for n, v in self.wlasne[rodzaj].items() if self.globalna[rodzaj].get(n) == v]:
                del self.wlasne[rodzaj][n]
        self._zapisz_wlasne()
        return zmiany

    def sciezka_obrazu(self, sciezka):
        """Ścieżki z bazy bywają względne (np. Zasoby/krzywa.jpg) - szukane w zasobach programu i folderze danych."""
        if not sciezka:
            return ""
        if os.path.isabs(sciezka):
            return sciezka if os.path.isfile(sciezka) else ""
        for kandydat in (sciezka_do_zasobu(sciezka), os.path.join(KATALOG_DANYCH, sciezka)):
            if os.path.isfile(kandydat):
                return os.path.abspath(kandydat)
        return ""
