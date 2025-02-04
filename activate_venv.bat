@echo off
IF NOT EXIST venv (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created!
)
call venv\Scripts\activate
echo Virtual environment activated!
IF NOT EXIST venv\Scripts\pip.exe (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo Dependencies installed!
)
