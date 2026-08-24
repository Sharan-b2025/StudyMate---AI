import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _database_url():
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        # Render/Heroku give postgres:// -> SQLAlchemy 1.4+/2.x wants postgresql://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    # Local fallback
    sqlite_path = os.path.join(BASE_DIR, "instance", "studymate.db")
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    return f"sqlite:///{sqlite_path}"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "instance", "uploads")
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "png", "jpg", "jpeg"}

    REMEMBER_COOKIE_DURATION = timedelta(days=14)

    # AI provider abstraction
    AI_PROVIDER = os.environ.get("AI_PROVIDER", "gemini")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

    TESSERACT_CMD = os.environ.get("TESSERACT_CMD", "")
