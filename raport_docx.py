"""
raport_docx.py

Raport układu rozruchowego (PL / EN) w Wordzie, w stylu raportów Diamel (jak raport braków Korektora HR):
nagłówek z danymi projektu, kafelki z najważniejszymi wynikami, sekcje z obliczeniami krok po kroku, wykres
napięcia na rozruszniku w funkcji prądu, załączniki. Liczby z obliczenia.oblicz - te same, które pokazuje okno.

Szablon (opcjonalnie): plik .docx użytkownika - z niego zostają nagłówek, stopka, marginesy i rozmiar strony,
treść szablonu jest pomijana. PDF: ten sam dokument zapisany przez Microsoft Word (zapisz_pdf).
"""
import os
import tempfile
from datetime import datetime

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor, Emu

CZCIONKA = "Segoe UI"
TEKST = RGBColor(0x11, 0x18, 0x27)
SZARY = RGBColor(0x6B, 0x72, 0x80)
AKCENT = RGBColor(0xB4, 0x53, 0x09)    # bursztyn Kalkulatora (ciemny - czytelny po wydruku w odcieniach szarości)
ZIELONY = RGBColor(0x04, 0x78, 0x57)
CZERWONY = RGBColor(0xB9, 0x1C, 0x1C)
NIEBIESKI = RGBColor(0x1D, 0x4E, 0xD8)
TLO_SEKCJI = "EEF0F3"
TLO_NAGLOWKA = "F5F6F8"
LINIA = "D1D5DB"

