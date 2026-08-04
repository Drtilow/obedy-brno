@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   Obedove menu - spousteni
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
timeout /t 3 /nobreak >nul
