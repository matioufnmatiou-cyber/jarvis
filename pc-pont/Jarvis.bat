@echo off
chcp 65001 >nul
title Pont PC de Jarvis
cd /d "%~dp0"
where python >nul 2>&1
if errorlevel 1 (
  echo.
  echo  Python n'est pas installe. Le Microsoft Store va s'ouvrir :
  echo  clique sur "Obtenir", attends la fin, puis relance Jarvis.bat
  echo.
  start "" "ms-windows-store://pdp/?productid=9NCVDN91XZQP"
  pause
  exit /b
)
echo  Jarvis prend le controle du PC... Laisse cette fenetre ouverte (tu peux la reduire).
python jarvis_pont.py
pause
