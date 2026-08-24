import os
from flask import Flask, render_template, redirect, url_for
from flask_login import current_user
from .extensions import db, login_manager, migrate, cors


def create_app(config_object="app.config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    from .models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .blueprints.auth.routes import auth_bp
    from .blueprints.dashboard.routes import dashboard_bp
    from .blueprints.materials.routes import materials_bp
    from .blueprints.planner.routes import planner_bp
    from .blueprints.quiz.routes import quiz_bp
    from .blueprints.chat.routes import chat_bp
    from .blueprints.api.routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(materials_bp)
    app.register_blueprint(planner_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    upload_dir = app.config.get("UPLOAD_FOLDER")
    if upload_dir:
        os.makedirs(upload_dir, exist_ok=True)

    @app.context_processor
    def inject_globals():
        return {"app_name": "StudyMate AI"}

    @app.route("/")
    def landing():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.index"))
        return render_template("landing.html")

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app
