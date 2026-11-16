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
- **`menu.json`** — Pole objektů; každý objekt je jedna restaurace s poli `restaurace`, `dostupne`, `datum` (datum stažení YYYY-MM-DD), `polozky` (název + cena).
- **`index.html`** — Frontend aplikace; načítá `menu.json`, zajišťuje interaktivní filtry, vyhledávání, víkendový režim, kontrolu stáří dat a renderuje karty restaurací.
- **`index.html.popart.bak`** — Záloha původního komiksového Pop Art designu (ignorováno gitem).
- **`ukazky.html`** — Srovnávací přehled designových konceptů (Michelin vs. Gastro portál vs. Bib Gourmand).
- **`.github/workflows/update-menu.yml`** — GitHub Actions; spouští scraper v pracovní dny ráno (06:23 a 07:41 UTC) a pushne změněný `menu.json` do repozitáře.

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

5. **iPhone / iOS App & PWA podpora:**
   - **`manifest.json`** a **`sw.js`** (Service Worker s network-first strategií a offline zálohou).
   - **Domovské ikony:** `apple-touch-icon.png` (180×180), `icon-192.png`, `icon-512.png`.
   - **iOS Standalone mód:** `apple-mobile-web-app-capable="yes"`, podpora výřezu / Dynamic Island (`viewport-fit=cover` a `env(safe-area-inset-*)`).
   - **Mobilní optimalizace:** velikost písma `16px` ve vyhledávání (zabraňuje nechtěnému auto-zoomu v iOS Safari), plynulý horizontální posun filtrů a oddělení hover efektu jen pro zařízení s myší (`@media (hover: hover)`).

---

## Nasazení

Stránka běží na GitHub Pages pod vlastní doménou (`CNAME` → `obedy.ondrejtrtik.cz`). GitHub Actions (`update-menu.yml`) každý den commitne a pushne přegenerovaný `menu.json` do `main` — samotné nasazení statického webu (index.html + menu.json) obstarává GitHub Pages automaticky z obsahu `main`.

---

## Historie změn a optimalizací (CHANGELOG)

### 16. listopadu 2026 — Oprava zpoždění stahování, víkendový režim a kontrola stáří dat

#### 1. Problém s ranním stahováním (GitHub Actions Delay)
- **Příčina:** Původní plánovač v `.github/workflows/update-menu.yml` byl nastaven na `cron: '0 5 * * *'` (05:00 UTC v celou hodinu). V tento čas spouští úlohy tisíce repozitářů najednou, což na bezplatných GitHub Actions vedlo ke zpoždění ve frontě 7 až 8,5 hodiny (workflow reálně dobíhalo až mezi 13:00 a 14:40 SEČ, tedy po obědě).
- **Důsledek o víkendu:** Poslední běh z neděle 15. 11. ve 13:37 uložil stav *"Menu není dostupné"* (protože o víkendu restaurace nevaří polední menu), a protože se pondělní ranní běh zpozdil, na webu v pondělí ráno visel stav *"nikde se nevaří"*.

#### 2. Úprava plánovače GitHub Actions (`.github/workflows/update-menu.yml`)
- **Liché minuty mimo špičku:** Čas byl posunut mimo celou hodinu a ranní špičku:
  - **1. běh:** `23 6 * * 1-5` (06:23 UTC = **07:23 SEČ v zimě** / 08:23 SELČ v létě)
  - **2. záložní běh:** `41 7 * * 1-5` (07:41 UTC = **08:41 SEČ v zimě** / 09:41 SELČ v létě)
- **Omezení na pracovní dny (`1-5`):** Workflow se nespouští v sobotu a neděli, čímž se šetří GitHub Actions minuty a víkendové běhy nepřepisují páteční data.

#### 3. Víkendový režim na frontendu (`index.html`)
- **Proč vznikl:** Aby se o víkendu návštěvníkům nezobrazovala nabídka z pátku tvářící se jako víkendové obědy.
- **Implementace:**
  - V JavaScriptu se detekuje den v týdnu (`dnes.getDay() === 0 || 6`).
  - V sobotu a v neděli web ve výchozím stavu zobrazí přehlednou víkendovou kartu:
    * *„Přejeme pohodový víkend! Brněnské restaurace o víkendu polední menu nenabízejí a vaří ze stálých lístků.“*
  - Tlačítko **„Zobrazit páteční nabídku pro inspiraci“** (nebo vyhledávání) umožňuje volitelně zobrazit nabídku z pátku s jasným modrým informačním pruhem upozorňujícím na archivní data.

