from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from ...extensions import db
from ...models.material import Material, Topic
from ...models.flashcard import Flashcard
from ...services import ai_service
from ...services.spaced_repetition import schedule_review

flashcards_bp = Blueprint("flashcards", __name__, url_prefix="/flashcards")


@flashcards_bp.route("/")
@login_required
def index():
    materials = current_user.materials.filter_by(status="ready").all()
    topics_by_material = {
        m.id: [{"id": t.id, "title": t.title} for t in m.topics.order_by(Topic.order_index).all()]
        for m in materials
    }

    topics_with_cards = (
        current_user.topics.join(Flashcard).distinct().all()
    )
    today = date.today()
    deck_summaries = []
    for topic in topics_with_cards:
        cards = topic.flashcards.all()
        due = sum(1 for c in cards if c.next_review_date <= today)
        deck_summaries.append({"topic": topic, "total": len(cards), "due": due})

    total_due = sum(d["due"] for d in deck_summaries)

    return render_template(
        "flashcards/index.html",
        materials=materials,
        topics_by_material=topics_by_material,
        deck_summaries=deck_summaries,
        total_due=total_due,
    )


@flashcards_bp.route("/generate", methods=["POST"])
@login_required
def generate():
    material_id = request.form.get("material_id")
    topic_id = request.form.get("topic_id")
    num_cards = int(request.form.get("num_cards", 10) or 10)

    material = Material.query.filter_by(id=material_id, user_id=current_user.id).first_or_404()
    topic = Topic.query.filter_by(id=topic_id, user_id=current_user.id, material_id=material.id).first_or_404()

    if not material.raw_text:
        flash("This material has no extracted text yet.", "error")
        return redirect(url_for("flashcards.index"))

    try:
        cards_data = ai_service.generate_flashcards(topic.title, material.raw_text, num_cards)
        if not cards_data:
            flash("The AI didn't return any flashcards. Try again.", "error")
            return redirect(url_for("flashcards.index"))

        for c in cards_data:
            front = (c.get("front") or "").strip()
            back = (c.get("back") or "").strip()
            if not front or not back:
                continue
            db.session.add(Flashcard(
                user_id=current_user.id,
                topic_id=topic.id,
                front=front[:2000],
                back=back[:2000],
            ))
        db.session.commit()
        flash(f"Flashcards generated for {topic.title}!", "success")
    except ai_service.AIServiceError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        flash(f"Flashcard generation failed: {exc}", "error")

    return redirect(url_for("flashcards.index"))


@flashcards_bp.route("/review")
@login_required
def review():
    topic_id = request.args.get("topic_id")
    query = Flashcard.query.filter_by(user_id=current_user.id).filter(Flashcard.next_review_date <= date.today())
    if topic_id:
        query = query.filter_by(topic_id=topic_id)
    due_cards = query.order_by(Flashcard.next_review_date).all()

    cards_json = [
        {"id": c.id, "front": c.front, "back": c.back, "topic": c.topic.title if c.topic else None}
        for c in due_cards
    ]
    return render_template("flashcards/review.html", cards_json=cards_json, count=len(due_cards))


@flashcards_bp.route("/<int:card_id>/review", methods=["POST"])
@login_required
def submit_review(card_id):
    card = Flashcard.query.filter_by(id=card_id, user_id=current_user.id).first_or_404()
    quality = int((request.json or {}).get("quality", 3))
    schedule_review(card, quality)
    db.session.commit()
    return jsonify({"ok": True, "next_review_date": card.next_review_date.isoformat()})
