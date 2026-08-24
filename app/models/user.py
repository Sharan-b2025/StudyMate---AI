from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    daily_goal_minutes = db.Column(db.Integer, default=120)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    materials = db.relationship("Material", backref="owner", lazy="dynamic", cascade="all, delete-orphan")
    topics = db.relationship("Topic", backref="owner", lazy="dynamic", cascade="all, delete-orphan")
    plans = db.relationship("StudyPlan", backref="owner", lazy="dynamic", cascade="all, delete-orphan")
    quizzes = db.relationship("Quiz", backref="owner", lazy="dynamic", cascade="all, delete-orphan")
    chat_messages = db.relationship("ChatMessage", backref="owner", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
