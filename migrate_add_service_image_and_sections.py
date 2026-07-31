"""Migration ponctuelle : ajoute la colonne image_filename à la table
services, et crée la table service_sections si elles n'existent pas déjà.

Usage (dans le conteneur de prod) :
    python migrate_add_service_image_and_sections.py
"""
from sqlalchemy import text

from app import app
from models import db

with app.app_context():
    dialect = db.engine.dialect.name

    if dialect == "postgresql":
        db.session.execute(text(
            "ALTER TABLE services ADD COLUMN IF NOT EXISTS image_filename VARCHAR(300)"
        ))
    else:
        existing = [row[1] for row in db.session.execute(text("PRAGMA table_info(services)"))]
        if "image_filename" not in existing:
            db.session.execute(text("ALTER TABLE services ADD COLUMN image_filename VARCHAR(300)"))
    print("OK : services.image_filename")
    db.session.commit()

    # Crée la table service_sections si absente (create_all ne modifie jamais
    # les tables existantes, mais crée bien les tables manquantes).
    db.create_all()
    print("OK : table service_sections")

print("Migration terminée.")
