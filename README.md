# Kalkulator Rozruchu - dobór akumulatorów i ładowarek

Program na Windows do doboru akumulatorów rozruchowych i ładowarek dla agregatów prądotwórczych. Liczy spadki napięć na kablach i rozrusznikach, zapotrzebowanie prądowe, zapas CCA i zużycie pojemności, dobiera prąd ładowarki i generuje raport DOCX (PL / EN).

> Status: **wersja 1.2.0** (2026-11-02). Instalator: [Releases](../../releases/latest)

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

1. Podnieś `VERSION` i dopisz zmiany do `CHANGELOG` w `konfiguracja_app.py`, zrób commit.
2. `python kompilacja.py` buduje program (PyInstaller) i instalator (Inno Setup 6) do `<wersja>/Paczka/`.
3. Na pytanie o publikację odpowiedz `t` - skrypt wypchnie commit i utworzy wydanie `v<wersja>` na GitHub (wymaga [GitHub CLI](https://cli.github.com/) zalogowanego przez `gh auth login`).

## Baza urządzeń

Baza globalna to pliki [`data/starters.json`](data/starters.json) i [`data/batteries.json`](data/batteries.json); wersja i historia zmian są w [`data/wersja_bazy.json`](data/wersja_bazy.json). Program porównuje wersję z polem `version` lokalnej bazy i proponuje scalenie nowych wpisów z własnymi.

Aktualizacja bazy **bez wydawania nowej wersji programu**:

1. Edytuj `data/starters.json` / `data/batteries.json`.
2. W `data/wersja_bazy.json` podnieś `version` i dopisz wpis na początku `changelog`, np. `"v1.1.1 (2026-11-10)\n- Dodano ...\n\n"` + poprzednia historia.
3. Commit + push do `master`. Programy zaproponują aktualizację przy następnym uruchomieniu (GitHub odświeża pliki do 5 minut).

## Jak działają aktualizacje programu

Program pyta `api.github.com/repos/Kuj0n/Diamel-Kalkulator-Rozruchu/releases/latest`; numer wersji to tag, lista zmian to opis wydania, instalator to załącznik `.exe`. Wydania oznaczone jako testowe (pre-release) są pomijane. Wersje 1.0.x pytają `diamel.pl/kalkulator_rozruchu/changelog/wersja.json` - serwer składa tę odpowiedź na bieżąco z GitHub.

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
