"""Migration ponctuelle : ajoute les colonnes code, function_tag,
deliverables, value_text à la table services si elles n'existent pas déjà.

Usage (dans le conteneur de prod) :
    python migrate_add_service_fields.py
"""
from sqlalchemy import text

from app import app
from models import db

COLUMNS = [
    ("code", "VARCHAR(20)"),
    ("function_tag", "VARCHAR(120)"),
    ("deliverables", "TEXT"),
    ("value_text", "TEXT"),
]

with app.app_context():
    dialect = db.engine.dialect.name
    for column, col_type in COLUMNS:
        if dialect == "postgresql":
            db.session.execute(text(
                f"ALTER TABLE services ADD COLUMN IF NOT EXISTS {column} {col_type}"
            ))
        else:
            existing = [row[1] for row in db.session.execute(text("PRAGMA table_info(services)"))]
            if column not in existing:
                db.session.execute(text(f"ALTER TABLE services ADD COLUMN {column} {col_type}"))
        print(f"OK : services.{column}")
    db.session.commit()

print("Migration terminée.")
