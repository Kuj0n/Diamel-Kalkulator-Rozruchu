# Kalkulator Rozruchu - dobór akumulatorów i ładowarek

Program na Windows do doboru akumulatorów rozruchowych i ładowarek dla agregatów prądotwórczych. Liczy spadki napięć na kablach i rozrusznikach, zapotrzebowanie prądowe, zapas CCA i zużycie pojemności, dobiera prąd ładowarki i generuje raport DOCX (PL / EN).

> Status: **wersja 2.1.0** (2026-11-04). Instalator: [Releases](../../releases/latest)

## Możliwości

- **Jeden ekran: dane i wyniki** - wyniki liczone na bieżąco podczas wpisywania, jasny / ciemny motyw (jak diamel.pl)
- **Układ 12 / 24 VDC** - rozruszniki i akumulatory z bazy lub wpisane ręcznie, połączenia szeregowe / równoległe (schemat zestawu)
- **Napięcie na rozruszniku w funkcji prądu** - spadek na kablach liczony płynnie (wykres), napięcie kręcenia i minimalne z karty rozrusznika, prąd graniczny
- **Kable i profil rozruchu** - przekroje, długości, liczba i czas prób rozruchu
- **Wyniki** - napięcie na rozruszniku, zużycie pojemności (%), CCA (informacyjnie), dobór ładowarki
- **Raport DOCX** z załącznikami (krzywe rozruszników, karty katalogowe)
- **Baza rozruszników, akumulatorów i silników** z serwera diamel.pl (edytowana w panelu administracyjnym) + własne wpisy, zgłaszanie nowego sprzętu z załącznikami
- **Automatyczna aktualizacja** programu i bazy z GitHub Releases

## Uruchomienie ze źródeł

Python 3 (Windows), zależności:

```
pip install pywebview python-docx
```

```
python aplikacja.py
```

Okno to Edge WebView2 (pywebview) z interfejsem z folderu `ui/`; `ROZRUCH_DEBUG=1` włącza narzędzia programisty (F12).

Test obliczeń (zgodność z wersją 1.2.0 + nowe funkcje): `python testy/test_obliczenia.py`

## Kompilacja

1. Podnieś `VERSION` i dopisz zmiany do `CHANGELOG` w `konfiguracja_app.py`, zrób commit.
2. `python kompilacja.py` buduje program (PyInstaller) i instalator (Inno Setup 6) do `<wersja>/Paczka/`.
3. Na pytanie o publikację odpowiedz `t` - skrypt wypchnie commit i utworzy wydanie `v<wersja>` na GitHub (wymaga [GitHub CLI](https://cli.github.com/) zalogowanego przez `gh auth login`).

## Baza urządzeń

Baza globalna (rozruszniki, akumulatory, silniki, krzywe i karty katalogowe) **nie jest w tym repozytorium** - administrator edytuje ją
w panelu administracyjnym diamel.pl (zakładka *Kalkulator Rozruchu*), a program pobiera ją w całości przy starcie
(`diamel.pl/api/rozruch.php`) - zmiana bazy nie wymaga wydania programu. Wpisy własne użytkownika są trzymane osobno
(`%APPDATA%\Diamel\Kalkulator Rozruchu\data\wlasne.json`). Pliki producentów (krzywe, karty) pobiera tylko zalogowany użytkownik
z dostępem do programu. Instalator zawiera kopię bazy z dnia kompilacji (pierwsze uruchomienie bez internetu).

## Jak działają aktualizacje programu

Program pyta `api.github.com/repos/Kuj0n/Diamel-Kalkulator-Rozruchu/releases/latest`; numer wersji to tag, lista zmian to opis wydania, instalator to załącznik `.exe`. Wydania oznaczone jako testowe (pre-release) są pomijane. Wersje 1.0.x pytają `diamel.pl/kalkulator_rozruchu/changelog/wersja.json` - serwer składa tę odpowiedź na bieżąco z GitHub.

Program nie zawiera haseł - zgłoszenia sprzętu przyjmuje `diamel.pl/api/zgloszenie.php`.

## Struktura

| Plik | Rola |
|---|---|
| `aplikacja.py` | start, okno programu |
| `interfejs.py` | funkcje wywoływane z okna: projekt, raport, aktualizacje, zgłoszenia |
| `obliczenia.py` | obliczenia układu rozruchowego (bez interfejsu) |
| `raport_docx.py` | raport DOCX (PL / EN) |
| `baza.py` | baza rozruszników i akumulatorów użytkownika (%APPDATA%), scalanie z bazą globalną |
| `ui/` | wygląd okna (HTML, CSS, JS) |
| `testy/` | test obliczeń |
| `konfiguracja_app.py` | wersja, changelog, ustawienia |
| `kompilacja.py` | budowanie wydania |

## Licencja

**Wszelkie prawa zastrzeżone** - © 2026 Diamel ([diamel.pl](https://diamel.pl)). Kod jest udostępniony wyłącznie do wglądu, szczegóły w [LICENSE](LICENSE).

Autor: **Diamel** - [diamel.pl](https://diamel.pl)
