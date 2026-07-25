import os
import re

from flask import Blueprint, render_template, send_from_directory, abort, current_app
from werkzeug.utils import secure_filename

from models import SiteSetting, Service, Tutorial, NewsItem, Document

public_bp = Blueprint("public", __name__)

YOUTUBE_RE = re.compile(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/))([\w-]{11})")
VIMEO_RE = re.compile(r"vimeo\.com/(\d+)")


def to_embed_url(video_url):
    if not video_url:
        return None
    match = YOUTUBE_RE.search(video_url)
    if match:
        return f"https://www.youtube.com/embed/{match.group(1)}"
    match = VIMEO_RE.search(video_url)
    if match:
        return f"https://player.vimeo.com/video/{match.group(1)}"
    return None


def get_settings():
    rows = SiteSetting.query.all()
    settings = {row.key: row.value for row in rows}
    settings["credibility_list"] = (settings.get("credibility") or "").split("|") if settings.get("credibility") else []
    return settings


@public_bp.route("/")
def index():
    settings = get_settings()
    services = Service.query.order_by(Service.position, Service.id).all()
    tutorials = Tutorial.query.order_by(Tutorial.position, Tutorial.id).all()
    news_items = NewsItem.query.order_by(NewsItem.position, NewsItem.id).all()
    return render_template(
        "index.html",
        settings=settings,
        services=services,
        tutorials=tutorials,
        news_items=news_items,
        to_embed_url=to_embed_url,
    )


@public_bp.route("/documents")
def documents():
    settings = get_settings()
    docs = Document.query.order_by(Document.uploaded_at.desc()).all()
    return render_template("documents.html", documents=docs, settings=settings)


@public_bp.route("/documents/view/<int:doc_id>")
def view_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    safe_name = secure_filename(doc.filename)
    upload_dir = current_app.config["UPLOAD_DIR"]
    if safe_name != doc.filename or not os.path.exists(os.path.join(upload_dir, safe_name)):
        abort(404)
    response = send_from_directory(upload_dir, safe_name, mimetype="application/pdf")
    response.headers["Content-Disposition"] = "inline"
    return response


@public_bp.route("/documents/<int:doc_id>")
def document_detail(doc_id):
    settings = get_settings()
    doc = Document.query.get_or_404(doc_id)
    return render_template("document_detail.html", doc=doc, settings=settings)
