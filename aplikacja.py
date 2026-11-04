"""
aplikacja.py

Uruchomienie Kalkulatora Rozruchu: okno (Edge WebView2) z interfejsem z folderu ui/ i funkcjami z interfejs.py.
ROZRUCH_DEBUG=1 - narzędzia programisty (F12) w oknie.
"""
import ctypes
import json
import os
import socket
import sys
import threading
import urllib.request

import webview

from interfejs import Api, INSTALATOR
from baza import KATALOG_DANYCH
from konfiguracja_app import VERSION, sciezka_do_zasobu

PLIK_OKNA = os.path.join(KATALOG_DANYCH, "okno.json")
# Własny port lokalnego serwera okna (pywebview domyślnie używa 42001 we wszystkich programach - Korektor HR uruchomiony
# przy otwartym Kalkulatorze dostawał jego interfejs). Porty programów Diamel: HR 42011, Kalkulator 42021, Akustyka 42031.
PORT_OKNA = 42021
CZEKAJ_NA_OKNO = 25  # sekund - potem awaryjne sprawdzenie aktualizacji bez interfejsu


def bez_pamieci_podrecznej():
    """
    Pliki interfejsu zawsze świeże: pywebview ustawia "no-store", ale bottle.static_file zastępuje nagłówki odpowiedzi
    (zostają tylko Last-Modified / ETag) - okno WebView2 brało wtedy pliki z pamięci podręcznej (np. stary app.js
    po aktualizacji, a przy wspólnym porcie - interfejs innego programu). Do tego adres z numerem wersji (?v=).
    """
    import bottle
    oryginal = bottle.static_file

    def static_file(*a, **k):
        odp = oryginal(*a, **k)
        odp.set_header("Cache-Control", "no-cache, no-store, must-revalidate")
        odp.set_header("Pragma", "no-cache")
        odp.set_header("Expires", "0")
        return odp
    bottle.static_file = static_file


def wolny_port(preferowany):
    """Port serwera okna: własny programu, a gdy zajęty (drugie okno, inny program) - dowolny wolny, nigdy cudzy serwer."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferowany))
            return preferowany
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def awaryjna_aktualizacja(api):
    """
    Gdy okno programu nie wystartuje (np. błąd w wydanej wersji), aktualizację i tak da się zainstalować:
    zwykłe okienko Windows z propozycją nowszej albo zalecanej (wycofanie wadliwej) wersji.
    """
    if api.ui_gotowe.wait(CZEKAJ_NA_OKNO):
        return
    akt = api.sprawdz_aktualizacje()
    if not (akt.get("ok") and akt.get("do_instalacji")):
        return
    tekst = (f"Okno programu nie uruchomiło się poprawnie.\n\nZalecana jest wersja {akt['wersja']} "
             + ("(powrót do starszej - w tej wersji wykryto błąd)." if akt["wycofana"] else "(nowsza).")
             + "\n\nPobrać i zainstalować ją teraz?")
    if ctypes.windll.user32.MessageBoxW(0, tekst, "Kalkulator Rozruchu - aktualizacja", 0x04 | 0x30 | 0x40000) != 6:  # Tak/Nie, ostrzeżenie, na wierzchu
        return
    try:
        urllib.request.urlretrieve(akt["link"], INSTALATOR)
        api.uruchom_instalator()
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(0, f"Nie udało się pobrać aktualizacji:\n{e}\n\nInstalator jest też na diamel.pl",
                                         "Kalkulator Rozruchu", 0x10 | 0x40000)


def main():
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("diamel.kalkulator_rozruchu.main")
    except Exception:
        pass
    api = Api()
    try:
        okno_poz = json.load(open(PLIK_OKNA, encoding="utf-8"))
    except Exception:
        okno_poz = {}
    okno = webview.create_window(
        f"Kalkulator Rozruchu v{VERSION}", sciezka_do_zasobu(os.path.join("ui", "index.html")) + f"?v={VERSION}", js_api=api,
        width=okno_poz.get("w", 1400), height=okno_poz.get("h", 900), min_size=(1100, 700),
        background_color="#0a1530", text_select=True,
    )
    api._okno = okno  # z podkreśleniem: pywebview nie udostępnia (i nie przegląda) tego pola dla JS

    def zamykanie():
        if api._niezapisane and not api._zamykam:
            okno.evaluate_js("window.pytajPrzedZamknieciem && window.pytajPrzedZamknieciem()")
            return False  # okno pyta o zapis i zamyka się przez api.zamknij()
        api.zakoncz_sesje()
        try:
            os.makedirs(KATALOG_DANYCH, exist_ok=True)
            json.dump({"w": okno.width, "h": okno.height}, open(PLIK_OKNA, "w", encoding="utf-8"))
        except Exception:
            pass
        return True

    threading.Thread(target=awaryjna_aktualizacja, args=(api,), daemon=True).start()
    okno.events.closing += zamykanie
    bez_pamieci_podrecznej()
    webview.start(debug=os.environ.get("ROZRUCH_DEBUG") == "1", private_mode=False, http_port=wolny_port(PORT_OKNA),
                  storage_path=os.path.join(KATALOG_DANYCH, "webview"))


if __name__ == "__main__":
    sys.exit(main())
