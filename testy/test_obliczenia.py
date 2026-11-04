"""
Test obliczeń: wyniki muszą być takie same jak w wersji 1.2.0 (wzory poniżej, przepisane z modele.py / kontrolery.py),
gdy dane są takie same jak wtedy (układ 24 V, napięcie kręcenia 16 V). Do tego wczytanie projektu zapisanego wersją 1.x.

    python testy/test_obliczenia.py
"""
import itertools
import json
import os
import sys
import tempfile

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(TU))
os.environ["APPDATA"] = tempfile.mkdtemp()  # baza i ustawienia testu poza folderem użytkownika

import obliczenia  # noqa: E402
from interfejs import Api  # noqa: E402


def wzorzec_120(peak, qty, ah, cca, series, parallel, length, area, cores, time_s, attempts, charge_h, typ):
    """Obliczenia wersji 1.2.0 (kontrolery.MainController._get_ui_data)."""
    res = 1.68e-8 * (length / (area * 1e-6 * cores)) if area and cores else 0
    v_drop = peak * res
    consumed = peak * qty * time_s * attempts / 3600
    ineff = 1.4 if typ == "Lead-Acid" else 1.2
    return {"res": res, "v_drop": v_drop, "sustained_voltage": 16.0 - v_drop, "total_cca_available": cca * parallel,
            "total_ah_available": ah * parallel, "consumed_ah": consumed, "inefficiency": ineff,
            "charger_amps": consumed * ineff / charge_h if charge_h > 0 else 0, "pojemnosc_ok": consumed < ah * parallel}


def test_zgodnosc_z_120():
    n = 0
    for peak, qty, (ah, cca), (series, parallel), (length, area, cores), (time_s, attempts), charge_h, typ in itertools.product(
            (1400, 1600, 2720), (1, 3), ((75, 975), (225, 1150)), ((2, 4), (2, 1)), ((12.5, 95, 2), (30, 50, 1)),
            ((10, 5), (15, 3)), (3, 8), ("Lead-Acid", "AGM", "Li-Ion")):
        stan = dict(system_v="24", crank_v="16", min_v="", starter_normal="", starter_peak=str(peak), starter_qty=str(qty),
                    batt_v="12", batt_ah=str(ah), batt_cca=str(cca), batt_series=str(series), batt_parallel=str(parallel),
                    cable_l=str(length), cable_a=str(area), cable_cores=str(cores), time_s=str(time_s), attempts=str(attempts),
                    charge_h=str(charge_h), batt_type=typ)
        w = obliczenia.oblicz(stan)
        assert w["ok"], w
        for k, v in wzorzec_120(peak, qty, ah, cca, series, parallel, length, area, cores, time_s, attempts, charge_h, typ).items():
            assert abs(w[k] - v) < 1e-9 if isinstance(v, float) else w[k] == v, (k, w[k], v, stan)
        n += 1
    return n


def test_nowe_funkcje():
    baza = dict(system_v="12", starter_normal="600", starter_peak="1000", starter_qty="1", crank_v="8", min_v="6", batt_v="12",
                batt_ah="100", batt_cca="800", batt_series="1", batt_parallel="2", cable_l="4", cable_a="50", cable_cores="1",
                time_s="10", attempts="3", charge_h="5", batt_type="AGM")
    w = obliczenia.oblicz(baza)
    r = 1.68e-8 * 4 / 50e-6
    assert abs(w["res"] - r) < 1e-12
    assert abs(w["sustained_voltage"] - (8 - 1000 * r)) < 1e-9 and abs(w["sustained_normal"] - (8 - 600 * r)) < 1e-9
    assert w["napiecie_ok"] is True and abs(w["prad_graniczny"] - 2 / r) < 1e-6
    assert w["napiecie_zgodne"] and w["napiecie_banku"] == 12
    assert w["cca_wymagane"] == 1000 and w["cca_ok"] is True
    assert abs(w["zuzycie_proc"] - w["consumed_ah"] / 200 * 100) < 1e-9
    w = obliczenia.oblicz({**baza, "min_v": "7.9"})
    assert w["napiecie_ok"] is False
    w = obliczenia.oblicz({**baza, "min_v": "9"})
    assert w["prad_graniczny"] == 0  # napięcie kręcenia poniżej minimalnego
    w = obliczenia.oblicz({**baza, "batt_series": "2"})
    assert not w["napiecie_zgodne"]
    w = obliczenia.oblicz({**baza, "batt_ah": "", "attempts": "2.5", "cable_a": "0", "starter_peak": "1,5e3"})
    assert not w["ok"] and set(w["bledy"]) == {"batt_ah", "attempts", "cable_a"}, w
    w = obliczenia.oblicz({**baza, "starter_peak": "1000,5"})  # przecinek dziesiętny
    assert w["ok"] and w["starter_peak"] == 1000.5


