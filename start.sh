#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "Création de l'environnement virtuel..."
  python3 -m venv venv
fi

echo "Installation des dépendances..."
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet -r requirements.txt

echo ""
echo "Démarrage du site sur http://localhost:5000"
echo "(Ctrl+C pour arrêter)"
echo ""
./venv/bin/python app.py
