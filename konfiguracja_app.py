import os
import sys

# ==========================================
# KONFIGURACJA I METADANE
# ==========================================
VERSION = "1.0.1"
DB_VERSION = "1.0.1"
BUILD_DATE = "2026-10-23 10:00"

CHANGELOG = """
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
v1.0.1 (2026-10-23)
- Aktualizacja danych.

v1.0.0 (2026-10-01)
- Początkowa baza rozruszników (Delco Remy, Bosch).
- Początkowa baza akumulatorów (Optima, Varta).
"""

# Sekrety do podmiany przy kompilacji
ENCRYPTION_KEY = b"TUTAJ_KLUCZ"
EMAIL_NADAWCY = "TUTAJ_NADAWCA"
HASLO_NADAWCY = "TUTAJ_HASLO"
EMAIL_ODBIORCY = "TUTAJ_ODBIORCA"
SMTP_SERVER = "smtp.mail.ovh.net"
SMTP_PORT = 465

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