def test_ladowarka():
    for prad, wynik in ((16, (20, None)), (14, (15, None)), (14.6, (15, 20)), (15, (15, 20)), (20.5, (25, None)), (2, (5, None)), (26.67, (30, None))):
        assert obliczenia.dobor_ladowarki(prad) == wynik, (prad, obliczenia.dobor_ladowarki(prad))


def test_projekt_z_wersji_1x():
    stary = {"project_no": "PRJ-1", "client": "K", "genset": "G", "engine": "E", "author": "MK", "language": "Polski",
             "revisions": [{"rev": "0", "desc": "Initial", "drawn": "MK", "check": "Appr.", "date": "01OCT26"}],
             "starter_model": "Delco Remy 50MT-400", "starter_v": "24", "starter_peak": "1600", "starter_qty": "3",
             "batt_model": "Optima YT S 5.5", "batt_type": "AGM", "batt_ah": "75", "batt_cca": "975", "batt_series": "2",
             "batt_parallel": "4", "cable_l": "12.5", "cable_a": "95", "cable_cores": "2", "time_s": "10", "attempts": "5",
             "charge_h": "3", "images": {"curve": "", "diagram": "", "batt": "", "charger": ""}}
    plik = os.path.join(os.environ["APPDATA"], "stary.json")
    json.dump(stary, open(plik, "w", encoding="utf-8"))
    r = Api().wczytaj_projekt(plik)
    assert r["ok"]
    p = r["projekt"]
    assert p["system_v"] == "24" and p["crank_v"] == "16" and p["language"] == "Polski" and p["revisions"][0]["date"] == "01OCT26"
    w = obliczenia.oblicz(p)
    wz = wzorzec_120(1600, 3, 75, 975, 2, 4, 12.5, 95, 2, 10, 5, 3, "AGM")
    assert all(abs(w[k] - v) < 1e-9 for k, v in wz.items() if isinstance(v, float)), "projekt 1.x liczy się inaczej niż w 1.2.0"


def test_redundancja():
    """Zestawy są przełączane, nigdy łączone: wyniki rozruchu i ładowarki takie same jak dla jednego zestawu."""
    stan = dict(system_v="24", crank_v="16", min_v="11", starter_normal="1000", starter_peak="1600", starter_qty="3", batt_v="12",
                batt_ah="225", batt_cca="1150", batt_series="2", batt_parallel="4", cable_l="12.5", cable_a="95", cable_cores="2",
                time_s="10", attempts="5", charge_h="3", batt_type="Lead-Acid")
    jeden, dwa = obliczenia.oblicz(stan), obliczenia.oblicz({**stan, "zestawy": "2", "zmiana_co": "5"})
    for k in ("total_cca_available", "total_ah_available", "consumed_ah", "zuzycie_proc", "charger_amps", "ladowarka_od", "sustained_voltage"):
        assert jeden[k] == dwa[k], k
    assert jeden["zestawy"] == 1 and dwa["akumulatory_razem"] == 16 and dwa["ladowarki_razem"] == 2 and dwa["zmiana_co"] == 5


