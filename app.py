import os

from flask import Flask
from flask_login import LoginManager

from extensions import csrf, limiter
from models import db, User

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR", BASE_DIR)
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
DB_PATH = os.path.join(DATA_DIR, "site.db")
MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 Mo

DEFAULT_SETTINGS = {
    "brand_name": "Ignace Yao",
    "brand_subtitle": "SSI | SIA & Audit",
    "hero_eyebrow": "Sécurité des systèmes d'information",
    "hero_title": "Comprendre, sécuriser et auditer votre système d'information.",
    "hero_tagline": "Analyses, tutoriels et retours de terrain sur la sécurité des SI, la sécurité des environnements et l'audit de conformité.",
    "credibility": "ISO 27001 Lead Auditor|ISO 27005 Lead Implementer|15 ans de terrain",
    "about_text": "Consultant en sécurité des systèmes d'information avec 15 ans d'expérience de terrain, spécialisé en audit de conformité, sécurité des environnements et intégration sécurisée de l'IA en entreprise.",
    "contact_email": "contact@votre-domaine.fr",
    "linkedin_url": "https://www.linkedin.com/in/votre-profil",
    "youtube_url": "https://www.youtube.com/@votre-chaine",
    "footer_text": "© 2026 Ignace Yao — Sécurité IA & Sécurité et audit des systèmes d'information",
    "color_bg": "#FFFFFF",
    "color_text": "#0F1D3D",
    "color_accent": "#F5760A",
    "color_accent_2": "#0F1D3D",
    "hero_bg_image": "",
}


def create_app():
    app = Flask(__name__)

    secret_key = os.environ.get("SECRET_KEY")
    is_production = os.environ.get("FLASK_ENV") == "production"
    if not secret_key:
        if is_production:
            raise RuntimeError(
                "SECRET_KEY doit être définie en production (variable d'environnement)."
            )
        secret_key = "dev-secret-key-change-me"
    app.secret_key = secret_key

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    app.config["UPLOAD_DIR"] = UPLOAD_DIR

    # Cookies de session sécurisés
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = is_production
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True
    app.config["REMEMBER_COOKIE_SAMESITE"] = "Lax"
    app.config["REMEMBER_COOKIE_SECURE"] = is_production

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "admin.login"
    login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
    login_manager.login_message_category = "error"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from routes_public import public_bp
    from routes_admin import admin_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    with app.app_context():
        db.create_all()
        _ensure_default_settings()

    return app


def _ensure_default_settings():
    from models import SiteSetting
    existing_keys = {row.key for row in SiteSetting.query.all()}
    for key, value in DEFAULT_SETTINGS.items():
        if key not in existing_keys:
            db.session.add(SiteSetting(key=key, value=value))
    db.session.commit()


app = create_app()

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_ENV") != "production"
    app.run(debug=debug_mode, port=5000)