TEKSTY = {
    "Polski": {
        "eyebrow": "DOKUMENTACJA TECHNICZNA DO ZATWIERDZENIA",
        "tytul": "Obliczenia układu rozruchowego",
        "agregat": "Agregat", "silnik": "silnik",
        "meta": ["Numer projektu", "Klient", "Data", "Przygotował", "Agregat", "Silnik"],
        "k_napiecie": "Napięcie na rozruszniku", "k_pojemnosc": "Zużycie pojemności", "k_ladowarka": "Ładowarka", "k_cca": "CCA zestawu",
        "przy_szczycie": "przy prądzie szczytowym", "min": "min.", "z": "z", "zalecana": "zalecana", "wyliczone": "wyliczone",
        "info": "informacyjnie", "pokryte": "pokrywa szczyt",
        "ok": "Układ rozruchowy spełnia wymagania",
        "zle": "Układ rozruchowy wymaga poprawy",
        "problem_u": "napięcie na rozruszniku poniżej minimalnego", "problem_c": "zużycie przekracza pojemność akumulatorów",
        "problem_b": "napięcie zestawu akumulatorów ({u} V) różne od napięcia układu ({s} V)",
        "rewizje": "Historia zmian dokumentu", "rev_h": ["Rew.", "Opis zmiany", "Wykonał", "Sprawdził", "Data"],
        "s1": "Konfiguracja układu", "s2": "Spadek napięcia i napięcie na rozruszniku", "s3": "Akumulatory - prąd rozruchowy i pojemność",
        "s4": "Dobór ładowarki", "s5": "Uwagi i założenia", "zal": "Załącznik",
        "parametr": "Parametr", "wartosc": "Wartość", "wielkosc": "Wielkość", "obliczenie": "Obliczenie", "wynik": "Wynik",
        "g_rozruszniki": "Rozruszniki", "g_akumulatory": "Akumulatory", "g_kable": "Okablowanie", "g_profil": "Profil rozruchu",
        "model": "Producent / model", "ilosc": "Ilość w agregacie", "nap_ukladu": "Napięcie układu", "prad_znam": "Prąd znamionowy",
        "prad_szczyt": "Prąd szczytowy", "nap_krec": "Napięcie kręcenia (na akumulatorach)", "nap_min": "Napięcie minimalne rozrusznika",
        "technologia": "Technologia", "nap_akumulatora": "Napięcie / pojemność / CCA (1 szt.)", "polaczenie": "Połączenie",
        "polaczenie_w": "{s} szeregowo × {p} równolegle = {n} szt.", "zestaw": "Zestaw (napięcie / pojemność / CCA)",
        "dlugosc": "Długość kabli (tam i z powrotem)", "przekroj": "Przekrój", "przekroj_w": "{n} × {a} mm² na biegun",
        "proba": "Czas jednej próby", "proby": "Ilość prób rozruchu", "ladowanie": "Czas pełnego naładowania",
        "brak": "—", "szt": "szt.", "wlasny": "parametry wpisane ręcznie",
        "rezystancja": "Rezystancja linii kablowej", "spadek_znam": "Spadek napięcia przy prądzie znamionowym",
        "r_zestawu": "Rezystancja wewnętrzna zestawu akumulatorów", "r_obw": "Rezystancja obwodu na jeden rozrusznik",
        "r_obw_obl": "{q} × {z} mΩ (zestaw) + {k} mΩ (kable)", "r_obw_obl1": "{z} mΩ (zestaw) + {k} mΩ (kable)",
        "r_test": "Rezystancja obwodu testowego (krzywa rozrusznika)", "u0": "Napięcie bez obciążenia (z krzywej)",
        "u_min_ok_k": "Napięcie wystarczające - obwód {r} mΩ nie przekracza obwodu testowego {t} mΩ z krzywej rozrusznika; zapas {z} V ponad minimalne {m} V.",
        "u_min_zle_k": "Napięcie za niskie - obwód {r} mΩ jest większy niż obwód testowy {t} mΩ z krzywej rozrusznika; brakuje {z} V do minimalnego {m} V. Należy zmniejszyć rezystancję obwodu (więcej łańcuchów równoległych, większy przekrój albo krótsze kable).",
        "metoda_upr": "Metoda uproszczona (brak rezystancji obwodu testowego z karty rozrusznika albo rezystancji wewnętrznej akumulatora): od napięcia kręcenia z karty odjęto spadek na kablach. Wynik jest zachowawczy - napięcie z karty zawiera już spadek w obwodzie testowym.",
        "l_karta": "krzywa rozrusznika (obwód testowy {t} mΩ)", "l_obw": "obwód projektu {r} mΩ",
        "spadek_szczyt": "Spadek napięcia przy prądzie szczytowym", "u_szczyt": "Napięcie na rozruszniku (prąd szczytowy)",
        "u_znam": "Napięcie na rozruszniku (prąd znamionowy)", "u_min_ok": "Napięcie wystarczające - zapas {z} V ponad minimalne {m} V.",
        "u_min_zle": "Napięcie za niskie - brakuje {z} V do minimalnego {m} V. Należy zwiększyć przekrój albo skrócić kable.",
        "u_min_brak": "Napięcie minimalne rozrusznika nie zostało podane - nie sprawdzono.",
        "wykres": "Rys. {n}. Napięcie na rozruszniku w funkcji prądu: U(I) = U0 − I · R obwodu",
        "graniczny": "Napięcie minimalne zostanie osiągnięte przy prądzie {i} A.",
        "graniczny_0": "Napięcie kręcenia jest niższe niż napięcie minimalne rozrusznika.",
        "os_prad": "Prąd rozrusznika [A]", "os_nap": "Napięcie [V]", "l_znam": "znamionowy", "l_szczyt": "szczytowy", "l_min": "minimalne",
        "cca_dost": "CCA zestawu", "cca_wym": "Szczytowy prąd wszystkich rozruszników",
        "cca_silnik": "Wymagane CCA wg producenta silnika", "cca_silnik_obl": "karta katalogowa silnika {e}",
        "cca_silnik_ok": "CCA zestawu spełnia wymaganie producenta silnika ({c} A) - zapas {z} A.",
        "cca_silnik_zle": "CCA zestawu jest niższe niż wymaganie producenta silnika ({c} A) - brakuje {z} A. Należy zwiększyć liczbę łańcuchów równoległych albo dobrać akumulatory o większym CCA.",
        "cca_szczyt_info": "Informacyjnie: suma szczytowych prądów wszystkich rozruszników ({s} A) - prąd chwilowy przy załączeniu, nie jest kryterium doboru.",
        "problem_cca": "CCA zestawu poniżej wymagania producenta silnika", "k_cca_wym": "wymagane {c} A",
        "k_cca_tol": "wymagane {c} A · w tolerancji",
        "cca_silnik_tol": "CCA zestawu jest o {z} A ({p} %) niższe niż wymaganie producenta silnika ({c} A) - niedobór mieści się w przyjętej tolerancji {t} % i nie dyskwalifikuje akumulatorów.",
        "cca_ok": "CCA zestawu pokrywa szczytowy prąd wszystkich rozruszników.",
        "cca_normy": "CCA akumulatorów podano wg normy {a}, a wymaganie producenta silnika wg {s}. Metody badania obu norm różnią się (EN 50342-1: 10 s do 7,5 V, SAE J537: 30 s do 7,2 V), więc porównanie ma charakter orientacyjny - zaleca się potwierdzenie CCA akumulatora wg normy {s} u producenta.",
        "cca_info": "Informacyjnie: szczytowy prąd wszystkich rozruszników przekracza CCA zestawu. Prąd szczytowy występuje tylko przez krótką chwilę przy załączeniu rozrusznika i nie dyskwalifikuje akumulatorów.",
        "prad_rozr": "Prąd rozruchu (wszystkie rozruszniki)", "czas_rozr": "Łączny czas kręcenia", "zuzycie": "Zużycie pojemności",
        "pojemnosc": "Pojemność zestawu", "udzial": "Udział zużycia w pojemności", "krotnosc": "Zestaw jest {k}× większy niż zużycie w najgorszym scenariuszu (prąd szczytowy przez cały czas prób).",
        "poj_zle": "Zużycie przekracza pojemność zestawu - należy zwiększyć pojemność albo liczbę łańcuchów równoległych.",
        "wsp": "Współczynnik sprawności ładowania ({t})", "prad_lad": "Prąd ładowania", "zal_lad": "Zalecana ładowarka",
        "okolo": "około {a} A", "zakres": "{a}–{b} A", "lad_opis": "w górę do pełnych 5 A",
        "u_s_desc": "Krzywe wydajności rozrusznika są tworzone przy użyciu różnych metod (ISO, SAE, JIS, inne). Parametry, które mogą wpływać na wydajność rozrusznika, to temperatura, dostarczona krzywa akumulatora, rezystancja obwodu i inne. Jeśli mają być porównane dwie krzywe mocy rozrusznika, muszą być one utworzone przy użyciu tej samej metody. Moment obrotowy rozrusznika jest bezpośrednio związany z poborem prądu, a obroty - z napięciem dostępnym na rozruszniku. Dlatego moc wyjściowa rozrusznika zależy od napięcia dostępnego na nim przy określonym prądzie; prąd jest dyktowany przez moment obrotowy potrzebny do obrócenia silnika.",
        "u_zmienne": "Obliczenia nie uwzględniają zmiennych, które wpływają na rozruch i są trudne do oszacowania:",
        "u_lista": ["temperatura otoczenia", "minimalne napięcie akumulatorów wymagane do działania obwodu {v} V", "rezystancja obwodu (połączenia, izolatory)",
                    "lepkość i temperatura oleju silnikowego", "stan naładowania akumulatorów przed rozruchem",
                    "każda kolejna próba rozruchu musi pokonać początkową bezwładność silnika (maksymalny prąd przy minimalnym napięciu), co dodatkowo obciąża akumulatory"],
        "u_stan": "O ile układ jest w dobrym stanie technicznym, a kable są poprawnie dobrane, akumulatory zapewnią wymagane próby rozruchu.",
        "u_polaczenia": "Wszystkie zestawy akumulatorów zostaną podłączone do rozruszników zgodnie ze schematem połączeń. Agregat można odizolować po stronie DC przez otwarcie izolatorów, bez odłączania akumulatorów. Kable akumulatorowe - elastyczne przewody w izolacji PVC na biegunach dodatnich i ujemnych między akumulatorami a izolatorami.",
        "zal_nazwy": {"curve": "Krzywa rozrusznika", "batt": "Dane techniczne akumulatora", "diagram": "Schemat połączeń akumulatorów, izolatorów i rozruszników", "charger": "Specyfikacja ładowarki"},
        "strona": "Strona", "z_stron": "z", "stopka": "Obliczenia układu rozruchowego",
        "rys_bank": "Rys. {n}. Zestaw akumulatorów: {s} szeregowo × {p} równolegle ({u} V, {ah} Ah, {cca} A CCA)",
        "rys_bank2": "Rys. {n}. {k} jednakowe zestawy akumulatorów, każdy {s} szeregowo × {p} równolegle ({u} V, {ah} Ah, {cca} A CCA)",
        "zestaw_x": "Zestaw {x}", "przelacznik": "przekaźniki / styczniki zmiany zestawu", "do_rozrusznikow": "do rozruszników",
        "s_redund": "Redundancja układu rozruchowego", "g_redund": "Redundancja",
        "r_zestawy": "Liczba zestawów", "r_zestawy_w": "{k} jednakowe zestawy (akumulatory + ładowarka)",
        "r_akum": "Akumulatory w jednym zestawie", "r_akum_razem": "Akumulatory łącznie (do zamówienia)", "r_lad": "Ładowarki (każda dla swojego zestawu)",
        "r_zmiana": "Zmiana zestawu", "r_zmiana_w": "co {n} rozruchów (przekaźniki / styczniki)", "r_zmiana_brak": "przy awarii zestawu",
        "r_opis": "Układ ma {k} niezależne, jednakowe zestawy akumulatorów, każdy z własną ładowarką. Zestawy są zawsze przełączane, nigdy łączone równolegle - każdy zestaw sam zapewnia pełny profil rozruchu, a obliczenia w rozdziałach 2-4 (CCA, pojemność, ładowarka) dotyczą jednego zestawu. W razie awarii jednego zestawu rozruch zapewnia pozostały.",
        "r_opis_zmiana": " Zestawy są przełączane przekaźnikami / stycznikami co {n} rozruchów, dzięki czemu akumulatory zużywają się równomiernie, a każdy zestaw jest regularnie sprawdzany w pracy.",
    },
    "English": {
        "eyebrow": "TECHNICAL SUBMITTAL FOR APPROVAL",
        "tytul": "Generator Starting System Calculations",
        "agregat": "Generator set", "silnik": "engine",
        "meta": ["Project number", "Intended for", "Date", "Prepared by", "Generator set", "Engine"],
        "k_napiecie": "Voltage at starter", "k_pojemnosc": "Capacity used", "k_ladowarka": "Battery charger", "k_cca": "Battery set CCA",
        "przy_szczycie": "at peak current", "min": "min.", "z": "of", "zalecana": "recommended", "wyliczone": "calculated",
        "info": "for information", "pokryte": "covers peak",
        "ok": "The starting system meets the requirements",
        "zle": "The starting system needs improvement",
        "problem_u": "voltage at starter below minimum", "problem_c": "consumption exceeds battery capacity",
        "problem_b": "battery set voltage ({u} V) differs from system voltage ({s} V)",
        "rewizje": "Document revisions", "rev_h": ["Rev.", "Description of change", "Drawn", "Checked", "Date"],
        "s1": "System configuration", "s2": "Voltage drop and voltage at the starter motor", "s3": "Batteries - cranking current and capacity",
        "s4": "Battery charger sizing", "s5": "Notes and assumptions", "zal": "Appendix",
        "parametr": "Parameter", "wartosc": "Value", "wielkosc": "Quantity", "obliczenie": "Calculation", "wynik": "Result",
        "g_rozruszniki": "Starter motors", "g_akumulatory": "Batteries", "g_kable": "Battery cables", "g_profil": "Cranking profile",
        "model": "Manufacturer / model", "ilosc": "Quantity per generator set", "nap_ukladu": "System voltage", "prad_znam": "Rated current",
        "prad_szczyt": "Peak current", "nap_krec": "Cranking voltage (at batteries)", "nap_min": "Starter minimum voltage",
        "technologia": "Technology", "nap_akumulatora": "Voltage / capacity / CCA (1 pc.)", "polaczenie": "Connection",
        "polaczenie_w": "{s} in series × {p} in parallel = {n} pcs.", "zestaw": "Battery set (voltage / capacity / CCA)",
        "dlugosc": "Cable length (total, both ways)", "przekroj": "Cross-section", "przekroj_w": "{n} × {a} mm² per pole",
        "proba": "Cranking time per attempt", "proby": "Number of attempts", "ladowanie": "Full re-charge time",
        "brak": "—", "szt": "pcs.", "wlasny": "custom parameters",
        "rezystancja": "Battery cable resistance", "spadek_znam": "Voltage drop at rated current",
        "r_zestawu": "Battery set internal resistance", "r_obw": "Circuit resistance per starter motor",
        "r_obw_obl": "{q} × {z} mΩ (battery set) + {k} mΩ (cables)", "r_obw_obl1": "{z} mΩ (battery set) + {k} mΩ (cables)",
        "r_test": "Test circuit resistance (starter curve)", "u0": "Open-circuit voltage (from the curve)",
        "u_min_ok_k": "Voltage sufficient - the {r} mΩ circuit does not exceed the {t} mΩ test circuit of the starter curve; {z} V margin above the {m} V minimum.",
        "u_min_zle_k": "Voltage too low - the {r} mΩ circuit exceeds the {t} mΩ test circuit of the starter curve; {z} V below the {m} V minimum. Reduce the circuit resistance (more parallel strings, larger cross-section or shorter cables).",
        "metoda_upr": "Simplified method (no test circuit resistance from the starter data sheet or no battery internal resistance): the cable voltage drop was subtracted from the cranking voltage of the data sheet. The result is conservative - the data sheet voltage already includes the drop in the test circuit.",
        "l_karta": "starter curve (test circuit {t} mΩ)", "l_obw": "project circuit {r} mΩ",
        "spadek_szczyt": "Voltage drop at peak current", "u_szczyt": "Voltage at starter (peak current)",
        "u_znam": "Voltage at starter (rated current)", "u_min_ok": "Voltage sufficient - {z} V margin above the {m} V minimum.",
        "u_min_zle": "Voltage too low - {z} V below the {m} V minimum. Increase the cable cross-section or shorten the cables.",
        "u_min_brak": "Starter minimum voltage not given - not checked.",
        "wykres": "Fig. {n}. Voltage at the starter motor versus current: U(I) = U0 − I · R circuit",
        "graniczny": "The minimum voltage is reached at {i} A.",
        "graniczny_0": "The cranking voltage is lower than the starter minimum voltage.",
        "os_prad": "Starter current [A]", "os_nap": "Voltage [V]", "l_znam": "rated", "l_szczyt": "peak", "l_min": "minimum",
        "cca_dost": "Battery set CCA", "cca_wym": "Peak current of all starter motors",
        "cca_silnik": "CCA required by the engine manufacturer", "cca_silnik_obl": "engine data sheet {e}",
        "cca_silnik_ok": "The battery set CCA meets the engine manufacturer's requirement ({c} A) - margin {z} A.",
        "cca_silnik_zle": "The battery set CCA is lower than the engine manufacturer's requirement ({c} A) - short by {z} A. Increase the number of parallel strings or select batteries with higher CCA.",
        "cca_szczyt_info": "For information: sum of the peak currents of all starter motors ({s} A) - a momentary current at engagement, not a sizing criterion.",
        "problem_cca": "battery set CCA below the engine manufacturer's requirement", "k_cca_wym": "required {c} A",
        "k_cca_tol": "required {c} A · within tolerance",
        "cca_silnik_tol": "The battery set CCA is {z} A ({p} %) lower than the engine manufacturer's requirement ({c} A) - the shortfall is within the accepted {t} % tolerance and does not disqualify the batteries.",
        "cca_ok": "The battery set CCA covers the peak current of all starter motors.",
        "cca_normy": "The battery CCA is rated to {a}, while the engine manufacturer's requirement is given to {s}. The test methods of the two standards differ (EN 50342-1: 10 s to 7.5 V, SAE J537: 30 s to 7.2 V), so the comparison is indicative only - it is recommended to confirm the battery CCA to {s} with the manufacturer.",
        "cca_info": "For information: the peak current of all starter motors exceeds the battery set CCA. The peak current occurs only for a short moment at starter engagement and does not disqualify the batteries.",
        "prad_rozr": "Cranking current (all starter motors)", "czas_rozr": "Total cranking time", "zuzycie": "Capacity consumed",
        "pojemnosc": "Battery set capacity", "udzial": "Share of capacity used", "krotnosc": "The battery set is {k}× larger than the consumption in the worst-case scenario (peak current for the whole cranking time).",
        "poj_zle": "The consumption exceeds the battery set capacity - increase the capacity or the number of parallel strings.",
        "wsp": "Charging efficiency factor ({t})", "prad_lad": "Charging current", "zal_lad": "Recommended charger",
        "okolo": "approx. {a} A", "zakres": "{a}–{b} A", "lad_opis": "rounded up to full 5 A",
        "u_s_desc": "Cranking motor performance curves are created using various methods (ISO, SAE, JIS, other). Parameters that can affect the performance of a cranking motor are temperature, battery curve supplied, circuit resistance, and others. If two cranking motor power curves are to be compared, the curves must be created using the same method. Cranking motor torque is directly related to its current draw, and its RPM to the voltage available at the cranking motor. Therefore the output power depends on the voltage available at the cranking motor while drawing a certain current; the current is dictated by the torque required to turn the engine.",
        "u_zmienne": "The calculations do not take into account variables that affect starting and are extremely difficult to quantify:",
        "u_lista": ["ambient temperature", "minimal battery voltage required for the {v}-volt circuit to operate", "circuit resistance (connections, isolators)",
                    "engine oil viscosity and oil temperature", "state of charge prior to starting",
                    "every next cranking attempt has to overcome the initial inertia of the engine (max current at min voltage), which puts additional strain on the batteries"],
        "u_stan": "Providing the system is in good service condition with correctly sized battery cables, the batteries will provide the required cranking attempts.",
        "u_polaczenia": "All battery banks will be coupled to the starter motors as per the connection diagram. The generator can be DC isolated by opening the isolator switches, without disconnecting the batteries. Battery cables will be tri-rated PVC flexible cable on the positives and negatives between the battery terminals and isolators.",
        "zal_nazwy": {"curve": "Starter motor curve", "batt": "Battery technical data", "diagram": "Batteries / isolators / starter motors connection diagram", "charger": "Battery charger specification"},
        "strona": "Page", "z_stron": "of", "stopka": "Generator Starting System Calculations",
        "rys_bank": "Fig. {n}. Battery set: {s} in series × {p} in parallel ({u} V, {ah} Ah, {cca} A CCA)",
        "rys_bank2": "Fig. {n}. {k} identical battery sets, each {s} in series × {p} in parallel ({u} V, {ah} Ah, {cca} A CCA)",
        "zestaw_x": "Set {x}", "przelacznik": "changeover relays / contactors", "do_rozrusznikow": "to starter motors",
        "s_redund": "Starting system redundancy", "g_redund": "Redundancy",
        "r_zestawy": "Number of sets", "r_zestawy_w": "{k} identical sets (batteries + charger)",
        "r_akum": "Batteries per set", "r_akum_razem": "Batteries in total (to order)", "r_lad": "Battery chargers (each for its own set)",
        "r_zmiana": "Set changeover", "r_zmiana_w": "every {n} starts (relays / contactors)", "r_zmiana_brak": "on set failure",
        "r_opis": "The system has {k} independent, identical battery sets, each with its own battery charger. The sets are always switched over, never connected in parallel - each set alone provides the full cranking profile, and the calculations in sections 2-4 (CCA, capacity, charger) refer to one set. If one set fails, the remaining set provides the start.",
        "r_opis_zmiana": " The sets are switched by relays / contactors every {n} starts, so the batteries wear evenly and each set is regularly proven in operation.",
    },
}

