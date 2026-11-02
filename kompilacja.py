import os
import re
import json
import subprocess
import shutil

# --- KONFIGURACJA ---
folder_zasoby = "Zasoby"
folder_data = "data" 
plik_glowny = "main.py"
pliki_modulow = ["modele.py", "widoki.py", "kontrolery.py", "narzedzia.py", "konfiguracja_app.py"]
plik_ikony = os.path.join(folder_zasoby, "ikona.ico")
plik_sekretow = os.path.join("Konfiguracja", "sekrety.json")

inno_setup_compiler = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not os.path.exists(inno_setup_compiler):
    print("❌ Błąd: Nie znaleziono kompilatora Inno Setup!")
    exit(1)

print("🔍 Analizowanie konfiguracji (wersja MVC - Kalkulator Rozruchu)...")
with open("konfiguracja_app.py", "r", encoding="utf-8") as f:
    kod_konf = f.read()

wersja = re.search(r'VERSION\s*=\s*"([^"]+)"', kod_konf).group(1)
wersja_bazy = re.search(r'DB_VERSION\s*=\s*"([^"]+)"', kod_konf).group(1)
data_wydania = re.search(r'BUILD_DATE\s*=\s*"([^"]+)"', kod_konf).group(1)[:10]
changelog_full = re.search(r'CHANGELOG\s*=\s*"""(.*?)"""', kod_konf, re.DOTALL).group(1).strip()
changelog_db = re.search(r'CHANGELOG_DB\s*=\s*"""(.*?)"""', kod_konf, re.DOTALL).group(1).strip()

if os.path.exists(plik_sekretow):
    print("🔐 Wstrzykiwanie sekretów do kompilacji...")
    with open(plik_sekretow, "r", encoding="utf-8") as fs: sekrety = json.load(fs)
    kod_konf = re.sub(r'ENCRYPTION_KEY\s*=\s*b"[^"]*"', f'ENCRYPTION_KEY = b"{sekrety.get("ENCRYPTION_KEY", "")}"', kod_konf)
    kod_konf = re.sub(r'EMAIL_NADAWCY\s*=\s*"[^"]*"', f'EMAIL_NADAWCY = "{sekrety.get("EMAIL_NADAWCY", "")}"', kod_konf)
    kod_konf = re.sub(r'HASLO_NADAWCY\s*=\s*"[^"]*"', f'HASLO_NADAWCY = "{sekrety.get("HASLO_NADAWCY", "")}"', kod_konf)
    kod_konf = re.sub(r'EMAIL_ODBIORCY\s*=\s*"[^"]*"', f'EMAIL_ODBIORCY = "{sekrety.get("EMAIL_ODBIORCY", "")}"', kod_konf)

folder_archiwum = os.path.join(wersja, "Archiwum")
folder_paczka = os.path.join(wersja, "Paczka")
sciezka_ftp_app = os.path.join(folder_paczka, "kalkulator_rozruchu", "aplikacja")
sciezka_ftp_log = os.path.join(folder_paczka, "kalkulator_rozruchu", "changelog")

os.makedirs(folder_archiwum, exist_ok=True)
os.makedirs(sciezka_ftp_app, exist_ok=True)
os.makedirs(sciezka_ftp_log, exist_ok=True)

print("📂 Kopiowanie rozdzielonych modułów, danych i zasobów...")
with open(os.path.join(folder_archiwum, "konfiguracja_app.py"), "w", encoding="utf-8") as f: f.write(kod_konf)

for m_plik in [plik_glowny] + pliki_modulow:
    if os.path.exists(m_plik): shutil.copy(m_plik, os.path.join(folder_archiwum, m_plik))

if os.path.exists(folder_zasoby):
    shutil.copytree(folder_zasoby, os.path.join(folder_archiwum, folder_zasoby), dirs_exist_ok=True)

if os.path.exists(folder_data):
    shutil.copytree(folder_data, os.path.join(folder_archiwum, folder_data), dirs_exist_ok=True)

ikona_skopiowana = False
if os.path.exists(plik_ikony): 
    shutil.copy(plik_ikony, os.path.join(folder_archiwum, "ikona.ico"))
    ikona_skopiowana = True
else:
    print("⚠️ Ostrzeżenie: Nie znaleziono pliku 'ikona.ico' w folderze Zasoby. Kompilacja bez ikony.")

v_parts = wersja.split('.') + ['0'] * (4 - len(wersja.split('.')))
v_str = ".".join(v_parts)
nazwa_stala = "Kalkulator_Rozruchu"
nazwa_instalatora_exe = f"Instalator_Rozruchu_v{wersja}.exe"

