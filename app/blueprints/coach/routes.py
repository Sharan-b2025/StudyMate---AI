from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user

from ...extensions import db
from ...models.material import Topic
from ...models.chat import ChatMessage
from ...services import ai_service

coach_bp = Blueprint("coach", __name__, url_prefix="/coach")


@coach_bp.route("/<int:topic_id>")
@login_required
def index(topic_id):
    topic = Topic.query.filter_by(id=topic_id, user_id=current_user.id).first_or_404()
    history = (
        ChatMessage.query.filter_by(user_id=current_user.id, topic_id=topic.id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return render_template("coach/index.html", topic=topic, history=history)


@coach_bp.route("/<int:topic_id>/send", methods=["POST"])
@login_required
def send(topic_id):
    topic = Topic.query.filter_by(id=topic_id, user_id=current_user.id).first_or_404()
    message = ((request.json or {}).get("message") or "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    user_msg = ChatMessage(user_id=current_user.id, topic_id=topic.id, role="user", content=message)
    db.session.add(user_msg)
    db.session.commit()

    history = [
        {"role": m.role, "content": m.content}
        for m in ChatMessage.query.filter_by(user_id=current_user.id, topic_id=topic.id)
        .order_by(ChatMessage.created_at).all()
    ]

    # Ground the tutor in whatever context we have for this topic: its own
    # simplified notes first, falling back to the parent material's raw text.
    context = topic.simplified_content or ""
    if not context and topic.material and topic.material.raw_text:
        context = topic.material.raw_text

    try:
        reply = ai_service.coach_reply(history, message, topic.title, context=context)
    except ai_service.AIServiceError as exc:
        reply = f"⚠️ AI Coach is not available right now: {exc}"
    except Exception as exc:  # noqa: BLE001
        reply = f"⚠️ Something went wrong: {exc}"

    assistant_msg = ChatMessage(user_id=current_user.id, topic_id=topic.id, role="assistant", content=reply)
    db.session.add(assistant_msg)
    db.session.commit()

    return jsonify({"reply": reply})