# Opisy techniczne metody w rozdziałach raportu
OPISY = {
    "Polski": {
        "o_konfig": "Zestawienie danych wejściowych obliczeń. Parametry rozrusznika pochodzą z karty katalogowej producenta (prąd znamionowy - prąd kręcenia po rozpędzeniu silnika, prąd szczytowy - chwila załączenia, gdy wirnik jest jeszcze nieruchomy). Napięcie kręcenia to napięcie na zaciskach akumulatorów pod obciążeniem rozruchowym; napięcie minimalne - najniższe napięcie na zaciskach rozrusznika, przy którym zapewnia on jeszcze obroty potrzebne do uruchomienia silnika.",
        "o_spadek": "Krzywa rozrusznika (np. wg SAE J544) jest wyznaczona dla obwodu testowego o określonej rezystancji (akumulator + kable): napięcie na rozruszniku opisuje prosta U(I) = U0 − I·R_test, gdzie U0 to napięcie akumulatorów bez obciążenia. W rzeczywistym układzie napięcie na rozruszniku wynosi U(I) = U0 − I·R_obw, gdzie R_obw to rezystancja wewnętrzna zestawu akumulatorów (szeregowo się sumuje, łańcuchy równoległe ją dzielą; gdy z jednego zestawu kręci kilka rozruszników naraz, przez akumulatory płynie suma ich prądów) i rezystancja kabli R = ρ·L / (n·A) (ρ = 1,68·10⁻⁸ Ω·m - miedź w 20 °C, L - długość obwodu tam i z powrotem, n - żyły równolegle na biegun, A - przekrój żyły). Gdy R_obw nie przekracza R_test, rozrusznik pracuje co najmniej tak, jak pokazuje krzywa. Najgorszy przypadek to prąd szczytowy w chwili załączenia.",
        "o_spadek_uwagi": "Obliczenie nie obejmuje rezystancji zacisków, połączeń i izolatorów ani wzrostu rezystancji z temperaturą (dla miedzi ok. 0,4 % na 1 °C - kabel o temperaturze 60 °C ma rezystancję o ok. 16 % większą niż w 20 °C). W razie małego zapasu napięcia warto zwiększyć przekrój albo skrócić kable.",
        "o_cca": "CCA (Cold Cranking Amps, wg SAE J537) to prąd, który nowy, w pełni naładowany akumulator 12 V oddaje przez 30 s w temperaturze −18 °C, utrzymując napięcie co najmniej 7,2 V. Norma EN 50342-1 stosuje inną metodę badania, więc wartości CCA wg SAE i EN nie są wprost porównywalne. W zestawie łańcuchy połączone równolegle sumują prąd CCA i pojemność, a akumulatory połączone szeregowo - napięcie.",
        "o_pojemnosc": "Zużycie ładunku podczas rozruchu: Q = I·t, gdzie I to łączny prąd wszystkich rozruszników, a t - łączny czas kręcenia we wszystkich próbach. Przyjęto prąd szczytowy przez cały czas prób - w rzeczywistości po rozpędzeniu silnika prąd spada do wartości znamionowej, więc wynik jest zachowawczy. Przy dużych prądach rozładowania akumulator oddaje mniej niż pojemność nominalna (podawaną zwykle dla rozładowania 20-godzinnego, C20 - efekt Peukerta); uwzględnia to zapas pojemności zestawu. Akumulatory rozruchowe agregatu są stale utrzymywane w stanie naładowania przez ładowarkę, dlatego kryterium jest zużycie mniejsze od pojemności zestawu.",
        "o_ladowarka": "Prąd ładowarki potrzebny do uzupełnienia ładunku pobranego podczas rozruchu w zadanym czasie: I = Q·k / t, gdzie k to współczynnik sprawności ładowania (do akumulatora trzeba dostarczyć więcej ładunku niż z niego pobrano - straty na ciepło i reakcje uboczne): 1,4 dla akumulatorów kwasowo-ołowiowych, 1,2 dla AGM i Li-Ion.",
        "o_ladowarka_uwagi": "Ładowarka pracuje stale w trybie podtrzymania (float). Jeśli zasila też odbiorniki stałe agregatu (sterownik, przekaźniki, grzałki, oświetlenie), ich prąd należy dodać do wyliczonego prądu ładowania.",
    },
    "English": {
        "o_konfig": "Summary of the calculation input data. The starter motor parameters are taken from the manufacturer's data sheet (rated current - cranking current once the engine is rolling, peak current - the moment of engagement with the armature still stationary). The cranking voltage is the voltage at the battery terminals under cranking load; the minimum voltage is the lowest voltage at the starter terminals at which it still provides the speed needed to start the engine.",
        "o_spadek": "The starter motor curve (e.g. per SAE J544) is determined for a test circuit of a specified resistance (battery + cables): the voltage at the starter follows the line U(I) = U0 − I·R_test, where U0 is the open-circuit battery voltage. In the actual system the voltage at the starter is U(I) = U0 − I·R_circ, where R_circ is the internal resistance of the battery set (adds up in series, divided by parallel strings; when several starters crank from one battery set, the sum of their currents flows through the batteries) plus the cable resistance R = ρ·L / (n·A) (ρ = 1.68·10⁻⁸ Ω·m - copper at 20 °C, L - circuit length both ways, n - cores in parallel per pole, A - core cross-section). When R_circ does not exceed R_test, the starter performs at least as shown by the curve. The worst case is the peak current at engagement.",
        "o_spadek_uwagi": "The calculation does not include the resistance of terminals, connections and isolators, nor the increase of resistance with temperature (about 0.4 % per 1 °C for copper - a cable at 60 °C has about 16 % higher resistance than at 20 °C). If the voltage margin is small, increase the cross-section or shorten the cables.",
        "o_cca": "CCA (Cold Cranking Amps, per SAE J537) is the current a new, fully charged 12 V battery can deliver for 30 s at −18 °C while maintaining at least 7.2 V. EN 50342-1 uses a different test method, so SAE and EN CCA values are not directly comparable. In a battery set, strings connected in parallel add up CCA and capacity, batteries connected in series add up voltage.",
        "o_pojemnosc": "Charge consumed during starting: Q = I·t, where I is the total current of all starter motors and t the total cranking time of all attempts. The peak current is assumed for the whole cranking time - in reality the current drops to the rated value once the engine is rolling, so the result is conservative. At high discharge currents a battery delivers less than its nominal capacity (usually stated for a 20-hour discharge, C20 - Peukert effect); this is covered by the battery set capacity margin. Generator starting batteries are permanently kept charged by the battery charger, so the criterion is consumption lower than the battery set capacity.",
        "o_ladowarka": "Charger current needed to replace the charge drawn during starting within the given time: I = Q·k / t, where k is the charging efficiency factor (more charge has to be returned to the battery than was drawn - losses to heat and side reactions): 1.4 for lead-acid, 1.2 for AGM and Li-Ion batteries.",
        "o_ladowarka_uwagi": "The charger works permanently in float mode. If it also supplies the generator's permanent loads (controller, relays, heaters, lighting), their current has to be added to the calculated charging current.",
    },
}

