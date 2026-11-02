import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class MainView:
    def __init__(self, root, db_model):
        self.root = root
        self.db_model = db_model
        self.rev_data = [] 
        
        self._build_menu()
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=5, expand=True, fill='both')

        self.tab_project = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_project, text="1. Dane Projektowe")
        self._build_project_tab()

        self.tab_hardware = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_hardware, text="2. Konfiguracja Sprzętu")
        self._build_hardware_tab()

        self.tab_params = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_params, text="3. Kable i Profil Rozruchu")
        self._build_params_tab()

        self.tab_results = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_results, text="4. Wyniki Obliczeń")
        self._build_results_tab()

        self.tab_report = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_report, text="5. Załączniki i Raport")
        self._build_report_tab()

        self.tab_settings = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_settings, text="6. Ustawienia i Pomoc")
        self._build_settings_tab()

        frame_bottom = ttk.Frame(self.root)
        frame_bottom.pack(fill="x", pady=10, side="bottom")
        
        self.btn_calculate = ttk.Button(frame_bottom, text="OBLICZ I WERYFIKUJ PARAMETRY")
        self.btn_calculate.pack(side="top", fill="x", padx=20, pady=2, ipady=5)
        
        self.btn_generate_report = ttk.Button(frame_bottom, text="GENERUJ RAPORT (DOCX)")
        self.btn_generate_report.pack(side="top", fill="x", padx=20, pady=2, ipady=8)

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.file_menu = tk.Menu(menubar, tearoff=0)
        self.file_menu.add_command(label="Nowy Projekt")
        self.file_menu.add_command(label="Wczytaj Projekt (JSON)...")
        self.file_menu.add_command(label="Zapisz Projekt (JSON)...")
        menubar.add_cascade(label="Plik", menu=self.file_menu)
        self.root.config(menu=menubar)

    def _build_project_tab(self):
        scroll = ScrollableFrame(self.tab_project)
        scroll.pack(fill="both", expand=True)
        content = scroll.scrollable_frame

        frame = ttk.LabelFrame(content, text="Informacje Ogólne")
        frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(frame, text="Numer projektu:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_proj_no = ttk.Entry(frame, width=30)
        self.entry_proj_no.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Klient:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.entry_client = ttk.Entry(frame, width=30)
        self.entry_client.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame, text="Model agregatu:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_genset = ttk.Entry(frame, width=30)
        self.entry_genset.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Model silnika:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.entry_engine = ttk.Entry(frame, width=30)
        self.entry_engine.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(frame, text="Przygotował (Inicjały):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_author = ttk.Entry(frame, width=15)
        self.entry_author.insert(0, "MK")
        self.entry_author.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(frame, text="Język raportu:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.cb_language = ttk.Combobox(frame, values=["English", "Polski"], state="readonly", width=27)
        self.cb_language.set("English")
        self.cb_language.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        frame_revs = ttk.LabelFrame(content, text="Tabela Rewizji (Historia zmian dokumentu)")
        frame_revs.pack(fill="x", padx=10, pady=5)
        ttk.Button(frame_revs, text="+ Dodaj Rewizję", command=self.ui_add_rev_row).pack(anchor="nw", padx=5, pady=5)
        self.rev_container = ttk.Frame(frame_revs)
        self.rev_container.pack(fill="x", expand=True, padx=5, pady=5)
        self.ui_add_rev_row(rev="0", desc="Wydanie początkowe / Initial Issue", drawn="MK", check="Appr.")

    def ui_add_rev_row(self, rev="", desc="", drawn="", check="", date=None):
        if date is None: 
            date = datetime.now().strftime('%d%b%y').upper()
            
        row_frame = ttk.Frame(self.rev_container)
        row_frame.pack(fill="x", pady=2)
        
        v_rev, v_desc, v_drawn = tk.StringVar(value=rev), tk.StringVar(value=desc), tk.StringVar(value=drawn)
        v_check, v_date = tk.StringVar(value=check), tk.StringVar(value=date)
        
        rev_dict = {'rev': v_rev, 'desc': v_desc, 'drawn': v_drawn, 'check': v_check, 'date': v_date, 'frame': row_frame}
        self.rev_data.append(rev_dict)
        
        ttk.Label(row_frame, text="Rew:").pack(side="left")
        ttk.Entry(row_frame, textvariable=v_rev, width=4).pack(side="left", padx=2)
        ttk.Label(row_frame, text="Opis:").pack(side="left")
        ttk.Entry(row_frame, textvariable=v_desc, width=35).pack(side="left", padx=2)
        ttk.Label(row_frame, text="Wyk:").pack(side="left")
        ttk.Entry(row_frame, textvariable=v_drawn, width=5).pack(side="left", padx=2)
        ttk.Label(row_frame, text="Spr:").pack(side="left")
        ttk.Entry(row_frame, textvariable=v_check, width=5).pack(side="left", padx=2)
        ttk.Label(row_frame, text="Data:").pack(side="left")
        ttk.Entry(row_frame, textvariable=v_date, width=10).pack(side="left", padx=2)
        ttk.Button(row_frame, text="Usuń", width=5, command=lambda: self.ui_remove_rev_row(rev_dict)).pack(side="right", padx=5)

    def ui_remove_rev_row(self, rev_dict):
        rev_dict['frame'].destroy()
        self.rev_data.remove(rev_dict)

    def _build_hardware_tab(self):
        f_start = ttk.LabelFrame(self.tab_hardware, text="Rozruszniki (Wybierz z bazy lub wpisz ręcznie)")
        f_start.pack(fill="x", padx=10, pady=5)
        ttk.Label(f_start, text="Model (z bazy):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cb_starters = ttk.Combobox(f_start, values=list(self.db_model.starters.keys()), state="readonly", width=38)
        self.cb_starters.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(f_start, text="Napięcie [V]:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_starter_v = ttk.Entry(f_start, width=15)
        self.entry_starter_v.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(f_start, text="Prąd Szczytowy (Peak) [A]:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_starter_peak = ttk.Entry(f_start, width=15)
        self.entry_starter_peak.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(f_start, text="Ilość w agregacie:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.entry_starter_qty = ttk.Entry(f_start, width=15)
        self.entry_starter_qty.insert(0, "3")
        self.entry_starter_qty.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        f_batt = ttk.LabelFrame(self.tab_hardware, text="Akumulatory (Wybierz z bazy lub wpisz ręcznie)")
        f_batt.pack(fill="x", padx=10, pady=5)
        ttk.Label(f_batt, text="Model (z bazy):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cb_batteries = ttk.Combobox(f_batt, values=list(self.db_model.batteries.keys()), state="readonly", width=38)
        self.cb_batteries.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(f_batt, text="Typ (AGM / Lead-Acid):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.cb_batt_type = ttk.Combobox(f_batt, values=["AGM", "Lead-Acid", "Li-Ion"], width=15)
        self.cb_batt_type.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(f_batt, text="Pojemność pojedynczej baterii [Ah]:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_batt_ah = ttk.Entry(f_batt, width=15)
        self.entry_batt_ah.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(f_batt, text="Prąd rozruchowy CCA [A]:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.entry_batt_cca = ttk.Entry(f_batt, width=15)
        self.entry_batt_cca.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(f_batt, text="Ilość szeregowo (dla 24V):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.entry_batt_series = ttk.Entry(f_batt, width=15)
        self.entry_batt_series.insert(0, "2")
        self.entry_batt_series.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(f_batt, text="Ilość łańcuchów równoległych:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.entry_batt_parallel = ttk.Entry(f_batt, width=15)
        self.entry_batt_parallel.insert(0, "4")
        self.entry_batt_parallel.grid(row=5, column=1, padx=5, pady=5, sticky="w")

    def _build_params_tab(self):
        f_cab = ttk.LabelFrame(self.tab_params, text="Okablowanie Bateryjne")
        f_cab.pack(fill="x", padx=10, pady=5)
        ttk.Label(f_cab, text="Długość całkowita (w tę i z powrotem) [m]:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_cable_l = ttk.Entry(f_cab, width=10)
        self.entry_cable_l.insert(0, "12.5")
        self.entry_cable_l.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(f_cab, text="Przekrój pojedynczej żyły [mm2]:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_cable_a = ttk.Entry(f_cab, width=10)
        self.entry_cable_a.insert(0, "95")
        self.entry_cable_a.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(f_cab, text="Ilość żył na biegun:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_cable_cores = ttk.Entry(f_cab, width=10)
        self.entry_cable_cores.insert(0, "2")
        self.entry_cable_cores.grid(row=2, column=1, padx=5, pady=5)

        f_prof = ttk.LabelFrame(self.tab_params, text="Profil Rozruchu i Ładowanie")
        f_prof.pack(fill="x", padx=10, pady=5)
        ttk.Label(f_prof, text="Czas pojedynczej próby [s]:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_time_s = ttk.Entry(f_prof, width=10)
        self.entry_time_s.insert(0, "10")
        self.entry_time_s.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(f_prof, text="Ilość prób rozruchu:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_attempts = ttk.Entry(f_prof, width=10)
        self.entry_attempts.insert(0, "5")
        self.entry_attempts.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(f_prof, text="Czas pełnego naładowania [h]:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_charge_h = ttk.Entry(f_prof, width=10)
        self.entry_charge_h.insert(0, "3")
        self.entry_charge_h.grid(row=2, column=1, padx=5, pady=5)

    def _build_results_tab(self):
        self.lbl_results = ttk.Label(self.tab_results, text="Wprowadź dane i naciśnij Oblicz.", font=("Consolas", 10), justify="left")
        self.lbl_results.pack(padx=20, pady=20, anchor="nw")

    def _build_report_tab(self):
        f_att = ttk.LabelFrame(self.tab_report, text="Załączniki graficzne do raportu (Wczytywane również z Bazy Danych)")
        f_att.pack(fill="x", padx=10, pady=10)

        self.img_curve_path = tk.StringVar()
        self.img_diagram_path = tk.StringVar()
        self.img_batt_path = tk.StringVar()
        self.img_charger_path = tk.StringVar()

        def browse_img(var):
            f = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
            if f: var.set(f)

        row = 0
        for label_text, var in [
            ("Krzywa rozrusznika (np. Delco Remy):", self.img_curve_path),
            ("Karta/Zdjęcie akumulatora (np. Optima):", self.img_batt_path),
            ("Schemat połączeń izolatorów/baterii:", self.img_diagram_path),
            ("Karta/Zdjęcie ładowarki:", self.img_charger_path)
        ]:
            ttk.Label(f_att, text=label_text).grid(row=row, column=0, padx=5, pady=5, sticky="w")
            ttk.Entry(f_att, textvariable=var, width=45, state="readonly").grid(row=row, column=1, padx=5, pady=5)
            ttk.Button(f_att, text="Wybierz...", command=lambda v=var: browse_img(v)).grid(row=row, column=2, padx=5, pady=5)
            ttk.Button(f_att, text="X", width=3, command=lambda v=var: v.set("")).grid(row=row, column=3, padx=2, pady=5)
            row += 1

    def _build_settings_tab(self):
        f_upd = ttk.LabelFrame(self.tab_settings, text="Aktualizacje OTA (Over-The-Air)")
        f_upd.pack(fill="x", padx=10, pady=10)
        self.btn_update_app = ttk.Button(f_upd, text="Sprawdź aktualizacje programu")
        self.btn_update_app.pack(pady=5, padx=20, fill="x")
        self.btn_update_db = ttk.Button(f_upd, text="Sprawdź aktualizacje bazy danych")
        self.btn_update_db.pack(pady=5, padx=20, fill="x")

        f_db = ttk.LabelFrame(self.tab_settings, text="Baza Danych (Lokalne Edytory i Komunikacja z Twórcą)")
        f_db.pack(fill="x", padx=10, pady=10)
        self.btn_edit_starters = ttk.Button(f_db, text="Edytuj lokalną Bazę Rozruszników")
        self.btn_edit_starters.pack(pady=5, padx=20, fill="x")
        self.btn_edit_batteries = ttk.Button(f_db, text="Edytuj lokalną Bazę Akumulatorów")
        self.btn_edit_batteries.pack(pady=5, padx=20, fill="x")
        self.btn_report_item = ttk.Button(f_db, text="Wyślij do inżyniera prośbę o dodanie sprzętu do globalnej bazy...")
        self.btn_report_item.pack(pady=15, padx=20, fill="x")