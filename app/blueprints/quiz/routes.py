import json
import re
from collections import Counter

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from ...extensions import db
from ...models.material import Material, Topic
from ...models.quiz import Quiz, QuizQuestion, QuizAttempt
from ...services import ai_service

quiz_bp = Blueprint("quiz", __name__, url_prefix="/quiz")


@quiz_bp.route("/")
@login_required
def index():
    quizzes = current_user.quizzes.order_by(Quiz.created_at.desc()).all()
    materials = current_user.materials.filter_by(status="ready").all()

    # Topics grouped by material, embedded as JSON for the topic dropdown to
    # populate itself client-side when a material is selected.
    topics_by_material = {
        m.id: [{"id": t.id, "title": t.title} for t in m.topics.order_by(Topic.order_index).all()]
        for m in materials
    }

    attempts = QuizAttempt.query.filter_by(user_id=current_user.id).all()
    weak_topic_counter = Counter()
    for a in attempts:
        for topic in json.loads(a.weak_topics_json or "[]"):
            weak_topic_counter[topic] += 1
    weak_topics = weak_topic_counter.most_common(5)

    return render_template(
        "quiz/index.html",
        quizzes=quizzes,
        materials=materials,
        weak_topics=weak_topics,
        topics_by_material=topics_by_material,
    )


def _sanitize_option(text, max_len):
    return (text or "").strip()[:max_len]


def _sanitize_correct_option(value):
    match = re.search(r"[A-Da-d]", value or "A")
    return match.group(0).upper() if match else "A"


@quiz_bp.route("/generate", methods=["POST"])
@login_required
def generate():
    material_id = request.form.get("material_id")
    topic_id = request.form.get("topic_id") or None
    num_questions = int(request.form.get("num_questions", 5) or 5)

    material = Material.query.filter_by(id=material_id, user_id=current_user.id).first_or_404()
    if not material.raw_text:
        flash("This material has no extracted text yet.", "error")
        return redirect(url_for("quiz.index"))

    topic = None
    if topic_id:
        topic = Topic.query.filter_by(id=topic_id, user_id=current_user.id, material_id=material.id).first()

    try:
        if topic:
            questions_data = ai_service.generate_quiz_for_topic(topic.title, material.raw_text, num_questions)
        else:
            questions_data = ai_service.generate_quiz(material.raw_text, num_questions)

        if not questions_data:
            flash("The AI didn't return any questions. Try again.", "error")
            return redirect(url_for("quiz.index"))

        title = f"Quiz: {topic.title}" if topic else f"Quiz: {material.original_filename}"
        quiz = Quiz(user_id=current_user.id, material_id=material.id, title=title)
        db.session.add(quiz)
        db.session.flush()

        for q in questions_data:
            db.session.add(QuizQuestion(
                quiz_id=quiz.id,
                question_text=_sanitize_option(q.get("question_text"), 2000),
                option_a=_sanitize_option(q.get("option_a"), 500),
                option_b=_sanitize_option(q.get("option_b"), 500),
                option_c=_sanitize_option(q.get("option_c"), 500),
                option_d=_sanitize_option(q.get("option_d"), 500),
                correct_option=_sanitize_correct_option(q.get("correct_option")),
                explanation=_sanitize_option(q.get("explanation"), 2000),
                topic_tag=_sanitize_option(q.get("topic_tag") or (topic.title if topic else ""), 255),
            ))
        db.session.commit()
        flash("Quiz generated!", "success")
        return redirect(url_for("quiz.take", quiz_id=quiz.id))

    except ai_service.AIServiceError as exc:
        db.session.rollback()
        flash(str(exc), "error")
        return redirect(url_for("quiz.index"))
    except Exception as exc:  # noqa: BLE001 - never let quiz generation 500 the page
        db.session.rollback()
        flash(f"Quiz generation failed: {exc}", "error")
        return redirect(url_for("quiz.index"))


@quiz_bp.route("/<int:quiz_id>/take")
@login_required
def take(quiz_id):
    quiz = Quiz.query.filter_by(id=quiz_id, user_id=current_user.id).first_or_404()
    questions = quiz.questions.all()
    return render_template("quiz/take.html", quiz=quiz, questions=questions)


@quiz_bp.route("/<int:quiz_id>/submit", methods=["POST"])
@login_required
def submit(quiz_id):
    quiz = Quiz.query.filter_by(id=quiz_id, user_id=current_user.id).first_or_404()
    questions = quiz.questions.all()

    answers = {}
    score = 0
    weak_topics = []
    for q in questions:
        chosen = request.form.get(f"question_{q.id}")
        answers[q.id] = chosen
        if chosen and chosen.upper() == q.correct_option:
            score += 1
        elif q.topic_tag:
            weak_topics.append(q.topic_tag)

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
        score=score,
        total_questions=len(questions),
        answers_json=json.dumps(answers),
        weak_topics_json=json.dumps(weak_topics),
    )
    db.session.add(attempt)
    db.session.commit()

    return redirect(url_for("quiz.result", attempt_id=attempt.id))


@quiz_bp.route("/result/<int:attempt_id>")
@login_required
def result(attempt_id):
    attempt = QuizAttempt.query.filter_by(id=attempt_id, user_id=current_user.id).first_or_404()
    quiz = attempt.quiz
    questions = quiz.questions.all()
    answers = json.loads(attempt.answers_json or "{}")
    return render_template("quiz/result.html", attempt=attempt, quiz=quiz, questions=questions, answers=answers)
