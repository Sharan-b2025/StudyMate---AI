from datetime import datetime, date
from ..extensions import db


class Flashcard(db.Model):
    __tablename__ = "flashcards"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"), nullable=True)
    front = db.Column(db.Text, nullable=False)
    back = db.Column(db.Text, nullable=False)

    # SM-2 spaced repetition state
    ease_factor = db.Column(db.Float, default=2.5)
    interval_days = db.Column(db.Integer, default=0)
    repetitions = db.Column(db.Integer, default=0)
    next_review_date = db.Column(db.Date, default=date.today)
    last_reviewed_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    topic = db.relationship("Topic", backref=db.backref("flashcards", lazy="dynamic", cascade="all, delete-orphan"))