def test_baza():
    """Migracja starej wspólnej bazy (wpisy własne wydzielone), pełna aktualizacja bazy globalnej, wpisy własne nietknięte."""
    import baza as modul
    katalog = modul.KATALOG_BAZY
    wbud = {r: modul._wbudowana(r) for r in modul.PLIKI}
    stara = {r: dict(v) for r, v in wbud.items()}
    pierwszy = next(iter(stara["starters"]))
    stara["starters"][pierwszy] = {**stara["starters"][pierwszy], "min_voltage_v": 99}  # zmieniony przez użytkownika
    stara["batteries"]["Mój akumulator"] = {"type": "AGM", "capacity_ah": 50}           # własny
    os.makedirs(katalog, exist_ok=True)
    if os.path.exists(modul.PLIK_WLASNYCH):
        os.remove(modul.PLIK_WLASNYCH)  # stan sprzed tej wersji: tylko wspólna baza
    for r, p in modul.PLIKI.items():
        json.dump({"version": "1.1.0", r: stara[r]}, open(os.path.join(katalog, p), "w", encoding="utf-8"))
    b = modul.Baza()
    assert b.zrodla("starters")[pierwszy] == "zmieniona" and b.zrodla("batteries")["Mój akumulator"] == "wlasna"
    assert b.urzadzenia("starters")[pierwszy]["min_voltage_v"] == 99
    assert sum(1 for z in b.zrodla("starters").values() if z != "globalna") == 1
    # serwer: jedno urządzenie usunięte, jedno nowe
    nowe = {r: dict(v) for r, v in wbud.items()}
    usuniety = list(nowe["starters"])[-1]
    del nowe["starters"][usuniety]
    nowe["starters"]["Nowy rozrusznik"] = {"voltage_v": 24, "peak_current_a": 1000}
    zmiany = b.zastap_globalna(nowe, "9.9.9")
    assert zmiany["starters"]["nowe"] == ["Nowy rozrusznik"] and zmiany["starters"]["usuniete"] == [usuniety]
    b2 = modul.Baza()  # po ponownym uruchomieniu
    assert b2.wersja == "9.9.9" and usuniety not in b2.urzadzenia("starters") and "Nowy rozrusznik" in b2.urzadzenia("starters")
    assert b2.urzadzenia("starters")[pierwszy]["min_voltage_v"] == 99 and "Mój akumulator" in b2.urzadzenia("batteries")
    b2.usun_urzadzenie("starters", pierwszy)  # przywrócenie wersji z bazy globalnej
    assert b2.zrodla("starters")[pierwszy] == "globalna" and b2.urzadzenia("starters")[pierwszy] == wbud["starters"][pierwszy]


def test_cca_silnika():
    """CCA z karty katalogowej silnika: gdy zaznaczone - wartość obowiązkowa i prawdziwe kryterium; bez niego informacyjnie."""
    b = dict(system_v="24", crank_v="16", starter_peak="1600", starter_qty="3", batt_v="12", batt_ah="225", batt_cca="1150", batt_series="2",
             batt_parallel="4", cable_l="12.5", cable_a="95", cable_cores="2", time_s="10", attempts="5", charge_h="3")
    w = obliczenia.oblicz(b)
    assert w["ok"] and not w["cca_znane"] and not w["cca_ok"]  # 4600 A < 3 x 1600 A - tylko informacyjnie
    w = obliczenia.oblicz({**b, "cca_znane": "1"})
    assert not w["ok"] and "cca_silnika" in w["bledy"]
    w = obliczenia.oblicz({**b, "cca_znane": "1", "cca_silnika": "2000"})
    assert w["ok"] and w["cca_znane"] and w["cca_ok"] and not w["szczyt_pokryty"]
    w = obliczenia.oblicz({**b, "cca_znane": "1", "cca_silnika": "5000"})
    assert w["ok"] and not w["cca_ok"]
    # tolerancja (domyślnie 10 %): 4600 A przy wymaganiu 4700 A (-2,1 %) - w tolerancji; przy 5200 A (-11,5 %) - za mało
    w = obliczenia.oblicz({**b, "cca_znane": "1", "cca_silnika": "4700"})
    assert w["cca_stan"] == "tolerancja" and not w["cca_ok"] and abs(w["cca_niedobor_proc"] - 100 / 47) < 1e-9
    w = obliczenia.oblicz({**b, "cca_znane": "1", "cca_silnika": "5200"})
    assert w["cca_stan"] == "zle"
    w = obliczenia.oblicz({**b, "cca_znane": "1", "cca_silnika": "5200", "cca_tolerancja": 15})
    assert w["cca_stan"] == "tolerancja"
    w = obliczenia.oblicz({**b, "cca_znane": "1", "cca_silnika": "2000"})
    assert w["cca_stan"] == "ok"
    w = obliczenia.oblicz({**b, "cca_silnika": "5000"})  # wartość wpisana, ale pole wyboru odznaczone - nie liczy się
    assert w["ok"] and not w["cca_znane"]


if __name__ == "__main__":
    n = test_zgodnosc_z_120()
    test_nowe_funkcje()
    test_ladowarka()
    test_redundancja()
    test_projekt_z_wersji_1x()
    test_baza()
    test_cca_silnika()
    print(f"OK - {n} zestawów danych zgodnych z wersją 1.2.0; ładowarka, redundancja, CCA silnika, projekty 1.x i baza sprawdzone")
