from datetime import datetime
from ..extensions import db


class Quiz(db.Model):
    __tablename__ = "quizzes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey("materials.id"), nullable=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    difficulty = db.Column(db.String(10), default="medium")  # easy / medium / hard
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship("QuizQuestion", backref="quiz", lazy="dynamic", cascade="all, delete-orphan")
    attempts = db.relationship("QuizAttempt", backref="quiz", lazy="dynamic", cascade="all, delete-orphan")


class QuizQuestion(db.Model):
    __tablename__ = "quiz_questions"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(500))
    option_b = db.Column(db.String(500))
    option_c = db.Column(db.String(500))
    option_d = db.Column(db.String(500))
    correct_option = db.Column(db.String(1), nullable=False)  # A/B/C/D
    explanation = db.Column(db.Text)
    topic_tag = db.Column(db.String(255))


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    score = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    answers_json = db.Column(db.Text)  # JSON: {question_id: chosen_option}
    weak_topics_json = db.Column(db.Text)  # JSON list of topic tags answered wrong
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)
