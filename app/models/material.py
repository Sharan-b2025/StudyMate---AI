from datetime import datetime
from ..extensions import db


class Material(db.Model):
    __tablename__ = "materials"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    raw_text = db.Column(db.Text)
    simplified_notes = db.Column(db.Text)
    status = db.Column(db.String(20), default="processing")  # processing, ready, failed
    error_message = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    topics = db.relationship("Topic", backref="material", lazy="dynamic", cascade="all, delete-orphan")


class Topic(db.Model):
    __tablename__ = "topics"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey("materials.id"), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.Text)
    simplified_content = db.Column(db.Text)  # AI-simplified notes for just this topic
    importance = db.Column(db.String(10), default="medium")  # high, medium, low
    estimated_minutes = db.Column(db.Integer, default=30)
    status = db.Column(db.String(20), default="pending")  # pending, in_progress, completed
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    plan_items = db.relationship("StudyPlanItem", backref="topic", lazy="dynamic")
