# Kalkulator Rozruchu - dobór akumulatorów i ładowarek

Program na Windows do doboru akumulatorów rozruchowych i ładowarek dla agregatów prądotwórczych. Liczy spadki napięć na kablach i rozrusznikach, zapotrzebowanie prądowe, zapas CCA i zużycie pojemności, dobiera prąd ładowarki i generuje raport DOCX (PL / EN).

> Status: **wersja 1.1.0** (2026-11-02). Instalator: [Releases](../../releases/latest)

## Możliwości

- **Dane projektowe** - projekt, klient, agregat i silnik, tabela rewizji dokumentu
- **Konfiguracja sprzętu** - rozruszniki i akumulatory z bazy lub wpisane ręcznie, połączenia szeregowe / równoległe
- **Kable i profil rozruchu** - przekroje, długości, liczba i czas prób rozruchu
- **Wyniki** - analiza CCA, spadki napięć, zużycie pojemności, dobór ładowarki
- **Raport DOCX** z załącznikami (krzywe rozruszników, karty katalogowe)
- **Baza rozruszników i akumulatorów** (`data/*.json`) - własne wpisy + scalanie z bazą globalną, zgłaszanie nowego sprzętu przez formularz na diamel.pl
- **Automatyczna aktualizacja** programu i bazy z GitHub Releases

## Uruchomienie ze źródeł

Python 3 (Windows), zależności:

```
pip install python-docx
```

```
python main.py
```

## Kompilacja

1. Podnieś `VERSION` / `DB_VERSION` i dopisz zmiany do `CHANGELOG` / `CHANGELOG_DB` w `konfiguracja_app.py`, zrób commit.
2. `python kompilacja.py` buduje program (PyInstaller) i instalator (Inno Setup 6). Pliki wydania trafiają do `<wersja>/Paczka/`: instalator, `wersja.json`, `starters.json`, `batteries.json`.
3. Na pytanie o publikację odpowiedz `t` - skrypt wypchnie commit i utworzy wydanie `v<wersja>` na GitHub (wymaga [GitHub CLI](https://cli.github.com/) zalogowanego przez `gh auth login`).

### Jak działają aktualizacje

- **Program**: pyta `api.github.com/repos/Kuj0n/Diamel-Kalkulator-Rozruchu/releases/latest`; numer wersji to tag, lista zmian to opis wydania, instalator to załącznik `.exe`. Wydania oznaczone jako testowe (pre-release) są pomijane.
- **Baza**: wersja i zmiany bazy są w załączniku `wersja.json`, dane w `starters.json` / `batteries.json`. Program porównuje wersję z polem `version` lokalnej bazy i scala nowe wpisy z własnymi.
- **Wersje 1.0.x** sprawdzają jeszcze `diamel.pl/kalkulator_rozruchu/changelog/wersja.json` - wgranie tam pliku `wersja.json` z wydania przekierowuje je do instalatora na GitHub.

Program nie zawiera haseł - zgłoszenia sprzętu przyjmuje `diamel.pl/api/zgloszenie.php`.

## Struktura

| Plik | Rola |
|---|---|
| `main.py` | start, ekran powitalny |
| `modele.py` | baza danych i obliczenia |
| `widoki.py` | interfejs (Tkinter) |
| `kontrolery.py` | logika zakładek, raport DOCX |
| `narzedzia.py` | aktualizacje, zgłaszanie sprzętu |
| `konfiguracja_app.py` | wersja, changelog, ustawienia |
| `kompilacja.py` | budowanie wydania |

## Licencja

**Wszelkie prawa zastrzeżone** - © 2026 Diamel ([diamel.pl](https://diamel.pl)). Kod jest udostępniony wyłącznie do wglądu, szczegóły w [LICENSE](LICENSE).

Autor: **Diamel** - [diamel.pl](https://diamel.pl)
