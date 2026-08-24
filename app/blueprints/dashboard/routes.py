from flask import Blueprint, render_template
from flask_login import login_required, current_user

from ...models.material import Topic, Material
from ...models.quiz import QuizAttempt
from ...services.planner_service import calculate_completion

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def index():
    topics = [
        {"status": t.status, "importance": t.importance}
        for t in current_user.topics
    ]
    completion = calculate_completion(topics)

    total_topics = len(topics)
    completed = sum(1 for t in topics if t["status"] == "completed")
    in_progress = sum(1 for t in topics if t["status"] == "in_progress")
    pending = total_topics - completed - in_progress

    materials_count = current_user.materials.count()

    attempts = current_user.quizzes.join(QuizAttempt).count() if False else None
    recent_attempts = (
        QuizAttempt.query.filter_by(user_id=current_user.id)
        .order_by(QuizAttempt.taken_at.desc())
        .limit(5)
        .all()
    )
    avg_score = 0
    if recent_attempts:
        pct = [
            (a.score / a.total_questions * 100) if a.total_questions else 0
            for a in recent_attempts
        ]
        avg_score = round(sum(pct) / len(pct), 1)

    recent_materials = current_user.materials.order_by(Material.created_at.desc()).limit(5).all()

    return render_template(
        "dashboard/index.html",
        completion=completion,
        total_topics=total_topics,
        completed=completed,
        in_progress=in_progress,
        pending=pending,
        materials_count=materials_count,
        avg_score=avg_score,
        recent_attempts=recent_attempts,
        recent_materials=recent_materials,
    )
