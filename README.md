# 🎓 StudyMate AI

An AI-powered study management web app. Upload your syllabus/notes, tell the AI how
much time you have, and get an optimized study plan, simplified notes, adaptive
progress tracking, auto-generated quizzes, and an AI study assistant — all in one
clean dashboard.

Built with **Flask + Jinja2 + vanilla JS** (no frontend framework) and **Gemini AI**.

---

## ✨ Phase 1 (this build) — Core Platform

- Auth (register/login/logout) with Flask-Login
- Upload PDF / DOCX / TXT / PNG / JPG, text extraction (+ OCR for images)
- AI note simplification (dense material → short, clear notes)
- AI topic/chapter extraction from syllabus material
- "I have X minutes" → AI-optimized study plan (with deterministic fallback planner
  if the AI is unavailable, so the app never breaks)
- Topic status tracking (pending / in progress / completed) + live completion %
- Daily plan + weekly timetable view
- AI-generated quizzes from your own material, with weak-topic tracking
- AI study assistant chat, grounded in your uploaded material
- Dashboard with Chart.js visualizations

### Roadmap (Phase 2+)
See the landing page (`/`) for the full visual roadmap: gamification & streaks,
smart notifications & calendar sync, deeper analytics, public API & mobile PWA.

---

## 🗂 Project Structure

```
studymate-ai/
├── app/
│   ├── __init__.py          # app factory
│   ├── config.py            # env-driven config (SQLite ↔ Postgres auto-switch)
│   ├── extensions.py        # db, login_manager, migrate, cors
│   ├── models/               # User, Material, Topic, StudyPlan, Quiz, ChatMessage
│   ├── blueprints/
│   │   ├── auth/             # register/login/logout
│   │   ├── dashboard/        # stats dashboard
│   │   ├── materials/        # upload, extraction, simplify, topic extraction
│   │   ├── planner/          # plan generation, topic/plan tracking
│   │   ├── quiz/              # quiz generation, taking, results
│   │   ├── chat/              # AI assistant
│   │   └── api/                # JSON endpoints for charts
│   ├── services/
│   │   ├── ai_service.py     # Gemini abstraction — swap providers here only
│   │   ├── file_processing.py# PDF/DOCX/TXT/OCR extraction
│   │   └── planner_service.py# fallback greedy planner, completion calc
│   ├── templates/            # Jinja2 templates
│   └── static/                # css/js (no build step needed)
├── manage.py                  # `flask db` CLI entrypoint
├── wsgi.py                    # app entrypoint / local dev runner
├── requirements.txt
├── Procfile                   # gunicorn start command
├── render.yaml                # Render one-click blueprint
└── .env.example
```

---

## 🚀 Local Setup

```bash
git clone <your-repo-url>
cd studymate-ai
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env            # then fill in GEMINI_API_KEY

export FLASK_APP=manage.py      # Windows: set FLASK_APP=manage.py
flask db init
flask db migrate -m "initial"
flask db upgrade

python wsgi.py                  # runs on http://localhost:5000
```

No `DATABASE_URL` set → the app automatically uses a local SQLite file at
`instance/studymate.db`. Set `DATABASE_URL` to a PostgreSQL connection string to
switch to Postgres (this is done automatically on Render).

**OCR (image uploads)** requires the `tesseract` binary installed on your system:
- macOS: `brew install tesseract`
- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
- Windows: install from the [tesseract-ocr wiki](https://github.com/UB-Mannheim/tesseract/wiki) and set `TESSERACT_CMD` in `.env`

---

## ☁️ Deploy to Render (GitHub → Render, no local tooling needed)

1. **Push this project to a new GitHub repository** (see commands below).
2. Go to [render.com](https://render.com) → **New → Blueprint** → connect your GitHub repo.
   Render will read `render.yaml` and provision both the web service and a free
   PostgreSQL database automatically.
3. In the Render dashboard, open the new web service → **Environment** → set:
   - `GEMINI_API_KEY` — get one free at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
4. Click **Deploy**. Render runs `flask db upgrade` automatically before each start
   (see `startCommand` in `render.yaml`), so your schema is always current.

If you'd rather deploy manually (no `render.yaml`):
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `flask db upgrade && gunicorn wsgi:app --bind 0.0.0.0:$PORT`
- Add env vars: `FLASK_APP=manage.py`, `SECRET_KEY`, `DATABASE_URL` (attach a Postgres
  instance), `GEMINI_API_KEY`, `AI_PROVIDER=gemini`.

> Note: Render's native Python environment may not have `tesseract-ocr`
> preinstalled — image OCR uploads may not work out of the box on the free tier.
> All other features (PDF/DOCX/TXT, planning, quizzes, chat) work with zero extra setup.

---

## 📤 Push to GitHub

```bash
cd studymate-ai
git init
git add .
git commit -m "StudyMate AI — Phase 1: core platform"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

Then follow the **Deploy to Render** steps above and point it at this repo.

---

## 🔑 Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Flask session signing key |
| `DATABASE_URL` | No | Postgres connection string; omit for local SQLite |
| `GEMINI_API_KEY` | Yes (for AI features) | Google AI Studio API key |
| `GEMINI_MODEL` | No | Defaults to `gemini-2.0-flash` |
| `TESSERACT_CMD` | No | Path to tesseract binary if not on PATH |

---

## 🧠 AI Service Abstraction

All AI calls live in `app/services/ai_service.py` behind five plain functions
(`simplify_notes`, `extract_topics`, `generate_study_plan`, `generate_quiz`,
`chat_reply`). Swapping providers (OpenAI, Claude, local models) only means
rewriting this one file — no blueprint or template changes needed.
