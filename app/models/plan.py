from datetime import datetime
from ..extensions import db


class StudyPlan(db.Model):
    __tablename__ = "study_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan_date = db.Column(db.Date, nullable=False)
    available_minutes = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("StudyPlanItem", backref="plan", lazy="dynamic", cascade="all, delete-orphan")


class StudyPlanItem(db.Model):
    __tablename__ = "study_plan_items"

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("study_plans.id"), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"), nullable=True)
    allocated_minutes = db.Column(db.Integer, nullable=False)
    order_index = db.Column(db.Integer, default=0)
    is_done = db.Column(db.Boolean, default=False)
    is_break = db.Column(db.Boolean, default=False)
    label = db.Column(db.String(120))  # used for break items, e.g. "Short break"
