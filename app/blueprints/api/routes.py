from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from ...models.quiz import QuizAttempt

api_bp = Blueprint("api", __name__)


@api_bp.route("/stats/topics")
@login_required
def topics_stats():
    topics = current_user.topics.all()
    counts = {"pending": 0, "in_progress": 0, "completed": 0}
    for t in topics:
        counts[t.status] = counts.get(t.status, 0) + 1
    return jsonify(counts)


@api_bp.route("/stats/quiz-history")
@login_required
def quiz_history():
    attempts = (
        QuizAttempt.query.filter_by(user_id=current_user.id)
        .order_by(QuizAttempt.taken_at)
        .all()
    )
    return jsonify([
        {
            "date": a.taken_at.strftime("%b %d"),
            "percentage": round((a.score / a.total_questions) * 100, 1) if a.total_questions else 0,
        }
        for a in attempts
    ])


@api_bp.route("/health")
def health():
    return jsonify({"status": "ok"})
