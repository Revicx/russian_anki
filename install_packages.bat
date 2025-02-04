@echo off
echo Installing Python packages...

REM Aktiviere die virtuelle Umgebung
call venv\Scripts\activate

REM Installiere die Pakete
pip install -r requirements.txt

echo.
echo Installation abgeschlossen!
echo Du kannst jetzt main.py ausführen.
pause
