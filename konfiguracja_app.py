import os
import sys

# ==========================================
# KONFIGURACJA I METADANE
# ==========================================
VERSION = "2.2.0"
DB_VERSION = "0"  # wersja bazy, gdy lokalny plik jej nie zawiera (baza z panelu diamel.pl ma numer wersji 1, 2, 3...)
BUILD_DATE = "2026-11-04 18:00"

CHANGELOG = """
v2.2.0 (2026-11-04)
- Napięcie na rozruszniku z porównania obwodów (jak w krzywych SAE J544): krzywa rozrusznika jest wyznaczona dla obwodu
  testowego (akumulator + kable) - program liczy rzeczywisty obwód: rezystancja wewnętrzna zestawu akumulatorów
  (z uwzględnieniem kilku rozruszników na jednym zestawie) + kable, i porównuje go z obwodem testowym z karty.
  Wcześniej spadek na kablach był odejmowany od napięcia z karty, które już go zawiera (wynik zaniżony).
- Nowe pola: rezystancja obwodu wg karty rozrusznika i rezystancja wewnętrzna akumulatora (wpisywane z bazy).
  Bez nich - dotychczasowa metoda uproszczona, oznaczona w oknie i w raporcie.
- Wykres i raport: linia obwodu projektu i krzywa z karty (obwód testowy).

v2.1.1 (2026-11-04)
- Pliki producentów z bazy (krzywe rozruszników, karty katalogowe) usuwane z komputera po wylogowaniu, wygaśnięciu sesji
  albo odebraniu dostępu - dostępne tylko dla zalogowanych.

v2.1.0 (2026-11-04)
- Baza urządzeń pobierana z serwera diamel.pl - administrator edytuje ją w panelu (jak listę pracowników w Korektorze HR).
- Nowa część bazy: silniki - wybranie silnika wpisuje agregat, napięcie, liczbę i model rozrusznika oraz wymagane CCA.
- Krzywe rozruszników i karty katalogowe z bazy (po zalogowaniu kontem Diamel): krzywa trafia do raportu, kartę można otworzyć.
- Zgłoszenia z załącznikami (karta katalogowa, zdjęcie tabliczki).

v2.0.0 (2026-11-04)
- Nowy wygląd programu (jak diamel.pl): jasny / ciemny motyw, jeden ekran z danymi i wynikami.
- Wyniki liczone na bieżąco podczas wpisywania - bez przycisku "Oblicz".
- Wybór napięcia układu 12 / 24 VDC.
- Napięcie kręcenia i napięcie minimalne z bazy rozrusznika (wcześniej zawsze 16 V) - sprawdzenie, czy napięcie na rozruszniku wystarcza.
- Spadek napięcia liczony płynnie w funkcji prądu: wykres napięcia na rozruszniku, prąd graniczny dla napięcia minimalnego.
- Spadek przy prądzie znamionowym rozrusznika z bazy (wcześniej zawsze 1000 A).
- CCA: wymagane CCA z karty katalogowej silnika (pole wyboru + wartość) jako kryterium oceny, z tolerancją niedoboru (domyślnie 10 %, w ustawieniach); bez niego ocena informacyjna (suma szczytów rozruszników).
- Konto Diamel (nieobowiązkowe): po zalogowaniu raporty na papierze firmowym Twojej firmy i inicjały z imienia i nazwiska.
- Pojemność: procent zużycia pojemności zestawu.
- Ładowarka: wyliczony prąd zaokrąglony w górę do pełnych 5 A ("około 20 A", zakres "15-20 A" gdy zapas jest mały) zamiast +5 A.
- Redundancja: drugi taki sam zestaw akumulatorów z ładowarką, przełączany co N rozruchów - każdy zestaw liczony osobno.
- Nowy raport (jak raport Korektora HR): wyniki w skrócie, obliczenia krok po kroku, wykres napięcia, schemat zestawu akumulatorów.
- Raport PDF albo DOCX; własny szablon Word z nagłówkiem i stopką (pola {PROJEKT}, {KLIENT}, {DATA} itd.).
- Raport angielski bez polskich wstawek; poprawione teksty raportu polskiego.
- Baza urządzeń jak lista pracowników w Korektorze HR: baza globalna pobierana w całości z serwera przy starcie, wpisy własne (●) osobno.
- Edytor bazy ze wszystkimi parametrami (wcześniej zapis z edytora kasował np. napięcie minimalne).
- Ostatnie projekty, pytanie o zapis zmian przy zamykaniu, zgłoszenia z dołączonym projektem.
- Awaryjna aktualizacja, gdy okno programu się nie uruchomi; administrator może wskazać zalecaną (starszą) wersję.

v1.2.0 (2026-11-02)
- Baza urządzeń aktualizowana z repozytorium - nowe rozruszniki i akumulatory bez instalowania nowej wersji programu.

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

# Aktualizacje (GitHub: wydania programu, baza z gałęzi master) i zgłoszenia (formularz na diamel.pl)
NAZWA_PROGRAMU = "kalkulator_rozruchu"
GITHUB_REPO = "Kuj0n/Diamel-Kalkulator-Rozruchu"
URL_BAZY = "https://diamel.pl/api/rozruch.php"  # baza urządzeń edytowana w panelu administracyjnym (Kalkulator Rozruchu)
URL_ZGLOSZEN = "https://diamel.pl/api/zgloszenie.php"
URL_KONTA = "https://diamel.pl/api/konto.php"  # logowanie kontem Diamel (szablon raportu firmy, inicjały)

def sciezka_do_zasobu(relatywna_sciezka):
    """ Pancerna funkcja szukająca plików zasobów w trybie .exe i developerskim """
    katalogi = [
        os.path.dirname(os.path.abspath(__file__)),
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