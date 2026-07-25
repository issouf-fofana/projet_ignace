import os
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from app import limiter
from models import db, User, SiteSetting, Service, Tutorial, NewsItem, Document

admin_bp = Blueprint("admin", __name__, template_folder="templates/admin")

ALLOWED_PDF_EXTENSIONS = {"pdf"}
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}


def allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def admin_required(func):
    from functools import wraps

    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)
    return wrapper


# ---------- AUTH ----------

@admin_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Connexion réussie.", "success")
            return redirect(url_for("admin.dashboard"))
        flash("Identifiants incorrects.", "error")

    return render_template("admin/login.html")


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous avez été déconnecté.", "success")
    return redirect(url_for("admin.login"))


# ---------- DASHBOARD ----------

@admin_bp.route("/")
@login_required
def dashboard():
    stats = {
        "services": Service.query.count(),
        "tutorials": Tutorial.query.count(),
        "news_items": NewsItem.query.count(),
        "documents": Document.query.count(),
        "users": User.query.count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


# ---------- SITE SETTINGS ----------

SETTINGS_FIELDS = [
    ("brand_name", "Nom affiché"),
    ("brand_subtitle", "Sous-titre (ex. SSI | SIA & Audit)"),
    ("hero_eyebrow", "Étiquette d'en-tête (hero)"),
    ("hero_title", "Titre principal (hero)"),
    ("hero_tagline", "Sous-titre (hero)"),
    ("credibility", "Badges de crédibilité (séparés par |)"),
    ("about_text", "Texte 'Qui sommes-nous ?'"),
    ("contact_email", "E-mail de contact"),
    ("linkedin_url", "URL LinkedIn"),
    ("youtube_url", "URL YouTube"),
    ("footer_text", "Texte du pied de page"),
]

COLOR_FIELDS = [
    ("color_bg", "Couleur de fond"),
    ("color_text", "Couleur du texte"),
    ("color_accent", "Couleur d'accent principale"),
    ("color_accent_2", "Couleur d'accent secondaire"),
]


def _set_setting(key, value):
    row = db.session.get(SiteSetting, key)
    if row is None:
        row = SiteSetting(key=key)
        db.session.add(row)
    row.value = value


@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        for key, _ in SETTINGS_FIELDS + COLOR_FIELDS:
            _set_setting(key, request.form.get(key, "").strip())

        hero_bg_file = request.files.get("hero_bg_image_file")
        if hero_bg_file and hero_bg_file.filename:
            if not allowed_file(hero_bg_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                flash("Format d'image non supporté pour le fond du hero (jpg, png, gif, webp).", "error")
                return redirect(url_for("admin.settings"))
            old_name = db.session.get(SiteSetting, "hero_bg_image")
            if old_name and old_name.value:
                old_path = os.path.join(current_app.config["UPLOAD_DIR"], old_name.value)
                if os.path.exists(old_path):
                    os.remove(old_path)
            original_name = secure_filename(hero_bg_file.filename)
            new_name = f"{uuid.uuid4().hex}_{original_name}"
            hero_bg_file.save(os.path.join(current_app.config["UPLOAD_DIR"], new_name))
            _set_setting("hero_bg_image", new_name)

        db.session.commit()
        flash("Paramètres du site mis à jour.", "success")
        return redirect(url_for("admin.settings"))

    rows = {row.key: row.value for row in SiteSetting.query.all()}
    return render_template("admin/settings.html", fields=SETTINGS_FIELDS, color_fields=COLOR_FIELDS, values=rows)


@admin_bp.route("/settings/hero-bg/remove", methods=["POST"])
@login_required
def settings_hero_bg_remove():
    row = db.session.get(SiteSetting, "hero_bg_image")
    if row and row.value:
        old_path = os.path.join(current_app.config["UPLOAD_DIR"], row.value)
        if os.path.exists(old_path):
            os.remove(old_path)
        row.value = ""
        db.session.commit()
        flash("Image de fond réinitialisée (fond par défaut).", "success")
    return redirect(url_for("admin.settings"))


# ---------- GENERIC CONTENT CRUD (services, news) ----------

CONTENT_MODELS = {
    "services": (Service, "Service"),
    "news": (NewsItem, "Actualité"),
}


@admin_bp.route("/content/<kind>")
@login_required
def content_list(kind):
    if kind not in CONTENT_MODELS:
        abort(404)
    model, label = CONTENT_MODELS[kind]
    items = model.query.order_by(model.position, model.id).all()
    return render_template("admin/content_list.html", items=items, kind=kind, label=label)


@admin_bp.route("/content/<kind>/new", methods=["GET", "POST"])
@login_required
def content_new(kind):
    if kind not in CONTENT_MODELS:
        abort(404)
    model, label = CONTENT_MODELS[kind]

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        position = request.form.get("position", 0, type=int)
        if not title or not description:
            flash("Le titre et la description sont obligatoires.", "error")
        else:
            item = model(title=title, description=description, position=position)
            db.session.add(item)
            db.session.commit()
            flash(f"{label} ajouté.", "success")
            return redirect(url_for("admin.content_list", kind=kind))

    return render_template("admin/content_form.html", kind=kind, label=label, item=None)


@admin_bp.route("/content/<kind>/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def content_edit(kind, item_id):
    if kind not in CONTENT_MODELS:
        abort(404)
    model, label = CONTENT_MODELS[kind]
    item = model.query.get_or_404(item_id)

    if request.method == "POST":
        item.title = request.form.get("title", "").strip()
        item.description = request.form.get("description", "").strip()
        item.position = request.form.get("position", 0, type=int)
        db.session.commit()
        flash(f"{label} mis à jour.", "success")
        return redirect(url_for("admin.content_list", kind=kind))

    return render_template("admin/content_form.html", kind=kind, label=label, item=item)


@admin_bp.route("/content/<kind>/<int:item_id>/delete", methods=["POST"])
@login_required
def content_delete(kind, item_id):
    if kind not in CONTENT_MODELS:
        abort(404)
    model, label = CONTENT_MODELS[kind]
    item = model.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash(f"{label} supprimé.", "success")
    return redirect(url_for("admin.content_list", kind=kind))


# ---------- TUTORIALS (texte + image + vidéo) ----------

@admin_bp.route("/content/tutorials")
@login_required
def tutorials_list():
    items = Tutorial.query.order_by(Tutorial.position, Tutorial.id).all()
    return render_template("admin/tutorials_list.html", items=items)


@admin_bp.route("/content/tutorials/new", methods=["GET", "POST"])
@login_required
def tutorials_new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        video_url = request.form.get("video_url", "").strip()
        position = request.form.get("position", 0, type=int)
        image_file = request.files.get("image_file")

        if not title or not description:
            flash("Le titre et la description sont obligatoires.", "error")
            return render_template("admin/tutorial_form.html", item=None)

        image_filename = None
        if image_file and image_file.filename:
            if not allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                flash("Format d'image non supporté (jpg, png, gif, webp).", "error")
                return render_template("admin/tutorial_form.html", item=None)
            original_name = secure_filename(image_file.filename)
            image_filename = f"{uuid.uuid4().hex}_{original_name}"
            image_file.save(os.path.join(current_app.config["UPLOAD_DIR"], image_filename))

        item = Tutorial(
            title=title, description=description, position=position,
            video_url=video_url or None, image_filename=image_filename,
        )
        db.session.add(item)
        db.session.commit()
        flash("Tutoriel ajouté.", "success")
        return redirect(url_for("admin.tutorials_list"))

    return render_template("admin/tutorial_form.html", item=None)


@admin_bp.route("/content/tutorials/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def tutorials_edit(item_id):
    item = Tutorial.query.get_or_404(item_id)

    if request.method == "POST":
        item.title = request.form.get("title", "").strip()
        item.description = request.form.get("description", "").strip()
        item.video_url = request.form.get("video_url", "").strip() or None
        item.position = request.form.get("position", 0, type=int)

        image_file = request.files.get("image_file")
        if image_file and image_file.filename:
            if not allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                flash("Format d'image non supporté (jpg, png, gif, webp).", "error")
                return render_template("admin/tutorial_form.html", item=item)
            old_path = os.path.join(current_app.config["UPLOAD_DIR"], item.image_filename or "")
            if item.image_filename and os.path.exists(old_path):
                os.remove(old_path)
            original_name = secure_filename(image_file.filename)
            item.image_filename = f"{uuid.uuid4().hex}_{original_name}"
            image_file.save(os.path.join(current_app.config["UPLOAD_DIR"], item.image_filename))

        db.session.commit()
        flash("Tutoriel mis à jour.", "success")
        return redirect(url_for("admin.tutorials_list"))

    return render_template("admin/tutorial_form.html", item=item)


@admin_bp.route("/content/tutorials/<int:item_id>/delete", methods=["POST"])
@login_required
def tutorials_delete(item_id):
    item = Tutorial.query.get_or_404(item_id)
    if item.image_filename:
        path = os.path.join(current_app.config["UPLOAD_DIR"], item.image_filename)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(item)
    db.session.commit()
    flash("Tutoriel supprimé.", "success")
    return redirect(url_for("admin.tutorials_list"))


# ---------- DOCUMENTS ----------

@admin_bp.route("/documents")
@login_required
def documents_list():
    docs = Document.query.order_by(Document.uploaded_at.desc()).all()
    return render_template("admin/documents.html", documents=docs)


@admin_bp.route("/documents/upload", methods=["POST"])
@login_required
def documents_upload():
    file = request.files.get("pdf_file")
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()

    if not file or file.filename == "":
        flash("Veuillez sélectionner un fichier PDF.", "error")
        return redirect(url_for("admin.documents_list"))

    if not allowed_file(file.filename, ALLOWED_PDF_EXTENSIONS):
        flash("Seuls les fichiers PDF sont acceptés.", "error")
        return redirect(url_for("admin.documents_list"))

    original_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{original_name}"
    upload_dir = current_app.config["UPLOAD_DIR"]
    file.save(os.path.join(upload_dir, unique_name))

    if not title:
        title = original_name.rsplit(".", 1)[0]

    doc = Document(title=title, description=description or None, filename=unique_name, uploaded_by_id=current_user.id)
    db.session.add(doc)
    db.session.commit()
    flash("Document ajouté avec succès.", "success")
    return redirect(url_for("admin.documents_list"))


@admin_bp.route("/documents/<int:doc_id>/edit", methods=["GET", "POST"])
@login_required
def documents_edit(doc_id):
    doc = Document.query.get_or_404(doc_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        if not title:
            flash("Le titre est obligatoire.", "error")
        else:
            doc.title = title
            doc.description = description or None
            db.session.commit()
            flash("Document mis à jour.", "success")
            return redirect(url_for("admin.documents_list"))

    return render_template("admin/document_form.html", doc=doc)


@admin_bp.route("/documents/<int:doc_id>/delete", methods=["POST"])
@login_required
def documents_delete(doc_id):
    doc = Document.query.get_or_404(doc_id)
    upload_dir = current_app.config["UPLOAD_DIR"]
    file_path = os.path.join(upload_dir, doc.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.session.delete(doc)
    db.session.commit()
    flash("Document supprimé.", "success")
    return redirect(url_for("admin.documents_list"))


# ---------- USERS (admin only) ----------

@admin_bp.route("/users")
@admin_required
def users_list():
    users = User.query.order_by(User.created_at).all()
    return render_template("admin/users.html", users=users)


@admin_bp.route("/users/new", methods=["GET", "POST"])
@admin_required
def users_new():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "editor")

        if not name or not email or not password:
            flash("Tous les champs sont obligatoires.", "error")
        elif User.query.filter_by(email=email).first():
            flash("Un utilisateur avec cet e-mail existe déjà.", "error")
        else:
            user = User(name=name, email=email, role=role if role in ("admin", "editor") else "editor")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Utilisateur créé.", "success")
            return redirect(url_for("admin.users_list"))

    return render_template("admin/user_form.html", user=None)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def users_delete(user_id):
    if user_id == current_user.id:
        flash("Vous ne pouvez pas supprimer votre propre compte.", "error")
        return redirect(url_for("admin.users_list"))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("Utilisateur supprimé.", "success")
    return redirect(url_for("admin.users_list"))
