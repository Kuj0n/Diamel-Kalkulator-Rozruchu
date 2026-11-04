"""
obliczenia.py

Obliczenia układu rozruchowego agregatu - bez interfejsu, wspólne dla okna programu i raportu DOCX.
Spadek napięcia na kablach, napięcie na rozruszniku w funkcji prądu, CCA, zużycie pojemności, dobór ładowarki.
"""

import math

RHO_CU = 1.68e-8                 # rezystywność miedzi [Ohm*m]
NIEEFEKTYWNOSC = {"Lead-Acid": 1.4}  # pozostałe technologie (AGM, Li-Ion): 1.2
NIEEFEKTYWNOSC_INNE = 1.2
KROK_LADOWARKI_A = 5             # zalecana ładowarka: wyliczony prąd zaokrąglony w górę do pełnych 5 A
CCA_TOLERANCJA_PROC = 10        # niedobór CCA względem karty silnika do 10 % - w tolerancji (nie dyskwalifikuje)
ZAPAS_MIN_A = 1                  # gdy do pełnych 5 A brakuje mniej - zakres (np. 14,6 A -> 15-20 A)


def dobor_ladowarki(prad):
    """Zalecana ładowarka: 16 A -> około 20 A, 14 A -> około 15 A, 14,6 A -> 15-20 A. Zwraca (od, do albo None)."""
    od = max(KROK_LADOWARKI_A, math.ceil(prad / KROK_LADOWARKI_A - 1e-9) * KROK_LADOWARKI_A)
    return (od, od + KROK_LADOWARKI_A) if od - prad < ZAPAS_MIN_A else (od, None)
NAPIECIA_UKLADU = (12, 24)


def napiecie_krecenia_domyslne(napiecie_ukladu):
    """Typowe napięcie na akumulatorach podczas kręcenia: 2/3 napięcia znamionowego (16 V dla 24 V, 8 V dla 12 V)."""
    return round(napiecie_ukladu * 2 / 3, 2)


def rezystancja_kabla(dlugosc_m, przekroj_mm2, zyly_na_biegun):
    """Rezystancja linii kablowej (długość w obie strony) [Ohm]."""
    if przekroj_mm2 <= 0 or zyly_na_biegun <= 0:
        return 0.0
    return RHO_CU * dlugosc_m / (przekroj_mm2 * 1e-6 * zyly_na_biegun)


def liczba(tekst, calkowita=False):
    """Liczba z pola formularza (akceptuje przecinek). ValueError, gdy pole jest puste albo niepoprawne."""
    if isinstance(tekst, (int, float)):
        wartosc = float(tekst)
    else:
        wartosc = float(str(tekst).strip().replace(",", "."))
    if calkowita:
        if wartosc != int(wartosc):
            raise ValueError("liczba całkowita")
        return int(wartosc)
    return wartosc


# pole formularza -> (opis do komunikatu, całkowita, wymagane > 0)
POLA = {
    "system_v": ("Napięcie układu", True, True),
    "starter_normal": ("Prąd znamionowy rozrusznika", False, False),
    "starter_peak": ("Prąd szczytowy rozrusznika", False, True),
    "starter_qty": ("Ilość rozruszników", True, True),
    "crank_v": ("Napięcie kręcenia", False, True),
    "min_v": ("Napięcie minimalne rozrusznika", False, False),
    "batt_v": ("Napięcie akumulatora", False, True),
    "batt_ah": ("Pojemność akumulatora", False, True),
    "batt_cca": ("Prąd CCA akumulatora", False, True),
    "batt_series": ("Ilość szeregowo", True, True),
    "batt_parallel": ("Ilość łańcuchów równoległych", True, True),
    "cable_l": ("Długość kabli", False, True),
    "cable_a": ("Przekrój żyły", False, True),
    "cable_cores": ("Ilość żył na biegun", True, True),
    "time_s": ("Czas próby", False, True),
    "attempts": ("Ilość prób", True, True),
    "charge_h": ("Czas ładowania", False, True),
    "zestawy": ("Liczba zestawów (redundancja)", True, True),
    "zmiana_co": ("Zmiana zestawu co ... rozruchów", True, False),
    "cca_silnika": ("Wymagane CCA wg producenta silnika", False, False),
}
NIEWYMAGANE_PUSTE = {"starter_normal", "min_v", "zmiana_co", "cca_silnika"}  # puste = brak danych (nie liczone / nie sprawdzane)


