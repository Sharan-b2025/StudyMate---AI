import os
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from ...extensions import db
from ...models.material import Material, Topic
from ...services import file_processing, ai_service

materials_bp = Blueprint("materials", __name__, url_prefix="/materials")


@materials_bp.route("/")
@login_required
def index():
    materials = current_user.materials.order_by(Material.created_at.desc()).all()
    return render_template("materials/index.html", materials=materials)


@materials_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("Please choose a file to upload.", "error")
            return redirect(url_for("materials.upload"))

        is_allowed, ext = file_processing.allowed_file(file.filename)
        if not is_allowed:
            flash("Unsupported file type. Use PDF, DOCX, TXT, PNG or JPG.", "error")
            return redirect(url_for("materials.upload"))

        safe_name = secure_filename(file.filename)
        stored_name = f"{uuid.uuid4().hex}_{safe_name}"
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)
        file.save(filepath)

        material = Material(
            user_id=current_user.id,
            filename=stored_name,
            original_filename=safe_name,
            file_type=ext,
            status="processing",
        )
        db.session.add(material)
        db.session.commit()

        raw_text, error = file_processing.extract_text(filepath, ext)
        if error:
            material.status = "failed"
            material.error_message = error
            db.session.commit()
            flash(f"Upload saved, but extraction failed: {error}", "error")
            return redirect(url_for("materials.detail", material_id=material.id))

        material.raw_text = raw_text
        material.status = "ready"
        db.session.commit()
        flash("File uploaded and processed successfully!", "success")
        return redirect(url_for("materials.detail", material_id=material.id))

    return render_template("materials/upload.html")


@materials_bp.route("/<int:material_id>")
@login_required
def detail(material_id):
    material = Material.query.filter_by(id=material_id, user_id=current_user.id).first_or_404()
    topics = material.topics.order_by(Topic.order_index).all()
    page_count = file_processing.estimate_page_count(material.raw_text) if material.raw_text else 0
    return render_template("materials/detail.html", material=material, topics=topics, page_count=page_count)


@materials_bp.route("/<int:material_id>/simplify", methods=["POST"])
@login_required
def simplify(material_id):
    material = Material.query.filter_by(id=material_id, user_id=current_user.id).first_or_404()
    if not material.raw_text:
        return jsonify({"error": "No extracted text available."}), 400

    payload = request.get_json(silent=True) or {}
    start_page = payload.get("start_page")
    end_page = payload.get("end_page")

    if start_page and end_page:
        source_text = file_processing.get_text_for_page_range(material.raw_text, start_page, end_page)
        if not source_text.strip():
            return jsonify({"error": "No content found in that page range."}), 400
    else:
        source_text = material.raw_text

    try:
        notes = ai_service.simplify_notes(source_text)
        # Only overwrite the saved "full document" notes when the whole doc was simplified
        if not (start_page and end_page):
            material.simplified_notes = notes
            db.session.commit()
        return jsonify({"notes": notes})
    except ai_service.AIServiceError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Simplify failed: {exc}"}), 500


@materials_bp.route("/<int:material_id>/extract-topics", methods=["POST"])
@login_required
def extract_topics(material_id):
    material = Material.query.filter_by(id=material_id, user_id=current_user.id).first_or_404()
    if not material.raw_text:
        return jsonify({"error": "No extracted text available."}), 400
    try:
        topics_data = ai_service.extract_topics(material.raw_text)
    except ai_service.AIServiceError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Topic extraction failed: {exc}"}), 500

    created = []
    for idx, t in enumerate(topics_data):
        topic = Topic(
            user_id=current_user.id,
            material_id=material.id,
            title=t.get("title", "Untitled Topic")[:255],
            summary=t.get("summary", ""),
            importance=t.get("importance", "medium"),
            estimated_minutes=int(t.get("estimated_minutes", 30) or 30),
            order_index=idx,
        )
        db.session.add(topic)
        created.append(topic)
    db.session.commit()

    return jsonify({"topics": [
        {"id": t.id, "title": t.title, "importance": t.importance, "estimated_minutes": t.estimated_minutes}
        for t in created
    ]})


@materials_bp.route("/topic/<int:topic_id>/simplify", methods=["POST"])
@login_required
def simplify_topic(topic_id):
    topic = Topic.query.filter_by(id=topic_id, user_id=current_user.id).first_or_404()
    material = topic.material
    if not material or not material.raw_text:
        return jsonify({"error": "No source material available for this topic."}), 400
    try:
        notes = ai_service.simplify_topic(topic.title, material.raw_text)
        topic.simplified_content = notes
        db.session.commit()
        return jsonify({"notes": notes})
    except ai_service.AIServiceError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Simplify failed: {exc}"}), 500


@materials_bp.route("/<int:material_id>/delete", methods=["POST"])
@login_required
def delete(material_id):
    material = Material.query.filter_by(id=material_id, user_id=current_user.id).first_or_404()
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], material.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(material)
    db.session.commit()
    flash("Material deleted.", "info")
    return redirect(url_for("materials.index"))
