import datetime
import io
import json
import os
import re
import sys

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Chybí závislosti. Nainstaluj je příkazem:")
    print("  pip install requests beautifulsoup4")
    sys.exit(1)

try:
    import pdfplumber
except ImportError:
    print("Chybí závislost pdfplumber. Nainstaluj ji příkazem:")
    print("  pip install pdfplumber")
    sys.exit(1)

try:
    import pytesseract
    from PIL import Image
except ImportError:
    print("Chybí závislosti pytesseract/Pillow. Nainstaluj je příkazem:")
    print("  pip install pytesseract pillow")
    sys.exit(1)

# Cesta k programu Tesseract OCR (samotný Python balíček pytesseract je jen obálka).
# Na Windows používáme natvrdo zadanou instalaci; jinde (např. GitHub Actions na Ubuntu,
# kde je tesseract nainstalovaný přes apt) necháme pytesseract najít binárku v PATH.
_TESSERACT_WINDOWS_CESTA = (
    r"C:\Users\trtik ondrej\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
)
if os.path.exists(_TESSERACT_WINDOWS_CESTA):
    pytesseract.pytesseract.tesseract_cmd = _TESSERACT_WINDOWS_CESTA


def stahni(url, nazev):
    """Vrátí HTML string, nebo None při jakékoliv chybě sítě / HTTP."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"  [{nazev}] HTTP {response.status_code}. Prvních 500 znaků:")
            print(f"  {response.text[:500]}")
            return None
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"  [{nazev}] Chyba sítě: {e}")
        return None


def nedostupne(nazev, duvod="Menu není dostupné"):
    return {"restaurace": nazev, "dostupne": False, "duvod": duvod}


def scrape_korzar():
    nazev = "Korzar"
    html = stahni("https://korzar.com/obedove-menu", nazev)
    if html is None:
        return nedostupne(nazev)

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="lunch-meal-items__table")
    if not table:
        print(f"  [{nazev}] Tabulka menu nenalezena. Prvních 500 znaků:")
        print(f"  {html[:500]}")
        return nedostupne(nazev)

    polozky = []
    for radek in table.find_all("tr"):
        nazev_el = radek.find("span", class_="lunch-meal-item__name")
        if not nazev_el:
            continue
        jidlo = nazev_el.get_text(strip=True)
        cena = "v ceně"
        cena_sloupec = radek.find("div", class_=lambda c: c and "is-one-quarter" in c)
        if cena_sloupec:
            cena_el = cena_sloupec.find("p", class_="has-text-right")
            if cena_el:
                text = cena_el.get_text(strip=True)
                if text:
                    cena = text
        polozky.append({"nazev": jidlo, "cena": cena})

    if not polozky:
        return nedostupne(nazev)

    return {"restaurace": nazev, "dostupne": True, "polozky": polozky}


def scrape_pizzerie_viva():
    nazev = "Pizzerie VIVA"
    html = stahni("https://pizzerie-viva.cz/", nazev)
    if html is None:
        return nedostupne(nazev)

    soup = BeautifulSoup(html, "html.parser")
    bloky = soup.find_all(
        "div",
        class_="bg-menu-gradient rounded-corners shadow-menubox menu-1 menu-same-height",
    )
    if not bloky:
        print(f"  [{nazev}] Blok s denním menu nenalezen. Prvních 500 znaků:")
        print(f"  {html[:500]}")
        return nedostupne(nazev)

    blok = bloky[0]
    h3 = blok.find("h3")
    den = h3.get_text(strip=True) if h3 else ""
    h5 = blok.find("h5")
    datum = h5.get_text(strip=True) if h5 else ""

    polozky = []
    seznam = blok.find("ul", class_="list-group")
    if seznam:
        for li in seznam.find_all("li", class_="list-group-item"):
            nazev_el = li.find("div", class_="menu-item")
            jidlo = nazev_el.get_text(strip=True) if nazev_el else ""
            if not jidlo:
                continue
            cena = "v ceně"
            cena_el = li.find("div", class_="menu-item-price")
            if cena_el:
                text = cena_el.get_text(strip=True)
                if text:
                    cena = text
            polozky.append({"nazev": jidlo, "cena": cena})

    if not polozky:
        return nedostupne(nazev)

    return {"restaurace": nazev, "dostupne": True, "den": den, "datum": datum, "polozky": polozky}


def scrape_sono():
    nazev = "SONO Grill & Bar"
    html = stahni("https://www.sonogrillbar.cz/menu/", nazev)
    if html is None:
        return nedostupne(nazev)

    dnesni_den = datetime.date.today().weekday()  # 0 = Pondělí
    if dnesni_den > 4:
        return nedostupne(nazev)

    soup = BeautifulSoup(html, "html.parser")

    # Stránka (Webnode CMS) strukturuje menu takto:
    # - každý den týdne je nadpis <h1> (Pondělí–Pátek)
    # - jídla jsou <p> elementy ve tvaru "Název  cena,-"
    DNY = {"pondělí": 0, "úterý": 1, "středa": 2, "čtvrtek": 3, "pátek": 4}
    cena_re = re.compile(r"^(.+?)\s{2,}(\d{2,4}),-\s*$")

    polozky = []
    aktualni_den = None

    for el in soup.find_all(["h1", "p"]):
        text = el.get_text(separator=" ", strip=True)
        if el.name == "h1":
            aktualni_den = DNY.get(text.lower())
        elif el.name == "p" and aktualni_den == dnesni_den:
            m = cena_re.match(text)
            if m:
                polozky.append({"nazev": m.group(1).strip(), "cena": f"{m.group(2)} Kč"})

    if not polozky:
        print(f"  [{nazev}] Žádné položky pro dnešní den nenalezeny.")
        return nedostupne(nazev)

    return {"restaurace": nazev, "dostupne": True, "polozky": polozky}


PRIMU_POLEVKA_REGEX = re.compile(r"Pol[eé]vka\s*[-–—:]?\s*(.+)$", re.IGNORECASE)
PRIMU_POLOZKA_REGEX = re.compile(r"^\s*[1-4][.)]\s*(.+)$")
# OCR obvykle nepozná dvousloupcový layout obrázku a cenu připojí rovnou
# za text jídla na stejný řádek (např. "...tatarka (a.1.3.7.10.) 154 ,-").
PRIMU_CENA_KONEC_REGEX = re.compile(r'(\d{2,4})\s*[\s,.\-;=„"]*$')


def _primu_cena_z_radku(text):
    """Rozdělí text položky na (název, cena) podle ceny na konci řádku."""
    m = PRIMU_CENA_KONEC_REGEX.search(text)
    if not m:
        return None, None
    nazev = text[: m.start()].strip().rstrip(",.-–;„\" ").strip()
    if not nazev:
        return None, None
    return nazev, m.group(1)


def scrape_u_primu():
    nazev = "U Primů"
    html = stahni("https://www.uprimu.cz/tydenni-menu/", nazev)
    if html is None:
        return nedostupne(nazev)

    soup = BeautifulSoup(html, "html.parser")

    obrazek_url = None
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if "menu" in src.lower() and re.search(r"\.jpe?g", src.lower()):
            obrazek_url = src
            break

    if not obrazek_url:
        print(f"  [{nazev}] Obrázek menu nenalezen. Prvních 500 znaků:")
        print(f"  {html[:500]}")
        return nedostupne(nazev)

    # Fallback, kdyby OCR selhalo nebo nebylo spolehlivé.
    obrazek_zaznam = {"restaurace": nazev, "dostupne": True, "typ": "obrazek", "obrazek_url": obrazek_url}

    weekday = datetime.date.today().weekday()  # 0 = Pondělí ... 6 = Neděle
    if weekday > 4:
        return nedostupne(nazev)

    try:
        obrazek_response = requests.get(obrazek_url, timeout=10)
        if obrazek_response.status_code != 200:
            print(f"  [{nazev}] Obrázek menu HTTP {obrazek_response.status_code}.")
            return obrazek_zaznam
    except requests.exceptions.RequestException as e:
        print(f"  [{nazev}] Chyba sítě při stahování obrázku: {e}")
        return obrazek_zaznam

    try:
        obrazek = Image.open(io.BytesIO(obrazek_response.content))
        text = pytesseract.image_to_string(obrazek, lang="ces")
    except Exception as e:
        print(f"  [{nazev}] OCR se nepodařilo spustit / přečíst: {e}")
        return obrazek_zaznam

    radky = text.splitlines()

    # Bezpečnostní kontrola: párování podle pořadí je spolehlivé jen tehdy, když
    # OCR najde přesně 5 "Polévka" (5 dní) — jinak by index podle dne v týdnu
    # mohl ukázat na špatný blok textu.
    polevka_indexy = [i for i, r in enumerate(radky) if PRIMU_POLEVKA_REGEX.search(r)]

    if len(polevka_indexy) != 5:
        print(
            f"  [{nazev}] OCR rozpoznávání není spolehlivé, nenalezeno přesně 5 "
            f"řádků s polévkou (nalezeno {len(polevka_indexy)})."
        )
        return nedostupne(nazev, "Dnešní menu ještě není k dispozici")

    blok_start = polevka_indexy[weekday]
    blok_konec = polevka_indexy[weekday + 1] if weekday + 1 < len(polevka_indexy) else len(radky)
    blok = radky[blok_start:blok_konec]

    polevka_nazev = PRIMU_POLEVKA_REGEX.search(blok[0]).group(1).strip()

    polozky = [{"nazev": polevka_nazev, "cena": "v ceně"}]
    for radek in blok[1:]:
        m = PRIMU_POLOZKA_REGEX.match(radek.strip())
        if not m:
            continue
        jidlo, cena = _primu_cena_z_radku(m.group(1))
        if jidlo and cena:
            polozky.append({"nazev": jidlo, "cena": f"{cena} Kč"})

    # Pro dnešní den očekáváme polévku + přesně 4 číslované položky s cenou.
    if len(polozky) != 5:
        print(
            f"  [{nazev}] OCR rozpoznávání není spolehlivé, pro dnešní den nalezeno "
            f"{len(polozky) - 1}/4 položek s cenou."
        )
        return nedostupne(nazev, "Dnešní menu se nepodařilo přečíst")

    return {"restaurace": nazev, "dostupne": True, "polozky": polozky}


DNY_V_TYDNU = {
    0: "Pondělí",
    1: "Úterý",
    2: "Středa",
    3: "Čtvrtek",
    4: "Pátek",
    5: "Sobota",
    6: "Neděle",
}
DEN_REGEX = re.compile(r"^(Pondělí|Úterý|Středa|Čtvrtek|Pátek|Sobota|Neděle):")
POLEVKA_REGEX = re.compile(r"^0,[23]l\b", re.IGNORECASE)
CENA_REGEX = re.compile(r"(\d+,-)\s*$")


def scrape_u_nemilosrdnych_bratri():
    nazev = "U Nemilosrdných Bratří"
    html = stahni("https://unemilosrdnychbratri.cz/?lang=cs", nazev)
    if html is None:
        return nedostupne(nazev)

    soup = BeautifulSoup(html, "html.parser")
    odkaz = None
    for a in soup.find_all("a"):
        if "Obědová nabídka" in a.get_text():
            odkaz = a
            break

    if not odkaz or not odkaz.get("href"):
        print(f"  [{nazev}] Odkaz na obědovou nabídku nenalezen. Prvních 500 znaků:")
        print(f"  {html[:500]}")
        return nedostupne(nazev)

    pdf_url = odkaz["href"]

    try:
        pdf_response = requests.get(pdf_url, timeout=10)
        if pdf_response.status_code != 200:
            print(f"  [{nazev}] PDF HTTP {pdf_response.status_code} ({pdf_url})")
            return nedostupne(nazev)
    except requests.exceptions.RequestException as e:
        print(f"  [{nazev}] Chyba sítě při stahování PDF: {e}")
        return nedostupne(nazev)

    try:
        with pdfplumber.open(io.BytesIO(pdf_response.content)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        print(f"  [{nazev}] PDF se nepodařilo přečíst: {e}")
        return nedostupne(nazev)

    if not text.strip():
        return nedostupne(nazev)

    dnes = DNY_V_TYDNU[datetime.date.today().weekday()]

    radky = [r.strip() for r in text.splitlines()]
    dny_v_pdf = [(i, m.group(1)) for i, r in enumerate(radky) if (m := DEN_REGEX.match(r))]

    sekce = None
    for idx, (i, den) in enumerate(dny_v_pdf):
        if den == dnes:
            start = i + 1
            konec = dny_v_pdf[idx + 1][0] if idx + 1 < len(dny_v_pdf) else len(radky)
            sekce = radky[start:konec]
            break

    if sekce is None:
        print(f"  [{nazev}] Sekce pro den '{dnes}' v PDF nenalezena.")
        return nedostupne(nazev)

    polozky = []
    polevka_najdena = False
    buffer = ""
    for radek in sekce:
        if not radek:
            continue
        if not polevka_najdena and POLEVKA_REGEX.match(radek) and not CENA_REGEX.search(radek):
            polozky.append({"nazev": radek, "cena": "v ceně"})
            polevka_najdena = True
            continue

        buffer = f"{buffer} {radek}".strip() if buffer else radek
        m = CENA_REGEX.search(buffer)
        if m:
            polozky.append({"nazev": buffer[: m.start()].strip(), "cena": m.group(1)})
            buffer = ""

    if not polozky:
        return nedostupne(nazev)

    return {"restaurace": nazev, "dostupne": True, "polozky": polozky}


FRESH_POLEVKA_REGEX = re.compile(r"^Pol[eé]vka\s*:\s*(.+)$", re.IGNORECASE)
FRESH_POLOZKA_REGEX = re.compile(r"^\s*[1-5][.)]\s*(.+)$")
FRESH_CENA_REGEX = re.compile(r"(\d+)\s*K[cč]\s*$", re.IGNORECASE)


def _fresh_cena_z_radku(text):
    """Rozdělí text položky na (název, cena) podle ceny 've tvaru "xxx Kč" na konci řádku."""
    m = FRESH_CENA_REGEX.search(text)
    if not m:
        return None, None
    nazev = text[: m.start()].strip()
    if not nazev:
        return None, None
    return nazev, m.group(1)


