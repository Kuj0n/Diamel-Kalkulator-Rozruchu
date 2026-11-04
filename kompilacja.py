import os
import re
import json
import subprocess
import shutil

# --- KONFIGURACJA ---
folder_zasoby = "Zasoby"
folder_data = "data" 
plik_glowny = "aplikacja.py"
pliki_modulow = ["interfejs.py", "obliczenia.py", "raport_docx.py", "baza.py", "konto.py", "konfiguracja_app.py"]
folder_ui = "ui"  # wygląd okna (HTML/CSS/JS, czcionki) - Edge WebView2 przez pywebview
plik_ikony = os.path.join(folder_zasoby, "ikona.ico")
url_bazy_serwera = "https://diamel.pl/api/rozruch.php"  # baza urządzeń z panelu administracyjnego

inno_setup_compiler = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not os.path.exists(inno_setup_compiler):
    print("❌ Błąd: Nie znaleziono kompilatora Inno Setup!")
    exit(1)

print("🔍 Analizowanie konfiguracji (Kalkulator Rozruchu)...")
with open("konfiguracja_app.py", "r", encoding="utf-8") as f:
    kod_konf = f.read()

wersja = re.search(r'VERSION\s*=\s*"([^"]+)"', kod_konf).group(1)
data_wydania = re.search(r'BUILD_DATE\s*=\s*"([^"]+)"', kod_konf).group(1)[:10]
changelog_full = re.search(r'CHANGELOG\s*=\s*"""(.*?)"""', kod_konf, re.DOTALL).group(1).strip()
github_repo = re.search(r'GITHUB_REPO\s*=\s*"([^"]+)"', kod_konf).group(1)
# Paczka = pliki wydania na GitHub (instalator). Baza urządzeń: kopia z serwera z dnia kompilacji (pierwsze
# uruchomienie bez internetu) - program pobiera aktualną bazę z panelu przy każdym starcie.
folder_archiwum = os.path.join(wersja, "Archiwum")
folder_paczka = os.path.join(wersja, "Paczka")

os.makedirs(folder_archiwum, exist_ok=True)
os.makedirs(folder_paczka, exist_ok=True)

def pobierz_baze(folder):
    """Aktualna baza z serwera (diamel.pl/api/rozruch.php) do folderu data programu - pliki starters/batteries/engines.json."""
    import urllib.request
    req = urllib.request.Request(url_bazy_serwera, data=json.dumps({"akcja": "baza"}).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "Diamel-kompilacja"})
    with urllib.request.urlopen(req, timeout=30) as odp:
        baza = json.loads(odp.read().decode("utf-8"))
    if not baza.get("ok") or not baza.get("starters"):
        raise SystemExit("❌ Serwer zwrócił niepełną bazę urządzeń - kompilacja przerwana.")
    os.makedirs(folder, exist_ok=True)
    for rodzaj in ("starters", "batteries", "engines"):
        with open(os.path.join(folder, f"{rodzaj}.json"), "w", encoding="utf-8") as f:
            json.dump({"version": str(baza["wersja"]), rodzaj: baza.get(rodzaj) or {}}, f, ensure_ascii=False, indent=4)
    print(f"🗄️  Baza urządzeń z serwera: wersja {baza['wersja']} ({len(baza['starters'])} rozruszników, "
          f"{len(baza.get('batteries') or {})} akumulatorów, {len(baza.get('engines') or {})} silników)")

print("📂 Kopiowanie rozdzielonych modułów, danych i zasobów...")
for m_plik in [plik_glowny] + pliki_modulow:
    if os.path.exists(m_plik): shutil.copy(m_plik, os.path.join(folder_archiwum, m_plik))

if os.path.exists(folder_zasoby):
    shutil.copytree(folder_zasoby, os.path.join(folder_archiwum, folder_zasoby), dirs_exist_ok=True)
shutil.copytree(folder_ui, os.path.join(folder_archiwum, folder_ui), dirs_exist_ok=True)

pobierz_baze(os.path.join(folder_archiwum, folder_data))

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

print(f"⏳ Kompilacja struktury programu dla wersji {wersja}...")

cmd_icon = f'--icon="ikona.ico" --add-data "ikona.ico;."' if ikona_skopiowana else ""
cmd_zasoby = f'--add-data "{folder_zasoby};{folder_zasoby}"' if os.path.exists(folder_zasoby) else ""

cmd = (f'python -m PyInstaller --onedir --noconsole --clean --noconfirm {cmd_icon} '
       f'{cmd_zasoby} '
       f'--add-data "{folder_data};{folder_data}" '
       f'--add-data "{folder_ui};{folder_ui}" '
       f'--collect-all webview --collect-all clr_loader --collect-all pythonnet --hidden-import clr --hidden-import docx '
       f'--hidden-import win32com.client --hidden-import pythoncom --hidden-import PIL.ImageDraw --hidden-import PIL.ImageFont '
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
OutputDir={os.path.abspath(folder_paczka)}
OutputBaseFilename=Instalator_Rozruchu_v{wersja}
{inno_icon_line}
Compression=lzma2/ultra
SolidCompression=yes
PrivilegesRequired=lowest
UninstallDisplayIcon={{app}}\\{nazwa_stala}.exe
InfoBeforeFile={os.path.abspath(plik_info_txt)}

[Languages]
Name: "pl"; MessagesFile: "compiler:Languages\\Polish.isl"

[Tasks]
Name: "desktopicon"; Description: "Utwórz skrót na pulpicie"

[InstallDelete]
; stare biblioteki (wersje 1.x: Tkinter) - folder data obok programu zostaje, program przenosi z niego bazę użytkownika
Type: filesandordirs; Name: "{{app}}\\_internal"

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
subprocess.run(f'"{inno_setup_compiler}" "{plik_iss}"', shell=True, check=True)
print(f"🚀 SUKCES! Wersja: {wersja} gotowa w folderze Paczka.")

# --- PUBLIKACJA NA GITHUB ---
odp = input(f"\n🌐 Opublikować wydanie v{wersja} na GitHub ({github_repo})? [t/N]: ").strip().lower()
if odp == "t":
    gh = shutil.which("gh") or r"C:\Program Files\GitHub CLI\gh.exe"
    if subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip():
        print("❌ Niezatwierdzone zmiany w repozytorium - najpierw commit, potem ponów publikację.")
        exit(1)
    subprocess.run(["git", "push", "origin", "HEAD"], check=True)
    subprocess.run([gh, "release", "create", f"v{wersja}", os.path.join(folder_paczka, nazwa_instalatora_exe),
                    "--repo", github_repo, "--target", "master", "--title", f"v{wersja}", "--notes", log_wersji], check=True)
    print(f"✅ Opublikowano: https://github.com/{github_repo}/releases/tag/v{wersja}")
else:
    print("Publikację pominięto. Instalator jest w folderze Paczka.")