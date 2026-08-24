from datetime import date, datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from ...extensions import db
from ...models.material import Topic
from ...models.plan import StudyPlan, StudyPlanItem
from ...services import ai_service
from ...services.planner_service import greedy_plan, calculate_completion, week_range

planner_bp = Blueprint("planner", __name__, url_prefix="/planner")


@planner_bp.route("/")
@login_required
def index():
    topics = current_user.topics.order_by(Topic.status, Topic.importance.desc()).all()
    topics_dict = [
        {"id": t.id, "status": t.status, "importance": t.importance} for t in topics
    ]
    completion = calculate_completion(topics_dict)

    today = date.today()
    todays_plan = StudyPlan.query.filter_by(user_id=current_user.id, plan_date=today).order_by(
        StudyPlan.created_at.desc()
    ).first()

    week_days = week_range()
    week_plans = {
        d: StudyPlan.query.filter_by(user_id=current_user.id, plan_date=d).first()
        for d in week_days
    }

    return render_template(
        "planner/index.html",
        topics=topics,
        completion=completion,
        todays_plan=todays_plan,
        week_days=week_days,
        week_plans=week_plans,
    )


@planner_bp.route("/generate", methods=["POST"])
@login_required
def generate():
    available_minutes = int(request.form.get("available_minutes", 60) or 60)
    plan_date_str = request.form.get("plan_date") or date.today().isoformat()
    plan_date = datetime.strptime(plan_date_str, "%Y-%m-%d").date()

    pending_topics = current_user.topics.filter(Topic.status != "completed").all()
    topics_payload = [
        {
            "id": t.id,
            "title": t.title,
            "importance": t.importance,
            "estimated_minutes": t.estimated_minutes,
            "status": t.status,
        }
        for t in pending_topics
    ]

    if not topics_payload:
        flash("Add some topics first (upload material and extract topics).", "error")
        return redirect(url_for("planner.index"))

    try:
        plan_items_data = ai_service.generate_study_plan(topics_payload, available_minutes)
    except ai_service.AIServiceError:
        plan_items_data = greedy_plan(topics_payload, available_minutes)

    plan = StudyPlan(user_id=current_user.id, plan_date=plan_date, available_minutes=available_minutes)
    db.session.add(plan)
    db.session.flush()

    valid_ids = {t["id"] for t in topics_payload}
    for item in plan_items_data:
        topic_id = item.get("topic_id")
        if topic_id not in valid_ids:
            continue
        db.session.add(StudyPlanItem(
            plan_id=plan.id,
            topic_id=topic_id,
            allocated_minutes=int(item.get("allocated_minutes", 15) or 15),
            order_index=int(item.get("order_index", 0) or 0),
        ))

    db.session.commit()
    flash("Your optimized study plan is ready!", "success")
    return redirect(url_for("planner.index"))


@planner_bp.route("/topic/<int:topic_id>/status", methods=["POST"])
@login_required
def update_topic_status(topic_id):
    topic = Topic.query.filter_by(id=topic_id, user_id=current_user.id).first_or_404()
    new_status = request.json.get("status") if request.is_json else request.form.get("status")
    if new_status not in ("pending", "in_progress", "completed"):
        return jsonify({"error": "invalid status"}), 400
    topic.status = new_status
    if new_status == "completed":
        topic.completed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"ok": True, "status": topic.status})


@planner_bp.route("/plan-item/<int:item_id>/toggle", methods=["POST"])
@login_required
def toggle_plan_item(item_id):
    item = StudyPlanItem.query.join(StudyPlan).filter(
        StudyPlanItem.id == item_id, StudyPlan.user_id == current_user.id
    ).first_or_404()
    item.is_done = not item.is_done
    if item.is_done:
        item.topic.status = "completed"
        item.topic.completed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"ok": True, "is_done": item.is_done})
