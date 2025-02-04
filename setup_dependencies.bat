@echo off
setlocal enabledelayedexpansion

echo Automatic setup of dependencies...
echo.

REM Create target directories
if not exist "Tesseract-OCR" mkdir "Tesseract-OCR"
if not exist "poppler-windows\Library\bin" mkdir "poppler-windows\Library\bin"

REM Search for Tesseract installation
set "TESSERACT_FOUND="
for %%P in (
    "C:\Program Files\Tesseract-OCR"
    "C:\Program Files (x86)\Tesseract-OCR"
) do (
    if exist "%%~P\tesseract.exe" (
        echo Tesseract found in: %%~P
        set "TESSERACT_PATH=%%~P"
        set "TESSERACT_FOUND=1"
        goto :found_tesseract
    )
)
:found_tesseract

if not defined TESSERACT_FOUND (
    echo Error: Tesseract not found!
    echo Please install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
    pause
    exit /b 1
)

REM Copy Tesseract files
echo Copying Tesseract files...
xcopy /E /I /Y "%TESSERACT_PATH%\*.*" "Tesseract-OCR\"
if errorlevel 1 (
    echo Error copying Tesseract files!
    pause
    exit /b 1
)

REM Search for specific Poppler ZIP in downloads folder
set "POPPLER_ZIP=%USERPROFILE%\Downloads\Release-24.08.0-0.zip"
if not exist "%POPPLER_ZIP%" (
    echo Error: Poppler ZIP not found!
    echo Please ensure that the file 'Release-24.08.0-0.zip'
    echo is in your downloads folder: %USERPROFILE%\Downloads
    pause
    exit /b 1
)

REM Create temporary directory for extraction
set "TEMP_DIR=%TEMP%\poppler_extract"
if exist "%TEMP_DIR%" rd /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"

REM Extract Poppler ZIP
echo Extracting Poppler...
powershell -command "Expand-Archive -Path '%POPPLER_ZIP%' -DestinationPath '%TEMP_DIR%' -Force"
if errorlevel 1 (
    echo Error extracting Poppler files!
    pause
    exit /b 1
)

REM Copy Poppler files (adapted for new structure)
echo Copying Poppler files...
if exist "%TEMP_DIR%\poppler-24.08.0\Library\bin" (
    xcopy /E /I /Y "%TEMP_DIR%\poppler-24.08.0\Library\bin\*" "poppler-windows\Library\bin\"
) else (
    echo Error: Could not find bin directory in Poppler ZIP!
    echo Expected path: %TEMP_DIR%\poppler-24.08.0\Library\bin
    echo Please ensure that the correct Poppler version was downloaded.
    pause
    exit /b 1
)

REM Clean up
rd /s /q "%TEMP_DIR%"

echo.
echo Checking installation...

REM Check Tesseract
if exist "Tesseract-OCR\tesseract.exe" (
    echo [✓] Tesseract installed successfully
) else (
    echo [X] Error installing Tesseract
)

REM Check Poppler
if exist "poppler-windows\Library\bin\pdfinfo.exe" (
    echo [✓] Poppler installed successfully
) else (
    echo [X] Error installing Poppler
)

echo.
echo Setup completed! You can now run main.py.
pause