def oblicz(stan):
    """
    stan: słownik pól projektu (jak w pliku projektu .json). Zwraca {'ok': True, ...wyniki}
    albo {'ok': False, 'bledy': {pole: komunikat}} gdy dane są niepełne.
    """
    d, bledy = {}, {}
    for pole, (opis, calkowita, dodatnie) in POLA.items():
        surowe = stan.get(pole, "1" if pole == "zestawy" else "")  # projekty sprzed redundancji: 1 zestaw
        if pole in NIEWYMAGANE_PUSTE and str(surowe).strip() in ("", "0"):
            d[pole] = 0.0
            continue
        try:
            d[pole] = liczba(surowe, calkowita)
        except (ValueError, TypeError):
            bledy[pole] = f"{opis}: wpisz {'liczbę całkowitą' if calkowita else 'liczbę'}"
            continue
        if dodatnie and d[pole] <= 0:
            bledy[pole] = f"{opis}: musi być większe od zera"
        elif d[pole] < 0:
            bledy[pole] = f"{opis}: nie może być ujemne"
    # Wymagane CCA z karty katalogowej silnika: gdy zaznaczono, że jest znane - wartość obowiązkowa
    cca_znane = str(stan.get("cca_znane", "")).lower() in ("1", "true", "tak")
    try:
        tolerancja = max(0.0, min(50.0, float(stan.get("cca_tolerancja", CCA_TOLERANCJA_PROC))))
    except (TypeError, ValueError):
        tolerancja = CCA_TOLERANCJA_PROC
    if cca_znane and "cca_silnika" not in bledy and d.get("cca_silnika", 0) <= 0:
        bledy["cca_silnika"] = "Wymagane CCA wg producenta silnika: wpisz wartość z karty katalogowej"
    if bledy:
        return {"ok": False, "bledy": bledy}

    typ = stan.get("batt_type") or "Lead-Acid"
    peak, normal, ilosc = d["starter_peak"], d["starter_normal"], d["starter_qty"]
    krecenie, minimalne = d["crank_v"], d["min_v"]

    # Spadek napięcia na kablu (na rozrusznik) - liniowo z prądem: U(I) = U_kręcenia - I * R
    res = rezystancja_kabla(d["cable_l"], d["cable_a"], d["cable_cores"])
    v_drop = peak * res
    v_drop_normal = normal * res
    napiecie_peak = krecenie - v_drop
    napiecie_normal = krecenie - v_drop_normal if normal else None
    # prąd, przy którym napięcie na rozruszniku spada do minimalnego (0 = już napięcie kręcenia jest za niskie)
    prad_graniczny = max(0.0, (krecenie - minimalne) / res) if (minimalne and res > 0) else None
    krzywa = [{"i": round(peak * k / 20, 1), "u": round(krecenie - peak * k / 20 * res, 3)} for k in range(0, 25)]  # do 120% prądu szczytowego

    # Akumulatory: szeregowo sumuje się napięcie, równolegle - prąd i pojemność
    napiecie_banku = d["batt_v"] * d["batt_series"]
    cca_dostepne = d["batt_cca"] * d["batt_parallel"]
    cca_wymagane = peak * ilosc
    ah_dostepne = d["batt_ah"] * d["batt_parallel"]
    prad_rozruchu = peak * ilosc
    czas_calkowity = d["time_s"] * d["attempts"]
    amperosekundy = prad_rozruchu * czas_calkowity
    ah_zuzyte = amperosekundy / 3600
    nieefektywnosc = NIEEFEKTYWNOSC.get(typ, NIEEFEKTYWNOSC_INNE)
    prad_ladowarki = ah_zuzyte * nieefektywnosc / d["charge_h"]
    ladowarka_od, ladowarka_do = dobor_ladowarki(prad_ladowarki)

    return {
        "ok": True,
        **d,
        "batt_type": typ,
        "res": res,
        "v_drop": v_drop,
        "v_drop_normal": v_drop_normal,
        "sustained_voltage": napiecie_peak,
        "sustained_normal": napiecie_normal,
        "napiecie_ok": (napiecie_peak >= minimalne) if minimalne else None,
        "prad_graniczny": prad_graniczny,
        "krzywa": krzywa,
        "napiecie_banku": napiecie_banku,
        "napiecie_zgodne": abs(napiecie_banku - d["system_v"]) < 0.01,
        "total_cca_available": cca_dostepne,
        "cca_wymagane": cca_wymagane,
        # Kryterium CCA: wymaganie producenta silnika (z karty katalogowej) - spełnione albo nie. Bez niego tylko
        # informacyjnie: suma szczytowych prądów rozruszników (prąd chwilowy - nie dyskwalifikuje akumulatorów).
        "cca_znane": cca_znane,
        "cca_ok": cca_dostepne >= (d["cca_silnika"] if cca_znane else cca_wymagane),
        # niedobór względem karty silnika w granicy tolerancji (np. brakuje 50-100 A przy 2000 A) - akceptowalny
        "cca_tolerancja": tolerancja,
        "cca_niedobor_proc": max(0.0, (d["cca_silnika"] - cca_dostepne) / d["cca_silnika"] * 100) if cca_znane else 0.0,
        "cca_stan": ("ok" if cca_dostepne >= d["cca_silnika"] else "tolerancja" if (d["cca_silnika"] - cca_dostepne) <= d["cca_silnika"] * tolerancja / 100 else "zle")
                    if cca_znane else None,
        "szczyt_pokryty": cca_dostepne >= cca_wymagane,
        "total_ah_available": ah_dostepne,
        "prad_rozruchu": prad_rozruchu,
        "czas_calkowity": czas_calkowity,
        "amperosekundy": amperosekundy,
        "consumed_ah": ah_zuzyte,
        "zuzycie_proc": ah_zuzyte / ah_dostepne * 100,
        "pojemnosc_ok": ah_zuzyte < ah_dostepne,  # akumulatory są stale pod ładowarką - kryterium: zużycie poniżej pojemności
        "krotnosc": ah_dostepne / ah_zuzyte if ah_zuzyte > 0 else 0,
        "inefficiency": nieefektywnosc,
        "charger_amps": prad_ladowarki,
        "ladowarka_od": ladowarka_od,
        "ladowarka_do": ladowarka_do,
        # Redundancja: każdy zestaw (akumulatory + ładowarka) sam zapewnia pełny profil rozruchu - powyższe wyniki dotyczą jednego zestawu
        "akumulatory_zestaw": d["batt_series"] * d["batt_parallel"],
        "akumulatory_razem": d["batt_series"] * d["batt_parallel"] * d["zestawy"],
        "ladowarki_razem": d["zestawy"],
    }
