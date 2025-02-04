@echo off
setlocal enabledelayedexpansion

echo Automatische Einrichtung der Abhängigkeiten...
echo.

REM Erstelle Zielverzeichnisse
if not exist "Tesseract-OCR" mkdir "Tesseract-OCR"
if not exist "poppler-windows\Library\bin" mkdir "poppler-windows\Library\bin"

REM Suche nach Tesseract Installation
set "TESSERACT_FOUND="
for %%P in (
    "C:\Program Files\Tesseract-OCR"
    "C:\Program Files (x86)\Tesseract-OCR"
) do (
    if exist "%%~P\tesseract.exe" (
        echo Tesseract gefunden in: %%~P
        set "TESSERACT_PATH=%%~P"
        set "TESSERACT_FOUND=1"
        goto :found_tesseract
    )
)
:found_tesseract

if not defined TESSERACT_FOUND (
    echo Fehler: Tesseract wurde nicht gefunden!
    echo Bitte installiere Tesseract von: https://github.com/UB-Mannheim/tesseract/wiki
    pause
    exit /b 1
)

REM Kopiere Tesseract-Dateien
echo Kopiere Tesseract-Dateien...
xcopy /E /I /Y "%TESSERACT_PATH%\*.*" "Tesseract-OCR\"
if errorlevel 1 (
    echo Fehler beim Kopieren der Tesseract-Dateien!
    pause
    exit /b 1
)

REM Suche nach der spezifischen Poppler ZIP im Downloads-Ordner
set "POPPLER_ZIP=%USERPROFILE%\Downloads\Release-24.08.0-0.zip"
if not exist "%POPPLER_ZIP%" (
    echo Fehler: Poppler ZIP wurde nicht gefunden!
    echo Bitte stelle sicher, dass die Datei 'Release-24.08.0-0.zip'
    echo sich in deinem Downloads-Ordner befindet: %USERPROFILE%\Downloads
    pause
    exit /b 1
)

REM Erstelle temporäres Verzeichnis für die Extraktion
set "TEMP_DIR=%TEMP%\poppler_extract"
if exist "%TEMP_DIR%" rd /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"

REM Extrahiere Poppler ZIP
echo Extrahiere Poppler...
powershell -command "Expand-Archive -Path '%POPPLER_ZIP%' -DestinationPath '%TEMP_DIR%' -Force"
if errorlevel 1 (
    echo Fehler beim Extrahieren der Poppler-Dateien!
    pause
    exit /b 1
)

REM Kopiere Poppler-Dateien (angepasst für die neue Struktur)
echo Kopiere Poppler-Dateien...
if exist "%TEMP_DIR%\poppler-24.08.0\Library\bin" (
    xcopy /E /I /Y "%TEMP_DIR%\poppler-24.08.0\Library\bin\*" "poppler-windows\Library\bin\"
) else (
    echo Fehler: Konnte das bin-Verzeichnis in der Poppler-ZIP nicht finden!
    echo Erwarteter Pfad: %TEMP_DIR%\poppler-24.08.0\Library\bin
    echo Bitte stelle sicher, dass die richtige Poppler-Version heruntergeladen wurde.
    pause
    exit /b 1
)

REM Aufräumen
rd /s /q "%TEMP_DIR%"

echo.
echo Überprüfe die Installation...

REM Prüfe Tesseract
if exist "Tesseract-OCR\tesseract.exe" (
    echo [✓] Tesseract wurde erfolgreich installiert
) else (
    echo [X] Fehler bei der Tesseract-Installation
)

REM Prüfe Poppler
if exist "poppler-windows\Library\bin\pdfinfo.exe" (
    echo [✓] Poppler wurde erfolgreich installiert
) else (
    echo [X] Fehler bei der Poppler-Installation
)

echo.
echo Setup abgeschlossen! Du kannst jetzt main.py ausführen.
pause