def scrape_fresh_menu():
    nazev = "Fresh Menu (Šumavská/Veveří)"
    html = stahni("http://www.fresh-menu.cz/", nazev)
    if html is None:
        return nedostupne(nazev)

    soup = BeautifulSoup(html, "html.parser")
    pdf_url = None
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "centrum_sumavska_veveri" in href.lower() and href.lower().endswith(".pdf"):
            pdf_url = href
            break

    if not pdf_url:
        print(f"  [{nazev}] Odkaz na týdenní menu nenalezen. Prvních 500 znaků:")
        print(f"  {html[:500]}")
        return nedostupne(nazev)

    try:
        pdf_response = requests.get(pdf_url, timeout=10)
        if pdf_response.status_code != 200:
            print(f"  [{nazev}] PDF HTTP {pdf_response.status_code} ({pdf_url})")
            return nedostupne(nazev)
    except requests.exceptions.RequestException as e:
        print(f"  [{nazev}] Chyba sítě při stahování PDF: {e}")
        return nedostupne(nazev)

    try:
        with pdfplumber.open(io.BytesIO(pdf_response.content)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        print(f"  [{nazev}] PDF se nepodařilo přečíst: {e}")
        return nedostupne(nazev)

    if not text.strip():
        return nedostupne(nazev)

    dnes = DNY_V_TYDNU[datetime.date.today().weekday()]

    radky = [r.strip() for r in text.splitlines()]
    dny_v_pdf = [(i, m.group(1)) for i, r in enumerate(radky) if (m := DEN_REGEX.match(r))]

    sekce = None
    for idx, (i, den) in enumerate(dny_v_pdf):
        if den == dnes:
            start = i + 1
            konec = dny_v_pdf[idx + 1][0] if idx + 1 < len(dny_v_pdf) else len(radky)
            sekce = radky[start:konec]
            break

    if sekce is None:
        print(f"  [{nazev}] Sekce pro den '{dnes}' v PDF nenalezena.")
        return nedostupne(nazev)

    polozky = []
    for radek in sekce:
        polevka_m = FRESH_POLEVKA_REGEX.match(radek)
        if polevka_m:
            polozky.append({"nazev": polevka_m.group(1).strip(), "cena": "v ceně"})
            continue
        polozka_m = FRESH_POLOZKA_REGEX.match(radek)
        if not polozka_m:
            continue
        jidlo, cena = _fresh_cena_z_radku(polozka_m.group(1))
        if jidlo and cena:
            polozky.append({"nazev": jidlo, "cena": f"{cena} Kč"})

    # Očekáváme polévku + přesně 5 číslovaných jídel.
    if len(polozky) != 6:
        print(
            f"  [{nazev}] Parsování PDF není spolehlivé, pro den '{dnes}' nalezeno "
            f"{max(len(polozky) - 1, 0)}/5 položek s cenou."
        )
        return nedostupne(nazev)

    return {"restaurace": nazev, "dostupne": True, "polozky": polozky}


DREVAK_HEADER_REGEX = re.compile(
    r"^(Pondělí|Úterý|Středa|Čtvrtek|Pátek|Sobota|Neděle)\b.*?Polévka:\s*(.+)$"
)
DREVAK_POLOZKA_REGEX = re.compile(r"^\d+\)\s*(.+)$")
DREVAK_CENA_REGEX = re.compile(r"(\d+)\s*$")


def scrape_u_drevaka():
    nazev = "U Dřeváka Beer&Grill"
    html = stahni("https://udrevaka.cz/menu/pages/poledni-menu", nazev)
    if html is None:
        return nedostupne(nazev)

    soup = BeautifulSoup(html, "html.parser")
    dnes = DNY_V_TYDNU[datetime.date.today().weekday()]

    polozky = None
    aktualni_den = None
    for p in soup.find_all("p"):
        text = p.get_text(" ", strip=True)

        if p.find("strong"):
            m = DREVAK_HEADER_REGEX.match(text)
            aktualni_den = m.group(1) if m else None
            if aktualni_den == dnes:
                polozky = [{"nazev": m.group(2).strip(), "cena": "v ceně"}]
            continue

        if aktualni_den != dnes or polozky is None:
            continue

        polozka_m = DREVAK_POLOZKA_REGEX.match(text)
        obsah = polozka_m.group(1) if polozka_m else text
        cena_m = DREVAK_CENA_REGEX.search(obsah)
        if not cena_m:
            continue
        polozky.append({"nazev": obsah[: cena_m.start()].strip(), "cena": cena_m.group(1)})

    if not polozky:
        print(f"  [{nazev}] Sekce pro den '{dnes}' nenalezena nebo je prázdná.")
        return nedostupne(nazev)

    return {"restaurace": nazev, "dostupne": True, "polozky": polozky}


def scrape_plzensky_dvur():
    nazev = "Plzeňský dvůr"
    html = stahni("https://plzenskydvur.cz/", nazev)
    if html is None:
        return nedostupne(nazev)

    soup = BeautifulSoup(html, "html.parser")

    jidla = []
    for div in soup.find_all("div", class_=lambda c: c and "food-item" in c):
        cat_el = div.find("div", class_="food-category")
        title_el = div.find("div", class_="food-title")
        if not cat_el or not title_el:
            continue
        oznaceni = cat_el.get_text(strip=True)
        jidlo = re.sub(r"\s+", " ", title_el.get_text(strip=True))
        if oznaceni and jidlo:
            jidla.append((oznaceni, jidlo))

    if not jidla:
        print(f"  [{nazev}] Žádné položky menu nenalezeny. Prvních 500 znaků:")
        print(f"  {html[:500]}")
        return nedostupne(nazev)

    ceny = {}
    for div in soup.find_all("div", class_="price-item"):
        cat_el = div.find("div", class_="category-title")
        price_el = div.find("div", class_="category-price")
        if cat_el and price_el:
            ceny[cat_el.get_text(strip=True)] = price_el.get_text(strip=True)

    polozky = []
    for oznaceni, jidlo in jidla:
        cena = ceny.get(oznaceni, "v ceně")
        polozky.append({"nazev": jidlo, "cena": cena})

    if not polozky:
        return nedostupne(nazev)

    polozky.sort(key=lambda p: p["cena"] != "v ceně")

    return {"restaurace": nazev, "dostupne": True, "polozky": polozky}


# --- Hlavní běh ---

scrapery = [
    scrape_korzar,
    scrape_pizzerie_viva,
    scrape_sono,
    scrape_fresh_menu,
    scrape_plzensky_dvur,
    scrape_u_nemilosrdnych_bratri,
    scrape_u_primu,
    scrape_u_drevaka,
]
vysledky = []

for scraper in scrapery:
    vysledek = scraper()
    vysledky.append(vysledek)

with open("menu.json", "w", encoding="utf-8") as f:
    json.dump(vysledky, f, ensure_ascii=False, indent=2)

print("\n--- Souhrn ---")
for v in vysledky:
    if v["dostupne"]:
        if v.get("typ") == "obrazek":
            print(f"{v['restaurace']}: obrázek menu nalezen — {v['obrazek_url']}")
        else:
            pocet = len(v.get("polozky", []))
            print(f"{v['restaurace']}: nalezeno {pocet} položek")
    else:
        print(f"{v['restaurace']}: {v['duvod']}")
