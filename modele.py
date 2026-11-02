import os
import json
import shutil
from konfiguracja_app import sciezka_do_zasobu

class DatabaseModel:
    def __init__(self):
        self.local_data_dir = "data"
        self.starters_file = os.path.join(self.local_data_dir, "starters.json")
        self.batteries_file = os.path.join(self.local_data_dir, "batteries.json")
        self.starters = {}
        self.batteries = {}
        self.ensure_local_db()
        self.load_databases()

    def ensure_local_db(self):
        """Kopiuje bazy wbudowane w plik .exe do folderu lokalnego, aby umożliwić ich edycję i aktualizację OTA."""
        os.makedirs(self.local_data_dir, exist_ok=True)
        bundled_starters = sciezka_do_zasobu("data/starters.json")
        bundled_batteries = sciezka_do_zasobu("data/batteries.json")
        
        if not os.path.exists(self.starters_file) and os.path.exists(bundled_starters):
            shutil.copy(bundled_starters, self.starters_file)
        if not os.path.exists(self.batteries_file) and os.path.exists(bundled_batteries):
            shutil.copy(bundled_batteries, self.batteries_file)

    def load_databases(self):
        try:
            if os.path.exists(self.starters_file):
                with open(self.starters_file, "r", encoding="utf-8") as f:
                    self.starters = json.load(f).get("starters", {})
            if os.path.exists(self.batteries_file):
                with open(self.batteries_file, "r", encoding="utf-8") as f:
                    self.batteries = json.load(f).get("batteries", {})
        except Exception as e:
            print(f"Błąd ładowania baz danych: {e}")

    def save_starters(self):
        with open(self.starters_file, "w", encoding="utf-8") as f:
            json.dump({"version": "1.0.0", "starters": self.starters}, f, indent=4, ensure_ascii=False)

    def save_batteries(self):
        with open(self.batteries_file, "w", encoding="utf-8") as f:
            json.dump({"version": "1.0.0", "batteries": self.batteries}, f, indent=4, ensure_ascii=False)


class CalculatorModel:
    RHO_CU = 1.68e-8  # Rezystywność miedzi w Ohm*m

    @staticmethod
    def calculate_voltage_drop(length_m, cross_section_mm2, cores_per_pole, peak_current_a):
        if cross_section_mm2 == 0 or cores_per_pole == 0:
            return 0, 0
        total_cross_section_m2 = cross_section_mm2 * 1e-6 * cores_per_pole
        resistance = CalculatorModel.RHO_CU * (length_m / total_cross_section_m2)
        voltage_drop = peak_current_a * resistance
        return resistance, voltage_drop

    @staticmethod
    def calculate_capacity_consumption(peak_current_a, starters_qty, attempt_time_s, attempts_qty):
        total_current = peak_current_a * starters_qty
        total_time_s = attempt_time_s * attempts_qty
        consumed_as = total_current * total_time_s
        consumed_ah = consumed_as / 3600
        return consumed_ah

    @staticmethod
    def calculate_charger_current(consumed_ah, charge_time_h, inefficiency_factor=1.4):
        if charge_time_h <= 0:
            return 0
        return (consumed_ah * inefficiency_factor) / charge_time_h