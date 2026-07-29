"""Migration ponctuelle : ajoute la colonne link_url aux tables
services, tutorials, news_items si elle n'existe pas déjà.

Usage (dans le conteneur de prod) :
    python migrate_add_link_url.py
"""
from sqlalchemy import text

from app import app
from models import db

TABLES = ["services", "tutorials", "news_items"]

with app.app_context():
    dialect = db.engine.dialect.name
    for table in TABLES:
        if dialect == "postgresql":
            db.session.execute(text(
                f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS link_url VARCHAR(500)"
            ))
        else:
            # SQLite : vérifie si la colonne existe déjà avant d'ajouter
            columns = [row[1] for row in db.session.execute(text(f"PRAGMA table_info({table})"))]
            if "link_url" not in columns:
                db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN link_url VARCHAR(500)"))
        print(f"OK : {table}.link_url")
    db.session.commit()

print("Migration terminée.")
