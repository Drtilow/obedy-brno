# Obědové menu

## Jak to spustit

Ve složce jsou dva soubory, na které stačí **dvakrát kliknout**:

### `spustit.bat`
Jen otevře appku s menu, které je uložené v `menu.json` z posledního stažení.
Data se **neobnovují** — pokud je `menu.json` starý, uvidíš staré menu.

### `aktualizovat-menu.bat`
Nejdřív stáhne čerstvé menu ze všech restaurací (přepíše `menu.json`) a pak appku otevře,
stejně jako `spustit.bat`. Tohle použij, když chceš vidět **aktuální** menu (typicky
jednou za den, např. ráno).

## Co se stane po kliknutí

1. Na chvíli se objeví černé okno s textem — to je normální, jen to ukazuje, co se děje
   (u `aktualizovat-menu.bat` uvidíš i průběh stahování dat). Po chvíli se **само zavře**.
2. Otevře se **druhé černé okno** s názvem "OBĚDOVÉ MENU – SERVER" — to je lokální server,
   který appce dodává data. **Tohle okno musíš nechat běžet**, dokud si menu prohlížíš.
   Pokud ho zavřeš, appka v prohlížeči přestane fungovat (dokud server znovu nespustíš).
3. Otevře se prohlížeč s appkou na adrese `http://localhost:8000/index.html`.

## Jak server vypnout

Až s appkou skončíš, jednoduše zavři to černé okno s názvem
**"OBĚDOVÉ MENU – SERVER"** (klikni na křížek, nebo do okna klikni a stiskni `Ctrl+C`,
pak potvrď `Enter`). Zavření prohlížeče samo o sobě server nevypíná.

## Předpoklady

Na počítači musí být nainstalovaný Python (příkaz `python` musí fungovat v terminálu) —
pokud fungovalo stahování menu doteď, je vše v pořádku a nemusíš nic řešit.

