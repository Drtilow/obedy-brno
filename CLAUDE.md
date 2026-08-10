# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Účel projektu

Web aplikace, která stahuje denní obědové menu z 8 brněnských restaurací a zobrazuje je v přehledné HTML stránce.

## Spuštění

**Zobrazení uloženého menu (bez aktualizace):**
```
spustit.bat
```
Spustí Python HTTP server na portu 8000 a otevře prohlížeč.

**Stažení čerstvého menu + zobrazení:**
```
aktualizovat-menu.bat
```

**Ručně (Linux/Mac):**
```bash
python scrape_menu.py          # Stáhne menu do menu.json
python -m http.server 8000     # Server na http://localhost:8000
```

## Instalace závislostí

```bash
pip install -r requirements.txt
```

Na Windows je vyžadován i Tesseract OCR (pro OCR čtení menu U Primů). Cesta k němu je ve `scrape_menu.py` natvrdo zadaná pro cestu na tomto konkrétním počítači (`_TESSERACT_WINDOWS_CESTA`); na Linuxu (GitHub Actions) se použije `tesseract` z PATH.

Projekt nemá žádné automatizované testy ani linter — ověřování probíhá ručně: spuštění `scrape_menu.py` a kontrola výstupu v `menu.json` / v UI.

## Architektura

### Datový tok

```
scrape_menu.py → menu.json → index.html (frontend)
```

### Klíčové soubory

- **`scrape_menu.py`** — Python scraper; každá restaurace má vlastní funkci `scrape_*()`. Výstup je uložen do `menu.json`.
- **`menu.json`** — Pole objektů; každý objekt je jedna restaurace s poli `restaurace`, `dostupne`, `polozky` (název + cena).
- **`index.html`** — Jednoduchá JS aplikace; načítá `menu.json` a renderuje karty restaurací.
- **`.github/workflows/update-menu.yml`** — GitHub Actions; spouští scraper každý den v 5:00 UTC a pushne změněný `menu.json` do repozitáře.

### Scrapovací strategie

| Restaurace | Metoda |
|---|---|
| Korzar, VIVA, U Dřeváka, Plzeňský dvůr | HTML parsování (BeautifulSoup) |
| U Primů | OCR z obrázku (pytesseract + Pillow) |
| U Nemilosrdných Bratří, Fresh Menu (Šumavská/Veveří) | PDF čtení (pdfplumber) |
| SONO Grill & Bar | HTML parsování (aktuálně nedostupné) |

Při selhání scraper vrátí `{"dostupne": false, "duvod": "..."}` — chybová karta se zobrazí v UI.

### Nasazení

Stránka běží na GitHub Pages pod vlastní doménou (`CNAME` → `obedy.ondrejtrtik.cz`). GitHub Actions (`update-menu.yml`) každý den commitne a pushne přegenerovaný `menu.json` do `main` — samotné nasazení statického webu (index.html + menu.json) obstarává GitHub Pages automaticky z obsahu `main`.