TYPY = {"Polski": {"Lead-Acid": "kwasowo-ołowiowe", "AGM": "AGM", "Li-Ion": "litowo-jonowe"},
        "English": {"Lead-Acid": "Lead-Acid", "AGM": "AGM", "Li-Ion": "Li-Ion"}}


# ------------------------------------------------------------------ pomocnicze: formatowanie i XML Worda

class Liczby:
    """Liczby w języku raportu: 1 014,23 (PL) / 1,014.23 (EN)."""

    def __init__(self, jezyk):
        self.pl = jezyk == "Polski"

    def _jezyk(self, t):
        return t.replace(",", " ").replace(".", ",") if self.pl else t

    def __call__(self, x, miejsca=2):
        return "—" if x is None else self._jezyk(f"{x:,.{miejsca}f}")

    def g(self, x):
        """Bez zbędnych zer: 12.5 -> 12,5; 95.0 -> 95."""
        t = f"{x:,.4f}"
        return self._jezyk(t.rstrip("0").rstrip(".") if "." in t else t)


def _tlo(komorka, kolor):
    tc = komorka._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), kolor)
    tc.append(shd)


def _ramki_komorki(komorka, **boki):
    """boki: top/bottom/left/right = (grubość w 1/8 pt, kolor) albo None (bez ramki)."""
    tcPr = komorka._tc.get_or_add_tcPr()
    ramki = OxmlElement("w:tcBorders")
    for bok in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{bok}")
        wartosc = boki.get(bok)
        if wartosc:
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), str(wartosc[0]))
            el.set(qn("w:color"), wartosc[1])
        else:
            el.set(qn("w:val"), "nil")
        ramki.append(el)
    tcPr.append(ramki)


def _bez_ramek(tabela):
    tblPr = tabela._tbl.tblPr
    ramki = OxmlElement("w:tblBorders")
    for bok in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{bok}")
        el.set(qn("w:val"), "nil")
        ramki.append(el)
    tblPr.append(ramki)


def _marginesy_komorek(tabela, gora=40, dol=40, lewo=90, prawo=90):
    tblPr = tabela._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for bok, w in (("top", gora), ("left", lewo), ("bottom", dol), ("right", prawo)):
        el = OxmlElement(f"w:{bok}")
        el.set(qn("w:w"), str(w))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblPr.append(mar)


def _ramka_akapitu(akapit, bok, grubosc, kolor, odstep=4):
    pPr = akapit._p.get_or_add_pPr()
    pBdr = pPr.find(qn("w:pBdr"))
    if pBdr is None:
        pBdr = OxmlElement("w:pBdr")
        pPr.append(pBdr)
    el = OxmlElement(f"w:{bok}")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), str(grubosc))
    el.set(qn("w:space"), str(odstep))
    el.set(qn("w:color"), kolor)
    pBdr.append(el)


def _tlo_akapitu(akapit, kolor):
    pPr = akapit._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), kolor)
    pPr.append(shd)


def _pole(akapit, kod, rozmiar, kolor):
    """Pole Worda (PAGE, NUMPAGES) - numer strony w stopce."""
    run = akapit.add_run()
    _styl_runu(run, rozmiar, kolor=kolor)
    for typ, tekst in (("begin", None), (None, kod), ("separate", None), (None, "1"), ("end", None)):
        if typ:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), typ)
        elif tekst == kod:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = f" {kod} "
        else:
            el = OxmlElement("w:t")
            el.text = tekst
        run._r.append(el)


def _styl_runu(run, rozmiar=9.5, pogrubienie=False, kolor=TEKST, kursywa=False, czcionka=CZCIONKA):
    run.font.name = czcionka
    run._r.get_or_add_rPr().get_or_add_rFonts().set(qn("w:cs"), czcionka)
    run.font.size = Pt(rozmiar)
    run.font.bold = pogrubienie
    run.font.italic = kursywa
    run.font.color.rgb = kolor
    return run


def _odstepy(akapit, przed=0, po=0, interlinia=1.1):
    f = akapit.paragraph_format
    f.space_before = Pt(przed)
    f.space_after = Pt(po)
    f.line_spacing = interlinia


