from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from ...extensions import db
from ...models.chat import ChatMessage
from ...models.material import Material
from ...services import ai_service

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.route("/")
@login_required
def index():
    history = current_user.chat_messages.order_by(ChatMessage.created_at).all()
    return render_template("chat/index.html", history=history)


@chat_bp.route("/send", methods=["POST"])
@login_required
def send():
    message = (request.json.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    user_msg = ChatMessage(user_id=current_user.id, role="user", content=message)
    db.session.add(user_msg)
    db.session.commit()

    history = [
        {"role": m.role, "content": m.content}
        for m in current_user.chat_messages.order_by(ChatMessage.created_at).all()
    ]

    context = ""
    latest_material = current_user.materials.filter_by(status="ready").order_by(Material.created_at.desc()).first()
    if latest_material and latest_material.raw_text:
        context = latest_material.raw_text

    try:
        reply = ai_service.chat_reply(history, message, context=context)
    except ai_service.AIServiceError as exc:
        reply = f"⚠️ AI assistant is not available right now: {exc}"

    assistant_msg = ChatMessage(user_id=current_user.id, role="assistant", content=reply)
    db.session.add(assistant_msg)
    db.session.commit()

    return jsonify({"reply": reply})
