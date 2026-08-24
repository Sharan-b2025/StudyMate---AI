"""
Flask CLI entrypoint — enables `flask db migrate`, `flask db upgrade`, etc.
Usage:
    export FLASK_APP=manage.py
    flask db init
    flask db migrate -m "initial"
    flask db upgrade
"""
from dotenv import load_dotenv
load_dotenv()

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app import models  # noqa: E402,F401  (ensures models are registered)

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {"db": db, **{name: getattr(models, name) for name in models.__all__}}
