@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   Obedove menu - aktualizace dat + spusteni
echo ============================================
echo.
echo Stahuji cerstve menu ze vsech restauraci (chvili to muze trvat)...
echo Otevira se k tomu samostatne okno - az se sama zavre, pokracujeme dal.
echo.

start /wait "Aktualizace dat - pockej, az se toto okno zavre" cmd /c python scrape_menu.py

echo.
echo ============================================
echo Data v menu.json jsou aktualni.
echo ============================================
echo.
echo Spoustim lokalni server...

start "OBEDOVE MENU - SERVER (nezavirej dokud appku pouzivas)" cmd /k python -m http.server 8000

timeout /t 2 /nobreak >nul

echo Otevirem appku v prohlizeci...
start http://localhost:8000/index.html

echo.
echo Hotovo. Toto okno se za chvili samo zavre.
echo Server bezi v druhem okne - nezavirej ho, dokud appku prohlizis.
timeout /t 4 /nobreak >nul