with open(os.path.join(folder_archiwum, "wersja_info.txt"), "w", encoding="utf-8") as f:
    f.write(f"VSVersionInfo(ffi=FixedFileInfo(filevers=({v_parts[0]},{v_parts[1]},{v_parts[2]},{v_parts[3]}), prodvers=({v_parts[0]},{v_parts[1]},{v_parts[2]},{v_parts[3]}), mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)), kids=[StringFileInfo([StringTable(u'041504b0', [StringStruct(u'CompanyName', u'Diamel'), StringStruct(u'FileDescription', u'Kalkulator Rozruchu Agregatów'), StringStruct(u'FileVersion', u'{v_str}'), StringStruct(u'OriginalFilename', u'{nazwa_stala}.exe'), StringStruct(u'ProductName', u'Kalkulator Rozruchu'), StringStruct(u'ProductVersion', u'{v_str}')])]), VarFileInfo([VarStruct(u'Translation', [1045, 1200])])])")

wzorzec = rf'(v{wersja}.*?)(?=\nv\d+\.\d+|$)'
match = re.search(wzorzec, changelog_full, re.DOTALL)
log_wersji = match.group(1).strip() if match else f"v{wersja}\nZaktualizowano."

match_db = re.search(rf'(v{wersja_bazy}.*?)(?=\nv\d+\.\d+|$)', changelog_db, re.DOTALL)
log_bazy = match_db.group(1).strip() if match_db else f"v{wersja_bazy}\nZaktualizowano."

dane_json = {
    "najnowszawersja": wersja,
    "link": f"https://diamel.pl/kalkulator_rozruchu/aplikacja/{nazwa_instalatora_exe}",
    "data": data_wydania,
    "changelog": log_wersji,
    "wersja_bazy": wersja_bazy,
    "link_bazy": "https://diamel.pl/kalkulator_rozruchu/aplikacja/data_package.zip", 
    "changelog_bazy": log_bazy
}

with open(os.path.join(sciezka_ftp_log, "wersja.json"), "w", encoding="utf-8") as f:
    json.dump(dane_json, f, ensure_ascii=False, indent=4)

if os.path.exists(folder_data):
    docelowy_data_ftp = os.path.join(sciezka_ftp_app, "data")
    if os.path.exists(docelowy_data_ftp):
        shutil.rmtree(docelowy_data_ftp)
    shutil.copytree(folder_data, docelowy_data_ftp)

print(f"⏳ Kompilacja struktury programu dla wersji {wersja}...")

cmd_icon = f'--icon="ikona.ico" --add-data "ikona.ico;."' if ikona_skopiowana else ""
cmd_zasoby = f'--add-data "{folder_zasoby};{folder_zasoby}"' if os.path.exists(folder_zasoby) else ""

cmd = (f'python -m PyInstaller --onedir --noconsole --clean {cmd_icon} '
       f'{cmd_zasoby} '
       f'--add-data "{folder_data};{folder_data}" '
       f'--version-file="wersja_info.txt" -n "{nazwa_stala}" "{plik_glowny}"')

subprocess.run(cmd, shell=True, cwd=folder_archiwum, check=True)

sciezka_folderu_dist = os.path.join(folder_archiwum, "dist", nazwa_stala)

plik_info_txt = os.path.join(folder_archiwum, "info_instalatora.txt")
with open(plik_info_txt, "w", encoding="utf-8") as f: f.write(f"KALKULATOR ROZRUCHU AGREGATÓW - DIAMEL\nWersja: {wersja}\n\n{changelog_full}")

inno_icon_line = f'SetupIconFile={os.path.abspath(os.path.join(folder_archiwum, "ikona.ico"))}' if ikona_skopiowana else ""

inno_skrypt = f"""
[Setup]
AppId=Kalkulator_Rozruchu_Diamel
AppName=Kalkulator Rozruchu
AppVersion={wersja}
AppPublisher=Diamel
DefaultDirName={{autopf}}\\Kalkulator Rozruchu
DefaultGroupName=Kalkulator Rozruchu
DisableWelcomePage=no
DisableProgramGroupPage=yes
OutputDir={os.path.abspath(sciezka_ftp_app)}
OutputBaseFilename=Instalator_Rozruchu_v{wersja}
{inno_icon_line}
Compression=lzma2/ultra
SolidCompression=yes
PrivilegesRequired=lowest
InfoBeforeFile={os.path.abspath(plik_info_txt)}

[Languages]
Name: "pl"; MessagesFile: "compiler:Languages\\Polish.isl"

[Tasks]
Name: "desktopicon"; Description: "Utwórz skrót na pulpicie"

[Files]
Source: "{os.path.abspath(sciezka_folderu_dist)}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\Kalkulator Rozruchu"; Filename: "{{app}}\\{nazwa_stala}.exe"
Name: "{{autodesktop}}\\Kalkulator Rozruchu"; Filename: "{{app}}\\{nazwa_stala}.exe"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{nazwa_stala}.exe"; Description: "Uruchom Kalkulator"; Flags: nowait postinstall skipifsilent
"""
plik_iss = os.path.join(folder_archiwum, "skrypt_instalatora.iss")
with open(plik_iss, "w", encoding="utf-8") as f: f.write(inno_skrypt)

print("📦 Kompresowanie instalatora...")
subprocess.run(f'"{inno_setup_compiler}" "{plik_iss}"', shell=True)
print(f"🚀 SUKCES! Wersja: {wersja} gotowa w folderze Paczka.")