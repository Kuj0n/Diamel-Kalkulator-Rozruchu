import os
import json
import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime
from modele import CalculatorModel
from narzedzia import sprawdz_aktualizacje, sprawdz_aktualizacje_bazy, pokaz_okno_zgloszenia_sprzetu

try:
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    pass

class MainController:
    def __init__(self, view, db_model):
        self.view = view
        self.db_model = db_model
        
        self.view.btn_calculate.config(command=self.process_calculations)
        self.view.btn_generate_report.config(command=self.generate_report_docx)
        self.view.cb_starters.bind("<<ComboboxSelected>>", self.on_starter_select)
        self.view.cb_batteries.bind("<<ComboboxSelected>>", self.on_battery_select)
        
        self.view.file_menu.entryconfig(0, command=self.nowy_projekt)
        self.view.file_menu.entryconfig(1, command=self.wczytaj_projekt)
        self.view.file_menu.entryconfig(2, command=self.zapisz_projekt)
        
        self.view.btn_update_app.config(command=lambda: sprawdz_aktualizacje(self.view.root, tryb="recznie"))
        self.view.btn_update_db.config(command=lambda: sprawdz_aktualizacje_bazy(self.view.root, self, tryb="recznie"))
        self.view.btn_report_item.config(command=lambda: pokaz_okno_zgloszenia_sprzetu(self.view.root))
        self.view.btn_edit_starters.config(command=self.open_starters_db_editor)
        self.view.btn_edit_batteries.config(command=self.open_batteries_db_editor)
        
        self.last_results = None

    def _set_entry_val(self, entry, value):
        entry.delete(0, tk.END)
        entry.insert(0, str(value))

    def on_starter_select(self, event):
        key = self.view.cb_starters.get()
        if key in self.db_model.starters:
            data = self.db_model.starters[key]
            self._set_entry_val(self.view.entry_starter_v, data.get("voltage_v", ""))
            self._set_entry_val(self.view.entry_starter_peak, data.get("peak_current_a", ""))
            # Automatyczne ładowanie ścieżki załącznika z bazy JSON
            if data.get("curve_path"): self.view.img_curve_path.set(data.get("curve_path", ""))

    def on_battery_select(self, event):
        key = self.view.cb_batteries.get()
        if key in self.db_model.batteries:
            data = self.db_model.batteries[key]
            self.view.cb_batt_type.set(data.get("type", "Lead-Acid"))
            self._set_entry_val(self.view.entry_batt_ah, data.get("capacity_ah", ""))
            self._set_entry_val(self.view.entry_batt_cca, data.get("cca_a", ""))
            # Automatyczne ładowanie ścieżki załącznika z bazy JSON
            if data.get("batt_path"): self.view.img_batt_path.set(data.get("batt_path", ""))

    def get_state_dict(self):
        return {
            "project_no": self.view.entry_proj_no.get(),
            "client": self.view.entry_client.get(),
            "genset": self.view.entry_genset.get(),
            "engine": self.view.entry_engine.get(),
            "author": self.view.entry_author.get(),
            "language": self.view.cb_language.get(),
            "revisions": [
                {
                    "rev": r['rev'].get(), "desc": r['desc'].get(),
                    "drawn": r['drawn'].get(), "check": r['check'].get(), "date": r['date'].get()
                } for r in self.view.rev_data
            ],
            "starter_model": self.view.cb_starters.get(),
            "starter_v": self.view.entry_starter_v.get(),
            "starter_peak": self.view.entry_starter_peak.get(),
            "starter_qty": self.view.entry_starter_qty.get(),
            "batt_model": self.view.cb_batteries.get(),
            "batt_type": self.view.cb_batt_type.get(),
            "batt_ah": self.view.entry_batt_ah.get(),
            "batt_cca": self.view.entry_batt_cca.get(),
            "batt_series": self.view.entry_batt_series.get(),
            "batt_parallel": self.view.entry_batt_parallel.get(),
            "cable_l": self.view.entry_cable_l.get(),
            "cable_a": self.view.entry_cable_a.get(),
            "cable_cores": self.view.entry_cable_cores.get(),
            "time_s": self.view.entry_time_s.get(),
            "attempts": self.view.entry_attempts.get(),
            "charge_h": self.view.entry_charge_h.get(),
            "images": {
                "curve": self.view.img_curve_path.get(),
                "diagram": self.view.img_diagram_path.get(),
                "batt": self.view.img_batt_path.get(),
                "charger": self.view.img_charger_path.get()
            }
        }

    def zapisz_projekt(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.get_state_dict(), f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Zapisano", "Projekt zapisany pomyślnie!")

    def wczytaj_projekt(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f: 
                    state = json.load(f)
                
                self._set_entry_val(self.view.entry_proj_no, state.get("project_no", ""))
                self._set_entry_val(self.view.entry_client, state.get("client", ""))
                self._set_entry_val(self.view.entry_genset, state.get("genset", ""))
                self._set_entry_val(self.view.entry_engine, state.get("engine", ""))
                self._set_entry_val(self.view.entry_author, state.get("author", ""))
                self.view.cb_language.set(state.get("language", "English"))
                
                for r in list(self.view.rev_data): self.view.ui_remove_rev_row(r)
                revs = state.get("revisions", [])
                for r in revs:
                    self.view.ui_add_rev_row(rev=r.get('rev',''), desc=r.get('desc',''), drawn=r.get('drawn',''), check=r.get('check',''), date=r.get('date',''))
                if not revs:
                    self.view.ui_add_rev_row(rev="0", desc="Wydanie początkowe / Initial Issue", drawn="MK", check="Appr.")

                self.view.cb_starters.set(state.get("starter_model", ""))
                self._set_entry_val(self.view.entry_starter_v, state.get("starter_v", ""))
                self._set_entry_val(self.view.entry_starter_peak, state.get("starter_peak", ""))
                self._set_entry_val(self.view.entry_starter_qty, state.get("starter_qty", ""))
                
                self.view.cb_batteries.set(state.get("batt_model", ""))
                self.view.cb_batt_type.set(state.get("batt_type", "Lead-Acid"))
                self._set_entry_val(self.view.entry_batt_ah, state.get("batt_ah", ""))
                self._set_entry_val(self.view.entry_batt_cca, state.get("batt_cca", ""))
                self._set_entry_val(self.view.entry_batt_series, state.get("batt_series", ""))
                self._set_entry_val(self.view.entry_batt_parallel, state.get("batt_parallel", ""))
                
                self._set_entry_val(self.view.entry_cable_l, state.get("cable_l", ""))
                self._set_entry_val(self.view.entry_cable_a, state.get("cable_a", ""))
                self._set_entry_val(self.view.entry_cable_cores, state.get("cable_cores", ""))
                
                self._set_entry_val(self.view.entry_time_s, state.get("time_s", ""))
                self._set_entry_val(self.view.entry_attempts, state.get("attempts", ""))
                self._set_entry_val(self.view.entry_charge_h, state.get("charge_h", ""))

                imgs = state.get("images", {})
                self.view.img_curve_path.set(imgs.get("curve", ""))
                self.view.img_diagram_path.set(imgs.get("diagram", ""))
                self.view.img_batt_path.set(imgs.get("batt", ""))
                self.view.img_charger_path.set(imgs.get("charger", ""))

                messagebox.showinfo("Wczytano", "Projekt wczytany pomyślnie.")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się wczytać pliku:\n{e}")

    def nowy_projekt(self):
        if messagebox.askyesno("Nowy Projekt", "Niezapisane dane zostaną utracone. Kontynuować?"):
            self._set_entry_val(self.view.entry_proj_no, "PRJ-2026-002")
            self._set_entry_val(self.view.entry_client, "Nazwa Klienta")
            self._set_entry_val(self.view.entry_genset, "C3500D5EB")
            self._set_entry_val(self.view.entry_engine, "QSK78-G39")
            
            for r in list(self.view.rev_data): self.view.ui_remove_rev_row(r)
            self.view.ui_add_rev_row(rev="0", desc="Wydanie początkowe / Initial Issue", drawn="MK", check="Appr.")

            self.view.cb_starters.set("")
            self.view.cb_batteries.set("")
            self.view.img_curve_path.set("")
            self.view.img_diagram_path.set("")
            self.view.img_batt_path.set("")
            self.view.img_charger_path.set("")
            self.view.lbl_results.config(text="Wprowadź dane i naciśnij Oblicz.")
            self.last_results = None

    def _get_ui_data(self):
        s_model = self.view.cb_starters.get() or "Custom Starter"
        b_model = self.view.cb_batteries.get() or "Custom Battery"
        
        s_peak_a = float(self.view.entry_starter_peak.get())
        s_qty = int(self.view.entry_starter_qty.get())
        s_volts = float(self.view.entry_starter_v.get())
        
        b_type = self.view.cb_batt_type.get()
        b_ah = float(self.view.entry_batt_ah.get())
        b_cca = float(self.view.entry_batt_cca.get())
        b_series = int(self.view.entry_batt_series.get())
        b_parallel = int(self.view.entry_batt_parallel.get())
        
        length_m = float(self.view.entry_cable_l.get())
        area_mm2 = float(self.view.entry_cable_a.get())
        cores = int(self.view.entry_cable_cores.get())

        time_s = float(self.view.entry_time_s.get())
        attempts = int(self.view.entry_attempts.get())
        charge_h = float(self.view.entry_charge_h.get())

        total_cca_available = b_cca * b_parallel
        res, v_drop = CalculatorModel.calculate_voltage_drop(length_m, area_mm2, cores, s_peak_a)
        
        cranking_voltage = 16.00
        sustained_voltage = cranking_voltage - v_drop

        total_ah_available = b_ah * b_parallel
        consumed_ah = CalculatorModel.calculate_capacity_consumption(s_peak_a, s_qty, time_s, attempts)
        
        inefficiency = 1.4 if b_type == "Lead-Acid" else 1.2
        charger_amps = CalculatorModel.calculate_charger_current(consumed_ah, charge_h, inefficiency)

        return {
            's_model': s_model, 'b_model': b_model, 's_peak_a': s_peak_a, 's_qty': s_qty, 's_volts': s_volts,
            'b_type': b_type, 'b_ah': b_ah, 'b_cca': b_cca, 'b_series': b_series, 'b_parallel': b_parallel,
            'length_m': length_m, 'area_mm2': area_mm2, 'cores': cores,
            'time_s': time_s, 'attempts': attempts, 'charge_h': charge_h,
            'total_cca_available': total_cca_available, 'res': res, 'v_drop': v_drop,
            'sustained_voltage': sustained_voltage, 'total_ah_available': total_ah_available,
            'consumed_ah': consumed_ah, 'inefficiency': inefficiency, 'charger_amps': charger_amps
        }

    def process_calculations(self):
        try:
            d = self._get_ui_data()
            self.last_results = d

            raport = (
                f"--- RAPORT OBLICZENIOWY ---\n\n"
                f"1. ANALIZA CCA:\n"
                f"Dostępne CCA układu ({d['b_parallel']} x {d['b_cca']}A): {d['total_cca_available']} A\n\n"
                f"2. SPADKI NAPIĘCIA (Scenariusz {d['s_peak_a']}A):\n"
                f"Rezystancja linii kablowej: {d['res']:.6f} Ohm\n"
                f"Spadek napięcia (Vd):       {d['v_drop']:.2f} V\n"
                f"Napięcie w trakcie kręcenia (po uwzgl. Vd): {d['sustained_voltage']:.2f} V\n\n"
                f"3. ZUŻYCIE POJEMNOŚCI:\n"
                f"Całkowita pojemność bazy (C):  {d['total_ah_available']} Ah\n"
                f"Zużycie (profil {d['attempts']}x{d['time_s']}s): {d['consumed_ah']:.2f} Ah\n"
                f"Status pojemności: {'[OK] Zapas wystarczający' if d['consumed_ah'] < d['total_ah_available'] else '[BŁĄD] Brak wymaganej pojemności!'}\n\n"
                f"4. DOBÓR ŁADOWARKI:\n"
                f"Technologia: {d['b_type']} (nieefektywność {d['inefficiency']})\n"
                f"Rekomendowany min. prąd ładowania (dla {d['charge_h']}h): {d['charger_amps']:.2f} A\n"
            )
            self.view.lbl_results.config(text=raport)
            self.view.notebook.select(self.view.tab_results)

        except ValueError:
            messagebox.showerror("Błąd danych", "Wprowadzono niepoprawne liczby.")
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def get_translations(self, lang):
        if lang == 'Polski':
            return {
                'doc_title': "DOKUMENTACJA TECHNICZNA DO ZATWIERDZENIA",
                'doc_subtitle': "SYSTEM ROZRUCHU AGREGATU",
                'meta_proj_no': "NUMER PROJEKTU:",
                'meta_proj_title': "TYTUŁ PROJEKTU:",
                'meta_proj_title_val': "Obliczenia Układu Rozruchowego",
                'meta_client': "DLA KLIENTA:",
                'meta_author': "PRZYGOTOWAŁ:",
                'meta_date': "DATA:",
                'rev_h': ["Rew.", "Opis Zmiany", "Wykonał", "Sprawdził", "Data"],
                'sec1_title': " Szczegóły Techniczne Rozrusznika:",
                's_qty': "ILOŚĆ ROZRUSZNIKÓW: ",
                's_model': "PRODUCENT/MODEL: ",
                's_volts': "NAPIĘCIE: ",
                's_supply': "ZASILANIE: ELEKTRYCZNE\n\n",
                's_desc': "Krzywe wydajności rozrusznika są tworzone przy użyciu różnych metod (ISO, SAE, JIS, inne). Parametry, które mogą wpływać na wydajność rozrusznika, to temperatura, dostarczona krzywa akumulatora, rezystancja obwodu i inne. Jeśli mają być porównane dwie krzywe mocy rozrusznika, muszą być one utworzone przy użyciu tej samej metody.\nMoment obrotowy rozrusznika jest bezpośrednio związany z poborem prądu przez rozrusznik. Obroty rozrusznika są związane z napięciem dostępnym na rozruszniku.\nDlatego moc wyjściowa rozrusznika jest zależna od napięcia dostępnego na nim podczas pobierania określonego prądu. Prąd rozrusznika jest dyktowany przez wymagania dotyczące momentu obrotowego napędzanej maszyny.",
                's_fig': "Rysunek 1. Krzywa Rozrusznika ",
                'sec2_title': " Spadek Napięcia na Kablach (Na Rozrusznik / Na Zestaw Baterii):",
                'vd_res': "Rezystywność Miedzi = 1.68 x 10^-8\n",
                'vd_len': "Maksymalna długość kabli (Całkowita) = ",
                'vd_calc1': " Rezystancja kabli bateryjnych = 1.68 x 10^-8 x ",
                'vd_calc2': "Całkowity spadek napięcia na każdy rozrusznik:\n",
                'vd_calc3': "1. Spadek napięcia w normalnej sytuacji (Prąd 1000A)\n   = ",
                'vd_calc4': "2. Szczytowy spadek napięcia w najgorszym przypadku (Prąd ",
                'sec3_title': " Obliczenia Poboru Prądu przez Rozrusznik:",
                'dr_desc': "Poniższe wyliczenie to ciągły pobór prądu z każdego rozrusznika z uwzględnieniem najgorszego spadku napięcia od momentu początkowego załączenia rozrusznika.\n",
                'dr_v1': "Oczekiwane napięcie kręcenia = 16.00 V\n",
                'dr_v2': "Podtrzymywane napięcie kręcenia z uwzględnieniem spadku = 16.00 V - ",
                'dr_v3': "Przewidywany prąd obrotowy rozrusznika należy odczytać z krzywej na podstawie powyższego napięcia.\n",
                'sec4_title': " Obliczenia Doboru i Wydajności Baterii:",
                'b_desc1': "Istnieje wiele potencjalnych zmiennych, które wpływają na całkowity czas pracy, których te obliczenia nie biorą pod uwagę i które są niezwykle trudne do oszacowania, takie jak:\n1. Temperatura otoczenia\n2. Minimalne napięcie baterii wymagane do działania obwodu 24V\n3. Rezystancja obwodu\n4. Lepkość oleju silnikowego i temperatura oleju\n5. Stan naładowania przed testem\n6. Fakt, że za każdym razem, gdy baterie rozpoczynają kolejny cykl rozruchu, muszą pokonać początkową bezwładność silnika (maksymalny prąd / minimalne napięcie), co skutkuje dodatkowym obciążeniem / rozładowaniem układu baterii.\n\n",
                'b_desc2': "Całkowita liczba baterii - ",
                'b_desc3': "Całkowita liczba rozruszników - ",
                'b_desc4': "Żywotność baterii (godziny) = (pojemność baterii w mAh / prąd obciążenia w mA) x 0.7\n\n",
                'b_desc5': " szt. baterii o pojemności ",
                'b_desc6': " CCA jest połączonych szeregowo-równolegle. Dlatego całkowite CCA wynosi ",
                'b_desc7': "Aby podsumować obliczenia wydajności baterii, pracowaliśmy na najgorszym scenariuszu prądu rozruchowego rzędu ",
                'b_desc8': " sekund kręcenia x ",
                'b_desc9': " prób = ",
                'b_desc10': " maksymalny prąd rozruchu x ",
                'b_desc11': "Zestawy baterii to jednostki połączone w układzie ",
                'b_desc12': " zapewniające łącznie ",
                'b_desc13': "Dlatego zestaw baterii jest około ",
                'b_desc14': " razy większy, niż byłoby to wymagane przy założeniu najbardziej nierealistycznego najgorszego scenariusza. ",
                'b_desc15': "O ile systemy są w dobrym stanie technicznym z poprawnie zwymiarowanymi kablami, układ baterii nie powinien mieć problemów z zapewnieniem wymaganych rozruchów bez awarii.\n",
                'sec5_title': " Przykładowe Obliczenia Doboru Ładowarki Baterii:",
                'ch_1': "Maksymalny Prąd Ciągły (Najgorszy Przypadek) = ",
                'ch_2': "Maksymalny czas kręcenia = ",
                'ch_3': "Maksymalna liczba prób = ",
                'ch_4': "Czas ponownego ładowania = ",
                'ch_5': "Stała nieefektywności baterii (",
                'ch_6': "AH pobrane przez rozruszniki dla tego przykładu = ",
                'ch_7': "Szacowana Wielkość Ładowarki: ",
                'ch_8': "Na podstawie powyższego zalecamy użycie odpowiednio dobranej ładowarki (np. ",
                'sec6_title': " Proponowane Połączenia Baterii:",
                'conn_desc': "Wszystkie banki baterii zostaną podłączone do rozruszników zgodnie z poniższym schematem. Agregat prądotwórczy można odizolować DC poprzez otwarcie przełączników izolatorów, co eliminuje konieczność odłączania baterii. Kable bateryjne będą wykonane z elastycznego przewodu PVC na dodatnich i ujemnych zaciskach między bateriami a izolatorami.",
                'fig_diagram': "Schemat połączeń izolatorów/baterii/rozruszników",
                'fig_batt': "Dane Techniczne / Wymiary Baterii",
                'fig_charger': "Specyfikacja Ładowarki Baterii"
            }
        else:
            return {
                'doc_title': "TECHNICAL SUBMITTAL FOR APPROVAL",
                'doc_subtitle': "GENERATOR STARTING SYSTEM",
                'meta_proj_no': "PROJECT NUMBER:",
                'meta_proj_title': "PROJECT TITLE:",
                'meta_proj_title_val': "Generator Starting System Calculations",
                'meta_client': "INTENDED FOR:",
                'meta_author': "PREPARED BY:",
                'meta_date': "DATE:",
                'rev_h': ["Rev.", "Description of Change", "Drawn", "Check", "Date"],
                'sec1_title': " Starter Motor Technical Details:",
                's_qty': "NO OF STARTER MOTORS: ",
                's_model': "MANUFACTURER/MODEL: ",
                's_volts': "VOLTS: ",
                's_supply': "POWER SUPPLY: ELECTRIC\n\n",
                's_desc': "Cranking motor performance curves are created using various methods (ISO, SAE, JIS, other). Parameters that can affect the performance of a cranking motor are temperature, battery curve supplied, circuit resistance, and others. If two cranking motor power curves are to be compared, the curves must be created using the same method.\nCranking motor torque is directly related to cranking motor current draw. Cranking motor RPM is related to voltage available at the cranking motor.\nTherefore, cranking motor output power is dependent on voltage available at the cranking motor when it is drawing a certain current. Cranking motor current is dictated by the torque requirement of the machine it is driving.",
                's_fig': "Figure 1. Starter Motor Curve: ",
                'sec2_title': " Battery Cable Voltage Drop (Per Starter Motor / Per Battery Set):",
                'vd_res': "Resistivity of Copper = 1.68 x 10^-8\n",
                'vd_len': "Max cable length (Total) = ",
                'vd_calc1': " Battery cables resistance = 1.68 x 10^-8 x ",
                'vd_calc2': "Total Voltage drop through each starter motor:\n",
                'vd_calc3': "1. Substation voltage drop in normal situation (Current 1000A)\n   = ",
                'vd_calc4': "2. Peak Voltage drop in worst case (Current ",
                'sec3_title': " Starter Motor Current Draw Calculations:",
                'dr_desc': "The below calculation is the sustained current draw from each starter motor but with the worst-case volt drop factored in from initial starter motor engagement.\n",
                'dr_v1': "Approx. Cranking Voltage = 16.00 volts\n",
                'dr_v2': "Sustained cranking Voltage including volt drop (normal situation) = 16.00 V - ",
                'dr_v3': "Starter motor anticipated rolling amperage is calculated by referencing the above curve which indicates an approximate current draw.\n",
                'sec4_title': " Battery Sizing & Performance Calculations:",
                'b_desc1': "There are many potential variables that will affect the overall run time that these calculations do not take into account and that are extremely difficult to quantify, such as:\n1. Ambient Temperature\n2. Minimal battery voltage required for the 24-volt circuit to operate\n3. Circuit resistance\n4. Oil viscosity of engine and oil temperature\n5. State of charge prior to test\n6. That every time the batteries start the next cranking cycle, they must overcome the initial inertia of the engine i.e. max current / min voltage which will result in additional strain / discharge on the battery system.\n\n",
                'b_desc2': "Total number of batteries - ",
                'b_desc3': "Total number of starter motors - ",
                'b_desc4': "Battery life (hours) = (battery capacity in mAh / load current in mA) x 0.7\n\n",
                'b_desc5': " No. ",
                'b_desc6': " CCA batteries are connected in series parallel. Therefore, the total CCA when connected in series parallel to ",
                'b_desc7': "To summarize the battery performance calculation we have worked on the worst case cranking current scenario of ",
                'b_desc8': " seconds cranking x ",
                'b_desc9': " attempts = ",
                'b_desc10': " maximum cranking current x ",
                'b_desc11': "The batteries set's are ",
                'b_desc12': " units which is ",
                'b_desc13': "Therefore, the battery set is approx. ",
                'b_desc14': "x larger than what would be required assuming the most unrealistic worst-case scenario. ",
                'b_desc15': "Providing the systems are in good service condition with correctly sized battery cables then the battery system capacity should have no issues with providing the required cranks without failing.\n",
                'sec5_title': " Battery Charger Sizing Calculation Example:",
                'ch_1': "Maximum Rolling Current (Worst Case) = ",
                'ch_2': "Maximum cranking time = ",
                'ch_3': "Maximum attempts to start = ",
                'ch_4': "Re-Charge Time = ",
                'ch_5': " Battery inefficiency constant = ",
                'ch_6': "AH drawn by the starters for this example = ",
                'ch_7': "Estimated Charger Size: ",
                'ch_8': "Based on the above, we would recommend using an appropriately sized charger (e.g. ",
                'sec6_title': " Proposed Battery Connections:",
                'conn_desc': "All battery banks will be coupled to the starter motors as per the drawing below. The generator can be DC isolated by opening the isolator switches thus removing the need to disconnect the batteries. Battery cables will be tri-rated PVC flexible cable on the positive and negatives between the battery terminals and isolators.",
                'fig_diagram': "Batteries/chargers/starter Motors connection diagram",
                'fig_batt': "Battery Technical Data / Dimensions",
                'fig_charger': "Battery Charger Specification"
            }

    def generate_report_docx(self):
        try:
            import docx
        except ImportError:
            messagebox.showerror("Błąd", "Brak biblioteki python-docx. Zainstaluj: pip install python-docx")
            return
            
        try:
            d = self._get_ui_data()
        except ValueError:
            messagebox.showerror("Błąd", "Uzupełnij poprawnie dane liczbowe przed generowaniem raportu.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".docx", 
            filetypes=[("Word Document", "*.docx")], 
            initialfile=f"Starting_System_{self.view.entry_proj_no.get()}.docx"
        )
        if not file_path:
            return

        t = self.get_translations(self.view.cb_language.get())

        try:
            doc = Document()
            engine_name = self.view.entry_engine.get()
            
            title = doc.add_heading(t['doc_title'], level=1)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.add_heading(t['doc_subtitle'], level=2).alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.add_paragraph()

            t_meta = doc.add_table(rows=5, cols=2)
            t_meta.style = 'Table Grid'
            meta_data = [
                (t['meta_proj_no'], self.view.entry_proj_no.get()),
                (t['meta_proj_title'], t['meta_proj_title_val']),
                (t['meta_client'], self.view.entry_client.get()),
                (t['meta_author'], self.view.entry_author.get()),
                (t['meta_date'], datetime.now().strftime('%Y-%m-%d'))
            ]
            for i, (label, val) in enumerate(meta_data):
                t_meta.rows[i].cells[0].text = label
                t_meta.rows[i].cells[0].paragraphs[0].runs[0].bold = True
                t_meta.rows[i].cells[1].text = val

            doc.add_paragraph()
            
            if self.view.rev_data:
                t_rev = doc.add_table(rows=1 + len(self.view.rev_data), cols=5)
                t_rev.style = 'Table Grid'
                for i, h in enumerate(t['rev_h']):
                    t_rev.rows[0].cells[i].text = h
                    t_rev.rows[0].cells[i].paragraphs[0].runs[0].bold = True
                    
                for i, rev in enumerate(self.view.rev_data):
                    row_cells = t_rev.rows[i+1].cells
                    row_cells[0].text = rev['rev'].get()
                    row_cells[1].text = rev['desc'].get()
                    row_cells[2].text = rev['drawn'].get()
                    row_cells[3].text = rev['check'].get()
                    row_cells[4].text = rev['date'].get()

            doc.add_paragraph()
            
            # --- 1. STARTER MOTOR DETAILS ---
            doc.add_heading(f"{engine_name}{t['sec1_title']}", level=2)
            p_starter = doc.add_paragraph()
            p_starter.add_run(f"{t['s_qty']}{d['s_qty']}\n").bold = True
            p_starter.add_run(f"{t['s_model']}{d['s_model']}\n").bold = True
            p_starter.add_run(f"{t['s_volts']}{d['s_volts']}V\n").bold = True
            p_starter.add_run(t['s_supply']).bold = True
            p_starter.add_run(t['s_desc'])

            path_curve = self.view.img_curve_path.get()
            if path_curve and os.path.exists(path_curve):
                p_img1 = doc.add_paragraph()
                p_img1.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img1.add_run().add_picture(path_curve, width=Inches(6.0))
                doc.add_paragraph(f"{t['s_fig']}{d['s_model']}").alignment = WD_ALIGN_PARAGRAPH.CENTER

            doc.add_page_break()

            # --- 2. CABLE VOLTAGE DROP ---
            doc.add_heading(f"{engine_name}{t['sec2_title']}", level=2)
            p_vd = doc.add_paragraph()
            p_vd.add_run(t['vd_res'])
            p_vd.add_run(f"{t['vd_len']}{d['length_m']} m\n")
            
            p_vd.add_run(f"{d['cores']} x {d['area_mm2']} mm2{t['vd_calc1']}{d['length_m']} / ({d['cores']} x {d['area_mm2']} x 10^-6) = {d['res']:.6f} ohms\n\n")
            
            p_vd.add_run(t['vd_calc2']).bold = True
            p_vd.add_run(f"{t['vd_calc3']}{d['res']:.6f} x 1000 = {d['res']*1000:.2f} Volts\n")
            p_vd.add_run(f"{t['vd_calc4']}{d['s_peak_a']}A)\n   = {d['res']:.6f} x {d['s_peak_a']} = {d['v_drop']:.2f} Volts\n")

            # --- 3. CURRENT DRAW ---
            doc.add_heading(f"{engine_name}{t['sec3_title']}", level=2)
            p_draw = doc.add_paragraph()
            p_draw.add_run(t['dr_desc'])
            p_draw.add_run(t['dr_v1'])
            p_draw.add_run(f"{t['dr_v2']}{d['v_drop']:.2f} V = {d['sustained_voltage']:.2f} volts.\n").bold = True
            p_draw.add_run(t['dr_v3'])

            # --- 4. SIZING & PERFORMANCE ---
            doc.add_heading(t['sec4_title'], level=2)
            p_batt_intro = doc.add_paragraph()
            p_batt_intro.add_run(t['b_desc1'])
            p_batt_intro.add_run(f"{t['b_desc2']}{d['b_series'] * d['b_parallel']}\n")
            p_batt_intro.add_run(f"{t['b_desc3']}{d['s_qty']}\n")
            p_batt_intro.add_run(t['b_desc4'])
            
            p_batt_intro.add_run(f"{d['b_series'] * d['b_parallel']}{t['b_desc5']}{d['b_ah']} Ah {d['b_cca']}{t['b_desc6']}{d['s_qty']} rozruszników to {d['total_cca_available']} CCA.\n\n").bold = True
            
            total_crank_a = d['s_peak_a'] * d['s_qty']
            total_sec = d['time_s'] * d['attempts']
            asec = total_crank_a * total_sec
            
            p_batt_calc = doc.add_paragraph()
            p_batt_calc.add_run(f"{t['b_desc7']}{d['s_peak_a']} amps.\n")
            p_batt_calc.add_run(f"{d['time_s']}{t['b_desc8']}{d['attempts']}{t['b_desc9']}{total_sec} seconds\n")
            p_batt_calc.add_run(f"{d['s_peak_a']}A x {d['s_qty']}{t['b_desc10']}{total_sec} seconds = {asec} ASec or {d['consumed_ah']:.2f} Ah.\n\n").bold = True
            
            p_batt_calc.add_run(f"{t['b_desc11']}{d['b_series']}x{d['b_parallel']} ({d['b_ah']}Ah){t['b_desc12']}{d['total_ah_available']}Ah na bank. ")
            ratio = d['total_ah_available'] / d['consumed_ah'] if d['consumed_ah'] > 0 else 0
            p_batt_calc.add_run(f"{t['b_desc13']}{ratio:.1f}{t['b_desc14']}")
            p_batt_calc.add_run(t['b_desc15'])

            # --- 5. CHARGER SIZING ---
            doc.add_heading(t['sec5_title'], level=2)
            p_charg = doc.add_paragraph()
            p_charg.add_run(f"{t['ch_1']}{d['s_peak_a']} x {d['s_qty']} = {total_crank_a} Amps\n")
            p_charg.add_run(f"{t['ch_2']}{d['time_s']} seconds\n")
            p_charg.add_run(f"{t['ch_3']}{d['attempts']}\n")
            p_charg.add_run(f"{t['ch_4']}{d['charge_h']} hours\n")
            p_charg.add_run(f"{d['b_type']}{t['ch_5']}{d['inefficiency']}\n\n")
            
            p_charg.add_run(f"{t['ch_6']}{d['consumed_ah']:.2f} AH\n").bold = True
            p_charg.add_run(f"{t['ch_7']}{d['consumed_ah']:.2f} AH x {d['inefficiency']} (Constant) / {d['charge_h']} (hours) = {d['charger_amps']:.2f} Amps\n").bold = True
            p_charg.add_run(f"{t['ch_8']}{int(d['charger_amps'] + 5)}A).\n")

            # --- 6. CONNECTIONS ---
            doc.add_heading(t['sec6_title'], level=2)
            p_conn = doc.add_paragraph()
            p_conn.add_run(t['conn_desc'])
            
            for img_path, title_key in [
                (self.view.img_diagram_path.get(), 'fig_diagram'),
                (self.view.img_batt_path.get(), 'fig_batt'),
                (self.view.img_charger_path.get(), 'fig_charger')
            ]:
                if img_path and os.path.exists(img_path):
                    doc.add_page_break()
                    doc.add_heading(t[title_key], level=2)
                    p_img = doc.add_paragraph()
                    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_img.add_run().add_picture(img_path, width=Inches(6.0))

            doc.save(file_path)
            messagebox.showinfo("Sukces", f"Raport wygenerowano pomyślnie:\n{file_path}")
            
        except PermissionError:
            messagebox.showerror("Błąd Zapisu", "Plik jest otwarty w innym programie. Zamknij Worda i spróbuj ponownie.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił nieoczekiwany błąd podczas generowania raportu:\n{str(e)}")

    def open_starters_db_editor(self):
        win = tk.Toplevel(self.view.root)
        win.title("Edytor Bazy Rozruszników")
        win.geometry("500x400")
        
        frame_list = ttk.Frame(win)
        frame_list.pack(side="left", fill="y", padx=5, pady=5)
        lst = tk.Listbox(frame_list, width=25)
        lst.pack(side="left", fill="y", expand=True)
        for e in sorted(self.db_model.starters.keys()): lst.insert(tk.END, e)
        
        frame_det = ttk.Frame(win)
        frame_det.pack(side="right", fill="both", expand=True, padx=10, pady=5)
        
        v_name, v_volts, v_peak, v_curve = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
        
        ttk.Label(frame_det, text="Nazwa modelu:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(frame_det, textvariable=v_name, width=20).grid(row=0, column=1, sticky="w", pady=5)
        ttk.Label(frame_det, text="Napięcie [V]:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(frame_det, textvariable=v_volts, width=10).grid(row=1, column=1, sticky="w", pady=5)
        ttk.Label(frame_det, text="Prąd Peak [A]:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(frame_det, textvariable=v_peak, width=10).grid(row=2, column=1, sticky="w", pady=5)
        
        ttk.Label(frame_det, text="Plik krzywej rozruchu:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(frame_det, textvariable=v_curve, width=15).grid(row=3, column=1, sticky="w", pady=5)
        ttk.Button(frame_det, text="...", width=3, command=lambda: v_curve.set(filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")]))).grid(row=3, column=2, padx=2)

        def on_select(evt):
            sel = lst.curselection()
            if sel:
                name = lst.get(sel[0])
                data = self.db_model.starters[name]
                v_name.set(name)
                v_volts.set(data.get("voltage_v", ""))
                v_peak.set(data.get("peak_current_a", ""))
                v_curve.set(data.get("curve_path", ""))
        lst.bind("<<ListboxSelect>>", on_select)
        
        def save_item():
            name = v_name.get().strip()
            if not name: return
            try:
                self.db_model.starters[name] = {
                    "voltage_v": float(v_volts.get()),
                    "peak_current_a": float(v_peak.get()),
                    "power_kw": 0, "normal_current_a": 0,
                    "curve_path": v_curve.get()
                }
                self.db_model.save_starters()
                self.view.cb_starters['values'] = list(self.db_model.starters.keys())
                lst.delete(0, tk.END)
                for e in sorted(self.db_model.starters.keys()): lst.insert(tk.END, e)
                messagebox.showinfo("Zapisano", f"Zapisano: {name}", parent=win)
            except ValueError:
                messagebox.showerror("Błąd", "Napięcie i prąd muszą być liczbami!", parent=win)

        def del_item():
            sel = lst.curselection()
            if sel:
                name = lst.get(sel[0])
                del self.db_model.starters[name]
                self.db_model.save_starters()
                self.view.cb_starters['values'] = list(self.db_model.starters.keys())
                lst.delete(0, tk.END)
                for e in sorted(self.db_model.starters.keys()): lst.insert(tk.END, e)
                v_name.set(""); v_volts.set(""); v_peak.set(""); v_curve.set("")

        ttk.Button(frame_det, text="Zapisz", command=save_item).grid(row=5, column=0, pady=20)
        ttk.Button(frame_det, text="Usuń", command=del_item).grid(row=5, column=1, pady=20)

    def open_batteries_db_editor(self):
        win = tk.Toplevel(self.view.root)
        win.title("Edytor Bazy Akumulatorów")
        win.geometry("550x400")
        
        frame_list = ttk.Frame(win)
        frame_list.pack(side="left", fill="y", padx=5, pady=5)
        lst = tk.Listbox(frame_list, width=25)
        lst.pack(side="left", fill="y", expand=True)
        for e in sorted(self.db_model.batteries.keys()): lst.insert(tk.END, e)
        
        frame_det = ttk.Frame(win)
        frame_det.pack(side="right", fill="both", expand=True, padx=10, pady=5)
        
        v_name, v_type, v_ah, v_cca, v_img = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
        
        ttk.Label(frame_det, text="Nazwa modelu:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(frame_det, textvariable=v_name, width=25).grid(row=0, column=1, sticky="w", pady=5)
        ttk.Label(frame_det, text="Typ (AGM/Lead-Acid):").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Combobox(frame_det, textvariable=v_type, values=["AGM", "Lead-Acid", "Li-Ion"]).grid(row=1, column=1, sticky="w", pady=5)
        ttk.Label(frame_det, text="Pojemność [Ah]:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(frame_det, textvariable=v_ah, width=10).grid(row=2, column=1, sticky="w", pady=5)
        ttk.Label(frame_det, text="Prąd CCA [A]:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(frame_det, textvariable=v_cca, width=10).grid(row=3, column=1, sticky="w", pady=5)
        
        ttk.Label(frame_det, text="Karta katalogowa:").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Entry(frame_det, textvariable=v_img, width=15).grid(row=4, column=1, sticky="w", pady=5)
        ttk.Button(frame_det, text="...", width=3, command=lambda: v_img.set(filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")]))).grid(row=4, column=2, padx=2)

        def on_select(evt):
            sel = lst.curselection()
            if sel:
                name = lst.get(sel[0])
                data = self.db_model.batteries[name]
                v_name.set(name)
                v_type.set(data.get("type", "Lead-Acid"))
                v_ah.set(data.get("capacity_ah", ""))
                v_cca.set(data.get("cca_a", ""))
                v_img.set(data.get("batt_path", ""))
        lst.bind("<<ListboxSelect>>", on_select)
        
        def save_item():
            name = v_name.get().strip()
            if not name: return
            try:
                self.db_model.batteries[name] = {
                    "type": v_type.get(),
                    "capacity_ah": float(v_ah.get()),
                    "cca_a": float(v_cca.get()),
                    "voltage_v": 12,
                    "batt_path": v_img.get()
                }
                self.db_model.save_batteries()
                self.view.cb_batteries['values'] = list(self.db_model.batteries.keys())
                lst.delete(0, tk.END)
                for e in sorted(self.db_model.batteries.keys()): lst.insert(tk.END, e)
                messagebox.showinfo("Zapisano", f"Zapisano: {name}", parent=win)
            except ValueError:
                messagebox.showerror("Błąd", "Pojemność i CCA muszą być liczbami!", parent=win)

        def del_item():
            sel = lst.curselection()
            if sel:
                name = lst.get(sel[0])
                del self.db_model.batteries[name]
                self.db_model.save_batteries()
                self.view.cb_batteries['values'] = list(self.db_model.batteries.keys())
                lst.delete(0, tk.END)
                for e in sorted(self.db_model.batteries.keys()): lst.insert(tk.END, e)
                v_name.set(""); v_type.set(""); v_ah.set(""); v_cca.set(""); v_img.set("")

        ttk.Button(frame_det, text="Zapisz", command=save_item).grid(row=5, column=0, pady=20)
        ttk.Button(frame_det, text="Usuń", command=del_item).grid(row=5, column=1, pady=20)