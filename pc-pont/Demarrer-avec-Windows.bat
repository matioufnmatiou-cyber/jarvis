@echo off
chcp 65001 >nul
rem Lance le pont Jarvis tout seul a chaque demarrage du PC (et ouvre Jarvis)
set "DEST=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Jarvis.bat"
(
  echo @echo off
  echo cd /d "%~dp0"
  echo start "Jarvis" /min python jarvis_pont.py
) > "%DEST%"
echo.
echo  C'est fait : Jarvis demarrera tout seul avec Windows.
echo  Pour arreter ca, supprime le fichier :
echo  %DEST%
echo.
pause