#### 4. Ukládání data do `menu.json` a detekce zastaralých dat
- **`scrape_menu.py`:** Ke každé restauraci nově ukládá pole `"datum": "YYYY-MM-DD"`.
- **`index.html`:** Pokud je pracovní den (pondělí–pátek), ale data v `menu.json` neodpovídají dnešnímu dni (např. při výpadku sítě nebo státním svátku), aplikace nahoře zobrazí viditelný oranžový varovný banner:
  * *„⚠️ Upozornění: Zobrazena nabídka z [datum]. Dnešní meníčka se zatím stahují nebo je podniky ještě nezveřejnily.“*

#### 5. Aktualizace Service Workeru (`sw.js`)
- Verze cache byla zvýšena na `menu-v-brne-v2`, aby se ve všech klientských prohlížečích okamžitě načetla nová verze aplikace.

#### 6. Oprava scraperu SONO Grill & Bar (`scrape_menu.py` + `index.html`)
- **Příčina:** Webnode CMS na webu SONO vkládá názvy jídel a ceny do oddělených `<p>` a `<div>` značek (často navíc oddělených `<br>`). Původní regulární výraz hledal jídlo i cenu uvnitř jediného tagu, takže polévku a většinu hlavních chodů zahodil.
- **Oprava:** Nový parser nejprve získá ucelený text bloku pro daný den a spolehlivě páruje jídla s cenami podle struktury zakončené `Kč`. Navíc spolehlivě detekuje stav, kdy má restaurace zavřenou kuchyni (např. úterý).
- **Frontend (`index.html`):** Detekce polévky byla rozšířena tak, aby rozpoznávala i placené polévky (např. za 55 Kč u Sono) a vkládala je do horního mintového pruhu `POLÉVKA`.

---

## Zásady pro spolehlivé scrapery a prevence chyb (Best Practices)

Tato pravidla shrnují zkušenosti z provozu tohoto projektu a slouží jako návod pro psaní dalších scraperů i řešení výpadků:

### 1. Zákaz striktních kontrol typu „Všechno, nebo nic“
- **Chyba z minulosti:** Podmínky jako `if len(polozky) != 6: return nedostupne()` způsobily, že když restaurace uvařila místo 5 jídel jen 4 (nebo jedno vyprodala / byl svátek), scraper zahodil celou nabídku.
- **Pravidlo:** Vždy zobrazit raději neúplnou nabídku (např. 3 jídla) než vůbec žádnou. Selhání `nedostupne()` vracet výhradně tehdy, když je pole položek zcela prázdné.

### 2. Odolnost vůči lidskému faktoru a CMS editorům (Webnode, WordPress)
- **Chyba z minulosti:** Hledání dvojice `[název + cena]` uvnitř jediného HTML odstavce `<p>`. Když personál stiskl Shift+Enter nebo uložil cenu do vlastního odstavce, scraper jídlo nenašel.
- **Pravidlo:** 
  1. Před parsováním nahradit `<br>` znakem nového řádku `\n`.
  2. Získat ucelený text celého kontejneru dne přes `el.get_text(separator="\n")` a normalizovat nezlomitelné mezery (`\xa0` → `' '`).
  3. Regulární výrazy psát maximálně benevolentně: používat `\s*` pro libovolné mezery (pozor na chyby typu `'0,2 l'` vs `'0,2l'`), `re.IGNORECASE` a `re.DOTALL`.

### 3. OCR (čtení z obrázků) používat jen v krajní nouzi
- **Riziko:** Tesseract OCR je citlivý na změnu fontu, kontrastu, pozadí či komprese JPG. Na Linuxu (GitHub Actions) navíc funguje odlišně než lokálně na Windows.
- **Pravidlo:** Pokud podnik publikuje menu pouze jako grafický leták (sociální sítě, obrázek na webu), je stabilnější uložit a zobrazit v aplikaci přímo obrázek (`typ: "obrazek"`), než riskovat častá selhání OCR parseru.

### 4. Pravidla pro plánovač GitHub Actions (Cron)
- **Zpoždění:** Na GitHub Actions zdarma mají plánované úlohy v celou hodinu (`:00`, zejména `00:00` a `05:00` UTC) masivní zpoždění až 8 hodin.
- **Pravidlo:** 
  - Vždy plánovat na **náhodné liché minuty** (např. `23 6 * * 1-5` a `41 7 * * 1-5`).
  - Omezit cron pouze na dny, kdy se vaří (`1-5` pro pondělí až pátek). Běh o víkendu zbytečně pálí minuty a přepisuje páteční data na nedostupná.

### 5. Obranný frontend a časová razítka
- **Pravidlo:** 
  - Do `menu.json` vždy ukládat atribut `datum` (YYYY-MM-DD).
  - Frontend musí mít detekci víkendu (`dnes.getDay() === 0 || 6`), aby o víkendu nezobrazoval páteční obědy jako dnešní.
  - Frontend musí hlídat stáří dat v pracovní dny a při zpoždění scraperu uživatele jasně varovat (oranžový banner), že vidí včerejší nabídku.
