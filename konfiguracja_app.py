import os
import sys

# ==========================================
# KONFIGURACJA I METADANE
# ==========================================
VERSION = "1.1.0"
DB_VERSION = "1.1.0"
BUILD_DATE = "2026-11-02 21:00"

CHANGELOG = """
v1.1.0 (2026-11-02)
- Aktualizacje programu i bazy danych pobierane z GitHub (github.com/Kuj0n/Diamel-Kalkulator-Rozruchu).
- Zgłoszenia sprzętu wysyłane przez formularz na diamel.pl - program nie zawiera już hasła do poczty.
- Program pamięta wersję lokalnej bazy danych.

v1.0.1 (2026-10-23)
- Aktualizacja danych.

v1.0.0 (2026-10-01)
- Pierwsze wydanie kalkulatora rozruchu agregatów.
- Wdrożenie architektury MVC.
- Obliczanie spadków napięć i zapotrzebowania prądowego.
- Dobór prądu ładowarki.
- Generowanie zaawansowanych raportów DOCX.
"""

CHANGELOG_DB = """
v1.1.0 (2026-11-02)
- Baza publikowana razem z wydaniem na GitHub.

v1.0.1 (2026-10-23)
- Aktualizacja danych.

v1.0.0 (2026-10-01)
- Początkowa baza rozruszników (Delco Remy, Bosch).
- Początkowa baza akumulatorów (Optima, Varta).
"""

# Aktualizacje (GitHub Releases) i zgłoszenia (formularz na diamel.pl)
NAZWA_PROGRAMU = "kalkulator_rozruchu"
GITHUB_REPO = "Kuj0n/Diamel-Kalkulator-Rozruchu"
URL_ZGLOSZEN = "https://diamel.pl/api/zgloszenie.php"

def sciezka_do_zasobu(relatywna_sciezka):
    """ Pancerna funkcja szukająca plików zasobów w trybie .exe i developerskim """
    katalogi = [
        os.path.abspath("."),
        os.path.join(os.path.abspath("."), "_internal")
    ]
    if hasattr(sys, '_MEIPASS'):
        katalogi.insert(0, sys._MEIPASS)
        katalogi.insert(1, os.path.join(sys._MEIPASS, "_internal"))
        
    if hasattr(sys, 'executable'):
        baza_exe = os.path.dirname(sys.executable)
        katalogi.append(baza_exe)
        katalogi.append(os.path.join(baza_exe, "_internal"))
        
    for k in katalogi:
        pelna = os.path.join(k, relatywna_sciezka)
        if os.path.exists(pelna):
            return pelna
            
    return relatywna_sciezka