import os
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from extensions import limiter
from models import db, User, SiteSetting, Service, ServiceSection, Tutorial, NewsItem, Document

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
    ("services_title", "Titre de la section Services"),
    ("services_lead", "Texte d'intro de la section Services"),
    ("tutorials_title", "Titre de la section Tutoriels"),
    ("tutorials_lead", "Texte d'intro de la section Tutoriels"),
    ("news_title", "Titre de la section Veille Cyber & IA"),
    ("news_lead", "Texte d'intro de la section Veille Cyber & IA"),
    ("contact_title", "Titre de la section Contact"),
    ("contact_lead", "Texte d'intro de la section Contact"),
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


def _handle_setting_image_upload(setting_key, file_field_name, error_label):
    """Traite l'upload d'une image associée à une clé SiteSetting.
    Retourne True si un fichier a été traité (avec succès ou erreur), False si aucun fichier fourni.
    """
    image_file = request.files.get(file_field_name)
    if not image_file or not image_file.filename:
        return False, None

    if not allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
        return True, f"Format d'image non supporté pour {error_label} (jpg, png, gif, webp)."

    old_name = db.session.get(SiteSetting, setting_key)
    if old_name and old_name.value:
        old_path = os.path.join(current_app.config["UPLOAD_DIR"], old_name.value)
        if os.path.exists(old_path):
            os.remove(old_path)
    original_name = secure_filename(image_file.filename)
    new_name = f"{uuid.uuid4().hex}_{original_name}"
    image_file.save(os.path.join(current_app.config["UPLOAD_DIR"], new_name))
    _set_setting(setting_key, new_name)
    return True, None


@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        for key, _ in SETTINGS_FIELDS + COLOR_FIELDS:
            _set_setting(key, request.form.get(key, "").strip())

        for setting_key, file_field_name, error_label in (
            ("hero_bg_image", "hero_bg_image_file", "le fond du hero"),
            ("about_image", "about_image_file", "la photo 'à propos'"),
        ):
            handled, error = _handle_setting_image_upload(setting_key, file_field_name, error_label)
            if handled and error:
                flash(error, "error")
                return redirect(url_for("admin.settings"))

        db.session.commit()
        flash("Paramètres du site mis à jour.", "success")
        return redirect(url_for("admin.settings"))

    rows = {row.key: row.value for row in SiteSetting.query.all()}
    return render_template("admin/settings.html", fields=SETTINGS_FIELDS, color_fields=COLOR_FIELDS, values=rows)


def _remove_setting_image(setting_key, success_message):
    row = db.session.get(SiteSetting, setting_key)
    if row and row.value:
        old_path = os.path.join(current_app.config["UPLOAD_DIR"], row.value)
        if os.path.exists(old_path):
            os.remove(old_path)
        row.value = ""
        db.session.commit()
        flash(success_message, "success")
    return redirect(url_for("admin.settings"))


@admin_bp.route("/settings/hero-bg/remove", methods=["POST"])
@login_required
def settings_hero_bg_remove():
    return _remove_setting_image("hero_bg_image", "Image de fond réinitialisée (fond par défaut).")


@admin_bp.route("/settings/about-image/remove", methods=["POST"])
@login_required
def settings_about_image_remove():
    return _remove_setting_image("about_image", "Photo 'à propos' supprimée.")


# ---------- GENERIC CONTENT CRUD (news) ----------

