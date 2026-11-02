# Kalkulator Rozruchu - dobór akumulatorów i ładowarek

Program na Windows do doboru akumulatorów rozruchowych i ładowarek dla agregatów prądotwórczych. Liczy spadki napięć na kablach i rozrusznikach, zapotrzebowanie prądowe, zapas CCA i zużycie pojemności, dobiera prąd ładowarki i generuje raport DOCX (PL / EN).

> Status: **wersja 1.0.1** (2026-10-23)

## Możliwości

- **Dane projektowe** - projekt, klient, agregat i silnik, tabela rewizji dokumentu
- **Konfiguracja sprzętu** - rozruszniki i akumulatory z bazy lub wpisane ręcznie, połączenia szeregowe / równoległe
- **Kable i profil rozruchu** - przekroje, długości, liczba i czas prób rozruchu
- **Wyniki** - analiza CCA, spadki napięć, zużycie pojemności, dobór ładowarki
- **Raport DOCX** z załącznikami (krzywe rozruszników, karty katalogowe)
- **Baza rozruszników i akumulatorów** (`data/*.json`) - własne wpisy + aktualizacja bazy globalnej z serwera, zgłaszanie nowego sprzętu e-mailem
- **Automatyczna aktualizacja** programu i bazy

## Uruchomienie ze źródeł

Python 3 (Windows), zależności:

```
pip install python-docx
```

```
python main.py
```

## Kompilacja

`python kompilacja.py` buduje program (PyInstaller) i instalator (Inno Setup 6) do folderu `<wersja>/`. Hasło SMTP i adresy e-mail do zgłoszeń skrypt wstawia z pliku `Konfiguracja/sekrety.json`, który nie jest częścią repozytorium:

```json
{
  "ENCRYPTION_KEY": "...",
  "EMAIL_NADAWCY": "...",
  "HASLO_NADAWCY": "...",
  "EMAIL_ODBIORCY": "..."
}
```

Bez tego pliku program działa, ale wysyłanie zgłoszeń sprzętu e-mailem kończy się błędem logowania SMTP.

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