class Raport:
    def __init__(self, stan, w, obrazy, szablon=""):
        self.stan, self.w, self.obrazy = stan, w, obrazy
        self.jezyk = stan.get("language") if stan.get("language") in TEKSTY else "English"
        self.t = {**TEKSTY[self.jezyk], **OPISY[self.jezyk]}
        self.n = Liczby(self.jezyk)
        self.szablon = bool(szablon and os.path.isfile(szablon))
        self.doc = Document(szablon) if self.szablon else Document()
        self.nr_rys = 0
        self._przygotuj()

    # -------------------------------------------------------------- dokument, strona, stopka

    def _przygotuj(self):
        body = self.doc.element.body
        for el in list(body):
            if el.tag != qn("w:sectPr"):
                body.remove(el)  # treść szablonu pomijana - zostaje nagłówek, stopka i ustawienia strony
        normal = self.doc.styles["Normal"]
        normal.font.name = CZCIONKA
        normal.font.size = Pt(9.5)
        normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:cs"), CZCIONKA)
        sekcja = self.doc.sections[0]
        if self.szablon:
            self._wypelnij_pola_szablonu()
        else:
            sekcja.page_width, sekcja.page_height = Cm(21), Cm(29.7)
            sekcja.left_margin = sekcja.right_margin = Cm(1.8)
            sekcja.top_margin, sekcja.bottom_margin = Cm(1.6), Cm(1.8)
            sekcja.footer_distance = Cm(0.9)
            self._stopka(sekcja)
        self.szer = sekcja.page_width - sekcja.left_margin - sekcja.right_margin

    def _wypelnij_pola_szablonu(self):
        """Pola w nagłówku / stopce szablonu: {PROJEKT} {KLIENT} {AGREGAT} {SILNIK} {AUTOR} {DATA} {TYTUL}."""
        s = self.stan
        pola = {"{PROJEKT}": s.get("project_no", ""), "{KLIENT}": s.get("client", ""), "{AGREGAT}": s.get("genset", ""),
                "{SILNIK}": s.get("engine", ""), "{AUTOR}": s.get("author", ""), "{DATA}": datetime.now().strftime("%Y-%m-%d"),
                "{TYTUL}": self.t["tytul"], "{STRONA}": self.t["strona"], "{Z}": self.t["z_stron"]}

        def zamien(tekst):
            for k, v in pola.items():
                tekst = tekst.replace(k, v)
            return tekst
        for sekcja in self.doc.sections:
            for czesc in (sekcja.header, sekcja.footer, sekcja.first_page_header, sekcja.first_page_footer):
                akapity = list(czesc.paragraphs) + [p for tab in czesc.tables for w in tab.rows for k in w.cells for p in k.paragraphs]
                for p in akapity:
                    for r in p.runs:  # najpierw w obrębie fragmentów - zostaje formatowanie i pola Worda (numer strony)
                        if "{" in r.text:
                            r.text = zamien(r.text)
                    tekst = "".join(r.text for r in p.runs)
                    if not any(k in tekst for k in pola) or p._p.find(".//" + qn("w:fldChar")) is not None:
                        continue
                    p.runs[0].text = zamien(tekst)  # pole rozbite przez Worda na kilka fragmentów - formatowanie pierwszego
                    for r in p.runs[1:]:
                        r.text = ""

    def _stopka(self, sekcja):
        p = sekcja.footer.paragraphs[0]
        tabulatory = p.paragraph_format.tab_stops
        for poz in (Inches(3.25), Inches(6.5)):  # tabulatory stylu "Stopka" Worda (środek, prawo) - numer strony ma być przy prawym marginesie
            tabulatory.add_tab_stop(poz, WD_TAB_ALIGNMENT.CLEAR)
        tabulatory.add_tab_stop(sekcja.page_width - sekcja.left_margin - sekcja.right_margin, WD_TAB_ALIGNMENT.RIGHT)
        _ramka_akapitu(p, "top", 4, LINIA, 6)
        nazwa = " · ".join(x for x in (self.stan.get("project_no", ""), self.t["stopka"]) if x)
        _styl_runu(p.add_run(f"{nazwa}\t{self.t['strona']} "), 7.5, kolor=SZARY)
        _pole(p, "PAGE", 7.5, SZARY)
        _styl_runu(p.add_run(f" {self.t['z_stron']} "), 7.5, kolor=SZARY)
        _pole(p, "NUMPAGES", 7.5, SZARY)

    def akapit(self, tekst="", rozmiar=9.5, pogrubienie=False, kolor=TEKST, przed=0, po=4, wyrownanie=None, kursywa=False):
        p = self.doc.add_paragraph()
        _odstepy(p, przed, po)
        if wyrownanie:
            p.alignment = wyrownanie
        if tekst:
            _styl_runu(p.add_run(tekst), rozmiar, pogrubienie, kolor, kursywa)
        return p

    def tabela(self, wiersze, kolumny):
        tab = self.doc.add_table(rows=wiersze, cols=kolumny)
        tab.alignment = WD_TABLE_ALIGNMENT.CENTER
        tab.autofit = False
        _bez_ramek(tab)
        _marginesy_komorek(tab)
        return tab

    @staticmethod
    def komorka(komorka, tekst, rozmiar=9, pogrubienie=False, kolor=TEKST, wyrownanie=None, kursywa=False):
        p = komorka.paragraphs[0]
        _odstepy(p, 0, 0, 1.05)
        if wyrownanie:
            p.alignment = wyrownanie
        _styl_runu(p.add_run(tekst), rozmiar, pogrubienie, kolor, kursywa)
        komorka.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        return p

    def szerokosci(self, tab, proporcje):
        suma = sum(proporcje)
        for wiersz in tab.rows:
            for k, p in zip(wiersz.cells, proporcje):
                k.width = Emu(int(self.szer * p / suma))

    # -------------------------------------------------------------- elementy raportu

    def naglowek(self):
        t, s, n = self.t, self.stan, self.n
        p = self.akapit(t["eyebrow"], 7.5, kolor=AKCENT, po=2)
        p.runs[0].font.bold = True
        self.akapit(t["tytul"], 20, True, po=2)
        podtytul = " · ".join(x for x in (s.get("genset") and f"{t['agregat']} {s['genset']}", s.get("engine") and f"{t['silnik']} {s['engine']}") if x)
        p = self.akapit(podtytul or " ", 10.5, kolor=SZARY, po=8)
        _ramka_akapitu(p, "bottom", 12, "111827", 6)

        tab = self.tabela(2, 3)
        wartosci = [s.get("project_no", ""), s.get("client", ""), datetime.now().strftime("%Y-%m-%d"), s.get("author", ""), s.get("genset", ""), s.get("engine", "")]
        for i, (etykieta, wartosc) in enumerate(zip(t["meta"], wartosci)):
            k = tab.cell(i // 3, i % 3)
            self.komorka(k, etykieta.upper(), 6.5, kolor=SZARY)
            p = k.add_paragraph()
            _odstepy(p, 1, 2)
            _styl_runu(p.add_run(wartosc or "—"), 10, True)
        self.szerokosci(tab, [1, 1, 1])
        self.akapit(po=6)

    def kafelki(self):
        t, w, n = self.t, self.w, self.n
        lad = t["zakres"].format(a=w["ladowarka_od"], b=w["ladowarka_do"]) if w["ladowarka_do"] else t["okolo"].format(a=w["ladowarka_od"])
        kafelki = [
            (t["k_napiecie"], f"{n(w['sustained_voltage'])} V", f"{t['przy_szczycie']}" + (f" · {t['min']} {n(w['min_v'], 1)} V" if w["min_v"] else ""), w["napiecie_ok"]),
            (t["k_pojemnosc"], f"{n(w['zuzycie_proc'], 1)} %", f"{n(w['consumed_ah'])} Ah {t['z']} {n.g(w['total_ah_available'])} Ah", w["pojemnosc_ok"]),
            (t["k_ladowarka"], (f"{w['zestawy']} × " if w["zestawy"] > 1 else "") + lad, f"{t['wyliczone']} {n(w['charger_amps'])} A", None),
            (t["k_cca"], f"{n.g(w['total_cca_available'])} A", t["k_cca_tol" if w["cca_stan"] == "tolerancja" else "k_cca_wym"].format(c=n.g(w["cca_silnika"])),
             {"ok": True, "tolerancja": "info", "zle": False}[w["cca_stan"]]) if w["cca_znane"] else
            (t["k_cca"], f"{n.g(w['total_cca_available'])} A", t["pokryte"] if w["cca_ok"] else t["info"], "info" if not w["cca_ok"] else True),
        ]
        tab = self.tabela(1, 4)
        _marginesy_komorek(tab, 90, 90, 130, 130)
        for k, (etykieta, wartosc, opis, ok) in zip(tab.rows[0].cells, kafelki):
            _ramki_komorki(k, top=(6, "9CA3AF"), bottom=(6, "9CA3AF"), left=(6, "9CA3AF"), right=(6, "9CA3AF"))
            p = self.komorka(k, etykieta.upper(), 6.5, kolor=SZARY)
            p = k.add_paragraph()
            _odstepy(p, 2, 1)
            _styl_runu(p.add_run(wartosc), 14, True)
            if ok is not None:  # ✓ spełnione, ✗ niespełnione, i - informacyjnie; ładowarka i brak danych bez oceny
                symbol, kolor = {True: ("✓", ZIELONY), False: ("✗", CZERWONY), "info": ("i", NIEBIESKI)}[ok]
                _styl_runu(p.add_run(f"  {symbol}"), 11, True, kolor, czcionka="Segoe UI Symbol")
            p = k.add_paragraph()
            _odstepy(p, 0, 0)
            _styl_runu(p.add_run(opis), 7.5, kolor=SZARY)
        self.szerokosci(tab, [1, 1, 1, 1])

        problemy = [p for p, jest in ((t["problem_u"], w["napiecie_ok"] is False), (t["problem_c"], not w["pojemnosc_ok"]),
                                      (t["problem_b"].format(u=n.g(w["napiecie_banku"]), s=n.g(w["system_v"])), not w["napiecie_zgodne"]),
                                      (t["problem_cca"], w["cca_stan"] == "zle")) if jest]
        p = self.akapit(przed=10, po=10)
        _ramka_akapitu(p, "left", 24, "047857" if not problemy else "B91C1C", 8)
        _styl_runu(p.add_run("✓  " if not problemy else "✗  "), 11, True, ZIELONY if not problemy else CZERWONY, czcionka="Segoe UI Symbol")
        _styl_runu(p.add_run(t["ok"] if not problemy else t["zle"]), 11, True)
        if problemy:
            _styl_runu(p.add_run(" - " + "; ".join(problemy)), 9.5, kolor=CZERWONY)

    def rewizje(self):
        rew = self.stan.get("revisions") or []
        if not rew:
            return
        self.akapit(self.t["rewizje"].upper(), 7, True, SZARY, przed=2, po=3)
        tab = self.tabela(1 + len(rew), 5)
        for i, h in enumerate(self.t["rev_h"]):
            k = tab.cell(0, i)
            self.komorka(k, h.upper(), 6.5, True, SZARY)
            _ramki_komorki(k, bottom=(6, "111827"))
        for r_i, r in enumerate(rew, 1):
            for j, klucz in enumerate(("rev", "desc", "drawn", "check", "date")):
                k = tab.cell(r_i, j)
                self.komorka(k, str(r.get(klucz, "")), 8.5)
                _ramki_komorki(k, bottom=(4, LINIA))
        self.szerokosci(tab, [0.6, 4.4, 1, 1, 1.2])

    def sekcja(self, nr, tytul, nowa_strona=False):
        p = self.akapit(przed=4 if nowa_strona else 14, po=6)
        if nowa_strona:
            p.paragraph_format.page_break_before = True
        p.paragraph_format.keep_with_next = True
        _tlo_akapitu(p, TLO_SEKCJI)
        _ramka_akapitu(p, "left", 30, "111827", 6)
        _styl_runu(p.add_run(f"{nr}   "), 11, True, AKCENT)
        _styl_runu(p.add_run(tytul), 11, True)

    def tabela_wartosci(self, grupy, kolumny, proporcje):
        """grupy: [(nazwa grupy albo None, [(komórki...), ...])] - wiersze z cienką linią, grupy jako podtytuł."""
        wiersze = sum(len(g[1]) + (1 if g[0] else 0) for g in grupy) + 1
        tab = self.tabela(wiersze, len(kolumny))
        for i, h in enumerate(kolumny):
            k = tab.cell(0, i)
            self.komorka(k, h.upper(), 6.5, True, SZARY, WD_ALIGN_PARAGRAPH.RIGHT if i == len(kolumny) - 1 else None)
            _ramki_komorki(k, bottom=(6, "111827"))
        r = 1
        for nazwa, pozycje in grupy:
            if nazwa:
                scal = tab.cell(r, 0).merge(tab.cell(r, len(kolumny) - 1))
                self.komorka(scal, nazwa, 8.5, True, AKCENT)
                _tlo(scal, TLO_NAGLOWKA)
                r += 1
            for poz in pozycje:
                for i, tekst in enumerate(poz):
                    k = tab.cell(r, i)
                    ostatnia = i == len(kolumny) - 1
                    pogr = ostatnia and isinstance(tekst, tuple)
                    if isinstance(tekst, tuple):
                        tekst = tekst[0]
                    self.komorka(k, tekst, 9, pogr or (ostatnia and len(kolumny) > 2), TEKST if i else RGBColor(0x37, 0x41, 0x51),
                                 WD_ALIGN_PARAGRAPH.RIGHT if ostatnia else None)
                    _ramki_komorki(k, bottom=(4, LINIA))
                r += 1
        self.szerokosci(tab, proporcje)
        for wiersz in (tab.rows[:-1] if len(tab.rows) <= 8 else []):  # mała tabela nie dzieli się między strony
            for k in wiersz.cells:
                for p in k.paragraphs:
                    p.paragraph_format.keep_with_next = True
        return tab

    def ocena(self, ok, tekst):
        """Wiersz z oceną: ✓ zielony, ✗ czerwony, i niebieski (informacyjnie)."""
        symbol, kolor = {True: ("✓", ZIELONY), False: ("✗", CZERWONY), "info": ("i", NIEBIESKI), None: ("–", SZARY)}[ok]
        p = self.akapit(przed=6, po=4)
        p.paragraph_format.left_indent = Cm(0.1)
        _styl_runu(p.add_run(f"{symbol}  "), 10, True, kolor, czcionka="Segoe UI Symbol")
        _styl_runu(p.add_run(tekst), 9.5, ok is False, kolor if ok is False else TEKST)

    # -------------------------------------------------------------- sekcje obliczeń

    def opis(self, tekst, po=6):
        """Akapit z opisem technicznym metody."""
        self.akapit(tekst, 9, przed=2, po=po)

    def konfiguracja(self):
        t, w, s, n = self.t, self.w, self.stan, self.n
        self.opis(t["o_konfig"])
        model_s = s.get("starter_model") or t["wlasny"]
        model_b = s.get("batt_model") or t["wlasny"]
        grupy = [
            (t["g_rozruszniki"], [(t["model"], model_s), (t["ilosc"], f"{w['starter_qty']} {t['szt']}"), (t["nap_ukladu"], f"{n.g(w['system_v'])} VDC"),
                                  (t["prad_znam"], f"{n.g(w['starter_normal'])} A" if w["starter_normal"] else t["brak"]), (t["prad_szczyt"], f"{n.g(w['starter_peak'])} A"),
                                  (t["nap_krec"], f"{n(w['crank_v'])} V"), (t["nap_min"], f"{n(w['min_v'])} V" if w["min_v"] else t["brak"])]),
            (t["g_akumulatory"], [(t["model"], model_b), (t["technologia"], TYPY[self.jezyk].get(w["batt_type"], w["batt_type"])),
                                   (t["nap_akumulatora"], f"{n.g(w['batt_v'])} V / {n.g(w['batt_ah'])} Ah / {n.g(w['batt_cca'])} A" + (f" ({w['batt_cca_norma']})" if w["batt_cca_norma"] else "")),
                                   (t["polaczenie"], t["polaczenie_w"].format(s=w["batt_series"], p=w["batt_parallel"], n=w["batt_series"] * w["batt_parallel"])),
                                   (t["zestaw"], (f"{n.g(w['napiecie_banku'])} V / {n.g(w['total_ah_available'])} Ah / {n.g(w['total_cca_available'])} A",))]),
            (t["g_kable"], [(t["dlugosc"], f"{n.g(w['cable_l'])} m"), (t["przekroj"], t["przekroj_w"].format(n=w["cable_cores"], a=n.g(w["cable_a"])))]),
            (t["g_profil"], [(t["proba"], f"{n.g(w['time_s'])} s"), (t["proby"], str(w["attempts"])), (t["ladowanie"], f"{n.g(w['charge_h'])} h")]),
        ]
        if w["zestawy"] > 1:
            grupy.append((t["g_redund"], [(t["r_zestawy"], t["r_zestawy_w"].format(k=w["zestawy"])),
                                          (t["r_zmiana"], t["r_zmiana_w"].format(n=w["zmiana_co"]) if w["zmiana_co"] else t["r_zmiana_brak"])]))
        self.tabela_wartosci(grupy, [t["parametr"], t["wartosc"]], [1.25, 1])

    def spadek(self):
        t, w, n = self.t, self.w, self.n
        self.opis(t["o_spadek"])
        r = w["res"]
        wiersze = [(t["rezystancja"], f"R = ρ·L / (n·A) = 1,68·10⁻⁸ × {n.g(w['cable_l'])} / ({w['cable_cores']} × {n.g(w['cable_a'])}·10⁻⁶)".replace("1,68", n(1.68)),
                    f"{n(r * 1000, 3)} mΩ")]
        if w["metoda"] == "karta":
            zest, obw, mm = w["r_zestawu"] * 1000, w["r_obw"] * 1000, lambda v: n(v, 3)
            wiersze += [
                (t["r_zestawu"], f"{w['batt_series']} × {n.g(w['batt_rint_mohm'])} mΩ / {w['batt_parallel']}", f"{mm(zest)} mΩ"),
                (t["r_obw"], (t["r_obw_obl"] if w["starter_qty"] > 1 else t["r_obw_obl1"]).format(q=w["starter_qty"], z=mm(zest), k=mm(r * 1000)), (f"{mm(obw)} mΩ",)),
                (t["r_test"], "", f"{n.g(w['r_test_mohm'])} mΩ"),
                (t["u0"], f"U0 = {n(w['crank_v'])} + {n.g(w['starter_normal'])} × {n(w['r_test'], 4)}", f"{n(w['u0'])} V"),
                (t["u_znam"], f"U = {n(w['u0'])} − {n.g(w['starter_normal'])} × {n(w['r_obw'], 5)}", f"{n(w['sustained_normal'])} V"),
                (t["u_szczyt"], f"U = {n(w['u0'])} − {n.g(w['starter_peak'])} × {n(w['r_obw'], 5)}", (f"{n(w['sustained_voltage'])} V",)),
            ]
            self.tabela_wartosci([(None, wiersze)], [t["wielkosc"], t["obliczenie"], t["wynik"]], [2.05, 2.0, 0.8])
            if w["napiecie_ok"] is None:
                self.ocena(None, t["u_min_brak"])
            else:
                zapas = abs(w["sustained_voltage"] - w["min_v"])
                self.ocena(w["napiecie_ok"], (t["u_min_ok_k"] if w["napiecie_ok"] else t["u_min_zle_k"]).format(
                    r=n(obw, 2), t=n.g(w["r_test_mohm"]), z=n(zapas), m=n(w["min_v"])))
            self.wykres()
            if w["prad_graniczny"] is not None:
                self.akapit(t["graniczny"].format(i=n.g(round(w["prad_graniczny"]))) if w["prad_graniczny"] else t["graniczny_0"], 8.5, kolor=SZARY, po=2)
            self.akapit(t["o_spadek_uwagi"], 8.5, kolor=SZARY, przed=4, po=2)
            return
        if w["starter_normal"]:
            wiersze.append((t["spadek_znam"], f"ΔU = I·R = {n.g(w['starter_normal'])} × {n(r, 6)}", f"{n(w['v_drop_normal'])} V"))
        wiersze.append((t["spadek_szczyt"], f"ΔU = I·R = {n.g(w['starter_peak'])} × {n(r, 6)}", f"{n(w['v_drop'])} V"))
        if w["starter_normal"]:
            wiersze.append((t["u_znam"], f"U = {n(w['crank_v'])} − {n(w['v_drop_normal'])}", f"{n(w['sustained_normal'])} V"))
        wiersze.append((t["u_szczyt"], f"U = {n(w['crank_v'])} − {n(w['v_drop'])}", (f"{n(w['sustained_voltage'])} V",)))
        self.tabela_wartosci([(None, wiersze)], [t["wielkosc"], t["obliczenie"], t["wynik"]], [2.05, 2.0, 0.8])
        if w["napiecie_ok"] is None:
            self.ocena(None, t["u_min_brak"])
        else:
            zapas = abs(w["sustained_voltage"] - w["min_v"])
            self.ocena(w["napiecie_ok"], (t["u_min_ok"] if w["napiecie_ok"] else t["u_min_zle"]).format(z=n(zapas), m=n(w["min_v"])))
        self.akapit(t["metoda_upr"], 8.5, kolor=SZARY, przed=2, po=2)
        self.wykres()
        if w["prad_graniczny"] is not None:
            self.akapit(t["graniczny"].format(i=n.g(round(w["prad_graniczny"]))) if w["prad_graniczny"] else t["graniczny_0"], 8.5, kolor=SZARY, po=2)
        self.akapit(t["o_spadek_uwagi"], 8.5, kolor=SZARY, przed=4, po=2)

    def wykres(self):
        sciezka = rysuj_wykres(self.w, self.t, self.n)
        try:
            p = self.akapit(przed=6, po=2, wyrownanie=WD_ALIGN_PARAGRAPH.CENTER)
            p.paragraph_format.keep_with_next = True
            p.add_run().add_picture(sciezka, width=Emu(int(self.szer * 0.92)))
        finally:
            os.remove(sciezka)
        self.nr_rys += 1
        self.akapit(self.t["wykres"].format(n=self.nr_rys), 8, kolor=SZARY, po=4, wyrownanie=WD_ALIGN_PARAGRAPH.CENTER, kursywa=True)

    def rysunek_zestawu(self):
        t, w, n = self.t, self.w, self.n
        sciezka = rysuj_zestaw(w, t)
        try:
            p = self.akapit(przed=4, po=2, wyrownanie=WD_ALIGN_PARAGRAPH.CENTER)
            p.paragraph_format.keep_with_next = True
            p.add_run().add_picture(sciezka, width=Emu(int(self.szer * (0.95 if w["zestawy"] > 1 else 0.62))))
        finally:
            os.remove(sciezka)
        self.nr_rys += 1
        opis = t["rys_bank2" if w["zestawy"] > 1 else "rys_bank"].format(n=self.nr_rys, k=w["zestawy"], s=w["batt_series"], p=w["batt_parallel"],
                                                                         u=n.g(w["napiecie_banku"]), ah=n.g(w["total_ah_available"]), cca=n.g(w["total_cca_available"]))
        self.akapit(opis, 8, kolor=SZARY, po=8, wyrownanie=WD_ALIGN_PARAGRAPH.CENTER, kursywa=True)

    def akumulatory(self):
        t, w, n = self.t, self.w, self.n
        self.opis(t["o_cca"])
        self.rysunek_zestawu()
        norma = lambda k: f" ({w[k]})" if w[k] else ""
        cca = [(t["cca_dost"], f"{w['batt_parallel']} × {n.g(w['batt_cca'])} A{norma('batt_cca_norma')}", (f"{n.g(w['total_cca_available'])} A",))]
        if w["cca_znane"]:
            cca.append((t["cca_silnik"], t["cca_silnik_obl"].format(e=self.stan.get("engine", "")).strip() + norma("cca_silnika_norma"), (f"{n.g(w['cca_silnika'])} A",)))
        cca.append((t["cca_wym"], f"{w['starter_qty']} × {n.g(w['starter_peak'])} A", f"{n.g(w['cca_wymagane'])} A"))
        self.tabela_wartosci([(None, cca)], [t["wielkosc"], t["obliczenie"], t["wynik"]], [2.05, 2.0, 0.8])
        if w["cca_znane"]:
            zapas = abs(w["total_cca_available"] - w["cca_silnika"])
            if w["cca_stan"] == "tolerancja":
                self.ocena("info", t["cca_silnik_tol"].format(c=n.g(w["cca_silnika"]), z=n.g(zapas), p=n(w["cca_niedobor_proc"], 1), t=n.g(w["cca_tolerancja"])))
            else:
                self.ocena(w["cca_ok"], (t["cca_silnik_ok"] if w["cca_ok"] else t["cca_silnik_zle"]).format(c=n.g(w["cca_silnika"]), z=n.g(zapas)))
            if w["cca_normy_rozne"]:
                self.ocena("info", t["cca_normy"].format(a=w["batt_cca_norma"], s=w["cca_silnika_norma"]))
            self.akapit(t["cca_szczyt_info"].format(s=n.g(w["cca_wymagane"])), 8.5, kolor=SZARY, po=4)
        else:
            self.ocena(True if w["cca_ok"] else "info", t["cca_ok"] if w["cca_ok"] else t["cca_info"])
        poj = [(t["prad_rozr"], f"{w['starter_qty']} × {n.g(w['starter_peak'])} A", f"{n.g(w['prad_rozruchu'])} A"),
               (t["czas_rozr"], f"{w['attempts']} × {n.g(w['time_s'])} s", f"{n.g(w['czas_calkowity'])} s"),
               (t["zuzycie"], f"{n.g(w['prad_rozruchu'])} A × {n.g(w['czas_calkowity'])} s / 3600", (f"{n(w['consumed_ah'])} Ah",)),
               (t["pojemnosc"], f"{w['batt_parallel']} × {n.g(w['batt_ah'])} Ah", f"{n.g(w['total_ah_available'])} Ah"),
               (t["udzial"], f"{n(w['consumed_ah'])} / {n.g(w['total_ah_available'])}", (f"{n(w['zuzycie_proc'], 1)} %",))]
        self.opis(t["o_pojemnosc"], 4)
        self.tabela_wartosci([(None, poj)], [t["wielkosc"], t["obliczenie"], t["wynik"]], [2.05, 2.0, 0.8])
        self.ocena(w["pojemnosc_ok"], t["krotnosc"].format(k=n(w["krotnosc"], 1)) if w["pojemnosc_ok"] else t["poj_zle"])

    def ladowarka(self):
        t, w, n = self.t, self.w, self.n
        self.opis(t["o_ladowarka"])
        lad = t["zakres"].format(a=w["ladowarka_od"], b=w["ladowarka_do"]) if w["ladowarka_do"] else t["okolo"].format(a=w["ladowarka_od"])
        wiersze = [(t["zuzycie"], f"{n.g(w['prad_rozruchu'])} A × {n.g(w['czas_calkowity'])} s / 3600", f"{n(w['consumed_ah'])} Ah"),
                   (t["wsp"].format(t=TYPY[self.jezyk].get(w["batt_type"], w["batt_type"])), "", n.g(w["inefficiency"])),
                   (t["prad_lad"], f"I = {n(w['consumed_ah'])} Ah × {n.g(w['inefficiency'])} / {n.g(w['charge_h'])} h", f"{n(w['charger_amps'])} A"),
                   (t["zal_lad"], t["lad_opis"], (lad,))]
        self.tabela_wartosci([(None, wiersze)], [t["wielkosc"], t["obliczenie"], t["wynik"]], [2.05, 2.0, 0.8])
        self.akapit(t["o_ladowarka_uwagi"], 8.5, kolor=SZARY, przed=6, po=2)

    def redundancja(self):
        t, w = self.t, self.w
        lad = t["zakres"].format(a=w["ladowarka_od"], b=w["ladowarka_do"]) if w["ladowarka_do"] else t["okolo"].format(a=w["ladowarka_od"])
        wiersze = [(t["r_zestawy"], t["r_zestawy_w"].format(k=w["zestawy"])),
                   (t["r_akum"], f"{w['akumulatory_zestaw']} {t['szt']}"),
                   (t["r_akum_razem"], (f"{w['zestawy']} × {w['akumulatory_zestaw']} = {w['akumulatory_razem']} {t['szt']}",)),
                   (t["r_lad"], (f"{w['zestawy']} × {lad}",)),
                   (t["r_zmiana"], t["r_zmiana_w"].format(n=w["zmiana_co"]) if w["zmiana_co"] else t["r_zmiana_brak"])]
        self.tabela_wartosci([(None, wiersze)], [t["parametr"], t["wartosc"]], [1.25, 1])
        self.akapit(t["r_opis"].format(k=w["zestawy"]) + (t["r_opis_zmiana"].format(n=w["zmiana_co"]) if w["zmiana_co"] else ""), 9, przed=6, po=4)

    def uwagi(self):
        t, w = self.t, self.w
        self.akapit(t["u_s_desc"], 9, po=6)
        self.akapit(t["u_zmienne"], 9, po=2)
        for punkt in t["u_lista"]:
            p = self.akapit(f"•  {punkt.format(v=self.n.g(w['system_v']))}", 9, po=1)
            p.paragraph_format.left_indent = Cm(0.4)
        self.akapit(t["u_stan"], 9, przed=4, po=6)
        self.akapit(t["u_polaczenia"], 9, po=4)

    def zalaczniki(self):
        nr = 0
        for klucz in ("curve", "batt", "diagram", "charger"):
            sciezka = self.obrazy.get(klucz)
            if not sciezka:
                continue
            nr += 1
            nazwa = self.t["zal_nazwy"][klucz]
            if klucz == "curve" and self.stan.get("starter_model"):
                nazwa += f": {self.stan['starter_model']}"
            if klucz == "batt" and self.stan.get("batt_model"):
                nazwa += f": {self.stan['batt_model']}"
            self.sekcja(f"{self.t['zal']} {nr}", nazwa, nowa_strona=True)
            p = self.akapit(przed=6, wyrownanie=WD_ALIGN_PARAGRAPH.CENTER)
            p.add_run().add_picture(sciezka, width=self.szer)

    def zbuduj(self):
        t = self.t
        self.naglowek()
        self.kafelki()
        self.rewizje()
        self.sekcja(1, t["s1"])
        self.konfiguracja()
        self.sekcja(2, t["s2"])
        self.spadek()
        self.sekcja(3, t["s3"])
        self.akumulatory()
        self.sekcja(4, t["s4"])
        self.ladowarka()
        nr = 5
        if self.w["zestawy"] > 1:
            self.sekcja(nr, t["s_redund"])
            self.redundancja()
            nr += 1
        self.sekcja(nr, t["s5"])
        self.uwagi()
        self.zalaczniki()
        return self.doc


# ------------------------------------------------------------------ wykres napięcia (obraz PNG do raportu)

def rysuj_wykres(w, t, n):
    """U(I) = U kręcenia − I·R od 0 do 120% prądu szczytowego, linia napięcia minimalnego, punkty prądów. Zwraca ścieżkę PNG."""
    from PIL import Image, ImageDraw, ImageFont
    skala = 3
    szer, wys = 900 * skala, 330 * skala
    l, p, g, d = 70 * skala, 20 * skala, 20 * skala, 52 * skala
    obraz = Image.new("RGB", (szer, wys), "white")
    rys = ImageDraw.Draw(obraz)
    katalog = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")

    def czcionka(rozmiar, pogrubiona=False):
        try:
            return ImageFont.truetype(os.path.join(katalog, "segoeuib.ttf" if pogrubiona else "segoeui.ttf"), rozmiar * skala)
        except OSError:
            return ImageFont.load_default()
    f_os, f_et = czcionka(13), czcionka(13, True)

    krzywa = w["krzywa"]
    i_max = krzywa[-1]["i"] or 1
    u_dol = max(0, int(min(w["min_v"] or 1e9, krzywa[-1]["u"]) - 1))
    u_gora = int(max(w["u0"], w["min_v"] or 0) + 1.5)
    karta = w.get("krzywa_karty")
    if karta:
        u_dol = max(0, int(min(u_dol, karta[-1]["u"] - 1)))
    x = lambda i: l + i / i_max * (szer - l - p)
    y = lambda u: g + (1 - (u - u_dol) / ((u_gora - u_dol) or 1)) * (wys - g - d)

    krok_u = 4 if u_gora - u_dol > 10 else 2 if u_gora - u_dol > 5 else 1
    u = (u_dol // krok_u) * krok_u
    while u <= u_gora:
        if u >= u_dol:
            rys.line([(l, y(u)), (szer - p, y(u))], fill="#E5E7EB", width=skala)
            rys.text((l - 10 * skala, y(u)), f"{u} V", fill="#6B7280", font=f_os, anchor="rm")
        u += krok_u
    krok_i = 1000 if i_max > 2500 else 500 if i_max > 1000 else 200
    i = 0
    while i <= i_max:
        rys.line([(x(i), wys - d), (x(i), wys - d + 6 * skala)], fill="#9CA3AF", width=skala)
        rys.text((x(i), wys - d + 10 * skala), n.g(i), fill="#6B7280", font=f_os, anchor="mt")
        i += krok_i
    rys.text(((l + szer - p) / 2, wys - 4 * skala), t["os_prad"], fill="#374151", font=f_os, anchor="mb")
    rys.line([(l, wys - d), (szer - p, wys - d)], fill="#6B7280", width=2 * skala)

    punkty = [(x(k["i"]), y(k["u"])) for k in krzywa]
    rys.polygon(punkty + [(x(i_max), wys - d), (x(0), wys - d)], fill="#FDF3E1")
    if karta:  # krzywa karty (obwód testowy) - przerywana szara
        for a_, b_ in zip(karta[:-1], karta[1:]):
            x0_, y0_, x1_, y1_ = x(a_["i"]), y(a_["u"]), x(b_["i"]), y(b_["u"])
            for k_ in range(0, 10, 2):
                rys.line([(x0_ + (x1_ - x0_) * k_ / 10, y0_ + (y1_ - y0_) * k_ / 10), (x0_ + (x1_ - x0_) * (k_ + 1) / 10, y0_ + (y1_ - y0_) * (k_ + 1) / 10)], fill="#9CA3AF", width=2 * skala)
        # legenda w prawym górnym rogu (linie schodzą w dół w prawo - tam jest wolne miejsce)
        lx, ly = szer - p - 330 * skala, g + 8 * skala
        rys.line([(lx, ly), (lx + 34 * skala, ly)], fill="#B45309", width=4 * skala)
        rys.text((lx + 44 * skala, ly), t["l_obw"].format(r=n(w["r_obw"] * 1000, 2)), fill="#B45309", font=f_et, anchor="lm")
        for k_ in range(0, 34, 8):
            rys.line([(lx + k_ * skala, ly + 22 * skala), (lx + (k_ + 4) * skala, ly + 22 * skala)], fill="#9CA3AF", width=2 * skala)
        rys.text((lx + 44 * skala, ly + 22 * skala), t["l_karta"].format(t=n.g(w["r_test_mohm"])), fill="#6B7280", font=f_os, anchor="lm")
    rys.line(punkty, fill="#B45309", width=4 * skala, joint="curve")
    if w["min_v"]:
        ym = y(w["min_v"])
        for xs in range(int(l), int(szer - p), 18 * skala):
            rys.line([(xs, ym), (min(xs + 10 * skala, szer - p), ym)], fill="#B91C1C", width=2 * skala)
        rys.text((szer - p, ym - 6 * skala), f"{t['l_min']} {n(w['min_v'], 1)} V", fill="#B91C1C", font=f_et, anchor="rb")

    def punkt(prad, kolor, opis):
        px, py = x(prad), y(w["u0"] - prad * w["r_obw"])
        r = 8 * skala
        rys.ellipse([px - r, py - r, px + r, py + r], fill=kolor, outline="white", width=3 * skala)
        rys.text((px, py - 14 * skala), f"{opis} {n.g(prad)} A · {n(w['u0'] - prad * w['r_obw'])} V", fill=kolor, font=f_et, anchor="mb")
    if w["starter_normal"]:
        punkt(w["starter_normal"], "#1D4ED8", t["l_znam"])
    punkt(w["starter_peak"], "#B45309", t["l_szczyt"])

    plik = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    plik.close()
    obraz.save(plik.name)
    return plik.name


# ------------------------------------------------------------------ schemat zestawu akumulatorów (obraz PNG do raportu)

def rysuj_zestaw(w, t):
    """Zestaw (zestawy) akumulatorów: łańcuchy szeregowe połączone równolegle między szynami + i −. Zwraca ścieżkę PNG."""
    from PIL import Image, ImageDraw, ImageFont
    skala = 3
    s, p, k = w["batt_series"], w["batt_parallel"], min(w["zestawy"], 3)
    ws, wp = min(s, 6), min(p, 6)  # więcej akumulatorów: "+N"
    bw, bh, odst_x, odst_y = 74 * skala, 40 * skala, 22 * skala, 16 * skala
    szer_zestawu = 55 * skala + ws * bw + (ws - 1) * odst_x + (48 if s > ws else 30) * skala + 18 * skala
    wys_zestawu = wp * bh + (wp - 1) * odst_y
    gora = (30 if k > 1 else 12) * skala
    przerwa = 60 * skala
    szer = k * szer_zestawu + (k - 1) * przerwa + 20 * skala
    wys = gora + wys_zestawu + (36 + (40 if k > 1 else 0) + (18 if p > wp else 0)) * skala
    obraz = Image.new("RGB", (szer, wys), "white")
    rys = ImageDraw.Draw(obraz)
    katalog = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")

    def czcionka(rozmiar, pogrubiona=False):
        try:
            return ImageFont.truetype(os.path.join(katalog, "segoeuib.ttf" if pogrubiona else "segoeui.ttf"), rozmiar * skala)
        except OSError:
            return ImageFont.load_default()
    f_b, f_m, f_t = czcionka(10, True), czcionka(9), czcionka(12, True)
    akcent, ciemny, szary, tlo, plus = "#B45309", "#111827", "#6B7280", "#FDF3E1", "#B91C1C"
    liczba = lambda x: f"{x:g}"

    dolne = []
    for z in range(k):
        x0 = 10 * skala + z * (szer_zestawu + przerwa)
        if k > 1:
            rys.text((x0 + szer_zestawu / 2, 2 * skala), t["zestaw_x"].format(x="ABC"[z]), fill=ciemny, font=f_t, anchor="mt")
        xl, xp = x0 + 18 * skala, x0 + szer_zestawu - 18 * skala  # szyny: + po lewej, − po prawej
        yg, yd = gora, gora + wys_zestawu
        rys.line([(xl, yg - 6 * skala), (xl, yd + 6 * skala)], fill=plus, width=4 * skala)
        rys.line([(xp, yg - 6 * skala), (xp, yd + 6 * skala)], fill=ciemny, width=4 * skala)
        rys.text((xl, yd + 9 * skala), "+", fill=plus, font=f_t, anchor="mt")
        rys.text((xp, yd + 9 * skala), "−", fill=ciemny, font=f_t, anchor="mt")
        for j in range(wp):
            yb = yg + j * (bh + odst_y)
            ys = yb + bh / 2
            xb0 = x0 + 55 * skala
            rys.line([(xl, ys), (xb0, ys)], fill=szary, width=2 * skala)
            for i in range(ws):
                xb = xb0 + i * (bw + odst_x)
                rys.rounded_rectangle([xb, yb, xb + bw, yb + bh], radius=6 * skala, fill=tlo, outline=akcent, width=2 * skala)
                rys.rectangle([xb + bw, ys - 6 * skala, xb + bw + 4 * skala, ys + 6 * skala], fill=akcent)
                rys.text((xb + bw / 2, yb + 14 * skala), f"{liczba(w['batt_v'])} V", fill=ciemny, font=f_b, anchor="mm")
                rys.text((xb + bw / 2, yb + 28 * skala), f"{liczba(w['batt_ah'])} Ah", fill=szary, font=f_m, anchor="mm")
                if i < ws - 1:
                    rys.line([(xb + bw + 4 * skala, ys), (xb + bw + odst_x, ys)], fill=szary, width=2 * skala)
            xk = xb0 + ws * bw + (ws - 1) * odst_x + 4 * skala
            if s > ws:
                rys.text((xk + 6 * skala, ys), f"+{s - ws}", fill=szary, font=f_b, anchor="lm")
                xk += 30 * skala
            rys.line([(xk, ys), (xp, ys)], fill=szary, width=2 * skala)
        y_dol = yd + 30 * skala
        if p > wp:
            rys.text((x0 + szer_zestawu / 2, yd + 12 * skala), f"+{p - wp}", fill=szary, font=f_b, anchor="mt")
            y_dol += 18 * skala
        dolne.append((x0 + szer_zestawu / 2, y_dol))
    if k > 1:  # przełączanie zestawów przekaźnikami / stycznikami
        yb = wys - 22 * skala
        for xs, ys in dolne:
            rys.line([(xs, ys), (xs, yb)], fill=akcent, width=2 * skala)
        rys.line([(dolne[0][0], yb), (dolne[-1][0], yb)], fill=akcent, width=2 * skala)
        rys.text((szer / 2, yb + 4 * skala), f"{t['przelacznik']} → {t['do_rozrusznikow']}", fill=akcent, font=f_b, anchor="mt")

    plik = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    plik.close()
    obraz.save(plik.name)
    return plik.name


# ------------------------------------------------------------------ zapis

def generuj(sciezka, stan, w, obrazy, szablon=""):
    """
    stan: pola projektu (teksty, rewizje, modele), w: wynik obliczenia.oblicz,
    obrazy: {'curve'|'batt'|'diagram'|'charger': pełna ścieżka pliku albo ''}, szablon: .docx z nagłówkiem / stopką.
    """
    Raport(stan, w, obrazy, szablon).zbuduj().save(sciezka)
    return sciezka


def zapisz_pdf(docx, pdf):
    """PDF z dokumentu Word przez Microsoft Word (ta sama stopka i wygląd co w DOCX). RuntimeError, gdy Worda nie ma."""
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    word = None
    try:
        try:
            word = win32com.client.DispatchEx("Word.Application")
        except Exception as e:
            raise RuntimeError("Zapis do PDF wymaga programu Microsoft Word na tym komputerze.") from e
        word.Visible = False
        word.DisplayAlerts = 0
        dokument = word.Documents.Open(os.path.abspath(docx), ReadOnly=True, AddToRecentFiles=False)
        try:
            dokument.ExportAsFixedFormat(os.path.abspath(pdf), 17)  # 17 = PDF
        finally:
            dokument.Close(False)
    finally:
        if word is not None:
            word.Quit()
        pythoncom.CoUninitialize()
    return pdf


def istniejace(obrazy):
    """Tylko obrazy, których pliki istnieją (brakujące pomijane)."""
    return {k: v for k, v in obrazy.items() if v and os.path.isfile(v)}