CONTENT_MODELS = {
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
        link_url = request.form.get("link_url", "").strip()
        position = request.form.get("position", 0, type=int)
        if not title or not description:
            flash("Le titre et la description sont obligatoires.", "error")
        else:
            item = model(title=title, description=description, link_url=link_url or None, position=position)
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
        item.link_url = request.form.get("link_url", "").strip() or None
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


# ---------- SERVICES (code + fonction + livrables + valeur ajoutée) ----------

@admin_bp.route("/content/services")
@login_required
def services_list():
    items = Service.query.order_by(Service.position, Service.id).all()
    return render_template("admin/services_list.html", items=items)


def _service_form_data():
    return {
        "code": request.form.get("code", "").strip() or None,
        "function_tag": request.form.get("function_tag", "").strip() or None,
        "title": request.form.get("title", "").strip(),
        "description": request.form.get("description", "").strip(),
        "deliverables": request.form.get("deliverables", "").strip() or None,
        "value_text": request.form.get("value_text", "").strip() or None,
        "link_url": request.form.get("link_url", "").strip() or None,
        "position": request.form.get("position", 0, type=int),
    }


def _sync_service_sections(item):
    """Reconstruit les blocs personnalisés d'un service depuis les champs
    section_title[] / section_content[] du formulaire (nombre variable)."""
    titles = request.form.getlist("section_title[]")
    contents = request.form.getlist("section_content[]")

    item.sections.clear()
    position = 0
    for title, content in zip(titles, contents):
        title = title.strip()
        content = content.strip()
        if not title or not content:
            continue
        position += 1
        item.sections.append(ServiceSection(title=title, content=content, position=position))


@admin_bp.route("/content/services/new", methods=["GET", "POST"])
@login_required
def services_new():
    if request.method == "POST":
        data = _service_form_data()
        if not data["title"] or not data["description"]:
            flash("Le titre et la description sont obligatoires.", "error")
            return render_template("admin/service_form.html", item=None)

        image_file = request.files.get("image_file")
        image_filename = None
        if image_file and image_file.filename:
            if not allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                flash("Format d'image non supporté (jpg, png, gif, webp).", "error")
                return render_template("admin/service_form.html", item=None)
            original_name = secure_filename(image_file.filename)
            image_filename = f"{uuid.uuid4().hex}_{original_name}"
            image_file.save(os.path.join(current_app.config["UPLOAD_DIR"], image_filename))

        item = Service(image_filename=image_filename, **data)
        _sync_service_sections(item)
        db.session.add(item)
        db.session.commit()
        flash("Service ajouté.", "success")
        return redirect(url_for("admin.services_list"))

    return render_template("admin/service_form.html", item=None)


@admin_bp.route("/content/services/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def services_edit(item_id):
    item = Service.query.get_or_404(item_id)

    if request.method == "POST":
        data = _service_form_data()
        if not data["title"] or not data["description"]:
            flash("Le titre et la description sont obligatoires.", "error")
            return render_template("admin/service_form.html", item=item)

        image_file = request.files.get("image_file")
        if image_file and image_file.filename:
            if not allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                flash("Format d'image non supporté (jpg, png, gif, webp).", "error")
                return render_template("admin/service_form.html", item=item)
            old_path = os.path.join(current_app.config["UPLOAD_DIR"], item.image_filename or "")
            if item.image_filename and os.path.exists(old_path):
                os.remove(old_path)
            original_name = secure_filename(image_file.filename)
            data["image_filename"] = f"{uuid.uuid4().hex}_{original_name}"
            image_file.save(os.path.join(current_app.config["UPLOAD_DIR"], data["image_filename"]))

        for key, value in data.items():
            setattr(item, key, value)
        _sync_service_sections(item)
        db.session.commit()
        flash("Service mis à jour.", "success")
        return redirect(url_for("admin.services_list"))

    return render_template("admin/service_form.html", item=item)


@admin_bp.route("/content/services/<int:item_id>/delete", methods=["POST"])
@login_required
def services_delete(item_id):
    item = Service.query.get_or_404(item_id)
    if item.image_filename:
        path = os.path.join(current_app.config["UPLOAD_DIR"], item.image_filename)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(item)
    db.session.commit()
    flash("Service supprimé.", "success")
    return redirect(url_for("admin.services_list"))


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
        link_url = request.form.get("link_url", "").strip()
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
            video_url=video_url or None, link_url=link_url or None, image_filename=image_filename,
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
        item.link_url = request.form.get("link_url", "").strip() or None
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
