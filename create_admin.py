"""Crée ou met à jour un compte administrateur.

Usage :
    ./venv/bin/python create_admin.py email@exemple.fr "Nom Prénom" motdepasse
"""
import sys

from app import app
from models import db, User


def main():
    if len(sys.argv) != 4:
        print('Usage: python create_admin.py <email> "<nom>" <mot_de_passe>')
        sys.exit(1)

    email, name, password = sys.argv[1].strip().lower(), sys.argv[2].strip(), sys.argv[3]

    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(password)
            user.role = "admin"
            user.name = name
            print(f"Compte existant mis à jour : {email}")
        else:
            user = User(email=email, name=name, role="admin")
            user.set_password(password)
            db.session.add(user)
            print(f"Compte admin créé : {email}")
        db.session.commit()


if __name__ == "__main__":
    main()
