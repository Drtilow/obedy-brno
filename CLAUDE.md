# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Účel projektu

Web aplikace, která stahuje denní obědové menu z 8 brněnských restaurací a zobrazuje je v přehledné HTML stránce s názvem **Menu v Brně**.

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
- **`index.html`** — Frontend aplikace; načítá `menu.json`, zajišťuje interaktivní filtry, vyhledávání a renderuje karty restaurací.
- **`index.html.popart.bak`** — Záloha původního komiksového Pop Art designu (ignorováno gitem).
- **`ukazky.html`** — Srovnávací přehled designových konceptů (Michelin vs. Gastro portál vs. Bib Gourmand).
- **`.github/workflows/update-menu.yml`** — GitHub Actions; spouští scraper každý den v 5:00 UTC a pushne změněný `menu.json` do repozitáře.

### Scrapovací strategie

| Restaurace | Metoda |
|---|---|
| Korzar, VIVA, U Dřeváka, Plzeňský dvůr | HTML parsování (BeautifulSoup) |
| U Primů | OCR z obrázku (pytesseract + Pillow) |
| U Nemilosrdných Bratří, Fresh Menu (Šumavská/Veveří) | PDF čtení (pdfplumber) |
| SONO Grill & Bar | HTML parsování (stránka `/obedove-menu/`) |

Při selhání scraper vrátí `{"dostupne": false, "duvod": "..."}` — chybová karta se zobrazí v UI.

---

## Frontend a Design (aktualizace listopad 2026)

Frontend prošel kompletní rekonstrukcí z původního komiksového Pop Artu na moderní portálový gastro styl:

1. **Brand & Název:**
   - Název projektu a webu: **Menu v Brně**.
   - Podtitul: *„Prohlížejte denní nabídky oblíbených brněnských restaurací URSáků“*.
   - Gastronomická ikona v zeleném kruhu s badge `Dnes`.

2. **Barevná paleta & Typografie:**
   - Svěží portálová zeleň (`#00AA6C`), mintové podbarvení (`#E8F9F2`), tmavá lesní zeleň pro texty na světlém pozadí (`#004F32`).
   - Pozadí stránky: čisté neutrální `#F2F4F8`, karty čistě bílé s jemnými linkami `#E0E0E0`.
   - Font: moderní geometrický grotesk **Plus Jakarta Sans** v kombinaci s **Inter**.

3. **Interaktivní funkce (UI/UX):**
   - **Live Search (vyhledávání v reálném čase):** fulltextové filtrování v názvech restaurací i jídel se žlutým zvýrazňováním (`<mark>`).
   - **Rychlé filtry (Pill buttons):**
     - *Vše* (kompletní nabídka)
     - *S polévkou v ceně*
     - *Bez lepku* (detekce bezlepkových jídel)
     - *Do 185 Kč* (cenový filtr)
   - **Hover animace karet:** Při najetí myší se karta restaurace plynule zvětší (`scale(1.1)`), nadzvedne (`translateY(-8px)`), získá prostorový stín a díky `z-index: 50` vystoupí před okolní karty.

4. **Karty restaurací:**
   - Hlavička s hodnocením (zelené bubliny), štítky jako *Volba hostů*, odkaz na Google Mapy pro adresu podniku.
   - Polévka oddělena do samostatného mintového banneru se štítkem `POLÉVKA`.
   - Hlavní chody přehledně číslovány s fixně zarovnanými cenami napravo a štítkem `BEZ LEPKU`.

---

## Nasazení

Stránka běží na GitHub Pages pod vlastní doménou (`CNAME` → `obedy.ondrejtrtik.cz`). GitHub Actions (`update-menu.yml`) každý den commitne a pushne přegenerovaný `menu.json` do `main` — samotné nasazení statického webu (index.html + menu.json) obstarává GitHub Pages automaticky z obsahu `main`.
