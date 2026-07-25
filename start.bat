@echo off
cd /d "%~dp0"

if not exist venv (
    echo Creation de l'environnement virtuel...
    python -m venv venv
)

echo Installation des dependances...
venv\Scripts\python.exe -m pip install --quiet --upgrade pip
venv\Scripts\python.exe -m pip install --quiet -r requirements.txt

echo.
echo Demarrage du site sur http://localhost:5000
echo (Ctrl+C pour arreter)
echo.
venv\Scripts\python.exe app.py

pause
