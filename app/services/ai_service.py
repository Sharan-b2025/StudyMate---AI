"""
AI Service Abstraction Layer
-----------------------------
Every AI-powered feature in StudyMate AI goes through this module.
This means switching providers (Gemini -> OpenAI -> Anthropic -> local model)
never requires touching business logic in the blueprints.

Configured via environment variables:
    AI_PROVIDER=gemini            (default)
    GEMINI_API_KEY=...
    GEMINI_MODEL=gemini-2.0-flash

Public functions (all return plain Python data, never raw API responses):
    simplify_notes(raw_text, style="simple") -> str
    extract_topics(raw_text) -> list[dict]
    generate_study_plan(topics, available_minutes) -> list[dict]
    generate_quiz(raw_text, num_questions=5) -> list[dict]
    chat_reply(history, user_message, context="") -> str
"""
import json
import os
import re
from flask import current_app

import google.generativeai as genai


class AIServiceError(Exception):
    pass


def _get_model():
    api_key = current_app.config.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise AIServiceError(
            "GEMINI_API_KEY is not configured. Set it in your environment / Render dashboard."
        )
    genai.configure(api_key=api_key)
    model_name = current_app.config.get("GEMINI_MODEL", "gemini-2.0-flash")
    return genai.GenerativeModel(model_name)


def _call(prompt, temperature=0.4, max_tokens=2048):
    model = _get_model()
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )
    return (response.text or "").strip()


def _extract_json(text):
    """Gemini sometimes wraps JSON in markdown fences - strip them safely."""
    cleaned = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"(\[.*\]|\{.*\})", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise AIServiceError("AI response was not valid JSON.")


def simplify_notes(raw_text, style="simple"):
    text = raw_text[:15000]
    prompt = f"""You are an expert tutor. Convert the study material below into short,
clear, easy-to-understand notes for a student. Use bullet points, bold key terms
with **asterisks**, and short paragraphs. Keep the meaning fully intact, just simplify
the language and structure. Style: {style}.

STUDY MATERIAL:
{text}

Return only the simplified notes in Markdown, no preamble."""
    return _call(prompt, temperature=0.3)


def extract_topics(raw_text):
    text = raw_text[:15000]
    prompt = f"""Analyze the following syllabus / study material and extract the
distinct topics or chapters a student needs to study.

For each topic return:
- "title": short topic name
- "summary": one sentence description
- "importance": "high", "medium", or "low" based on how central it seems
- "estimated_minutes": a realistic study time estimate (15-180)

Return ONLY a JSON array like:
[{{"title": "...", "summary": "...", "importance": "high", "estimated_minutes": 45}}]

MATERIAL:
{text}"""
    result = _call(prompt, temperature=0.2)
    return _extract_json(result)


def generate_study_plan(topics, available_minutes):
    topics_payload = [
        {
            "id": t["id"],
            "title": t["title"],
            "importance": t["importance"],
            "estimated_minutes": t["estimated_minutes"],
            "status": t["status"],
        }
        for t in topics
    ]
    prompt = f"""You are an AI study planner. A student has {available_minutes} minutes
available today. Here are their pending/in-progress topics (JSON):

{json.dumps(topics_payload)}

Build an optimized study session that:
- Prioritizes higher importance and in_progress topics first
- Fits within the {available_minutes} minute budget (never exceed it)
- Allocates realistic minutes per topic (can be less than estimated_minutes if time is short)
- Orders topics logically

Return ONLY a JSON array like:
[{{"topic_id": 1, "allocated_minutes": 30, "order_index": 0}}]"""
    result = _call(prompt, temperature=0.2)
    return _extract_json(result)


def generate_quiz(raw_text, num_questions=5):
    text = raw_text[:15000]
    prompt = f"""Create a {num_questions}-question multiple choice quiz from the study
material below. Cover the most important concepts.

Return ONLY a JSON array like:
[{{
  "question_text": "...",
  "option_a": "...",
  "option_b": "...",
  "option_c": "...",
  "option_d": "...",
  "correct_option": "A",
  "explanation": "...",
  "topic_tag": "short topic name this question belongs to"
}}]

MATERIAL:
{text}"""
    result = _call(prompt, temperature=0.4)
    return _extract_json(result)


def chat_reply(history, user_message, context=""):
    convo = "\n".join(f"{h['role'].upper()}: {h['content']}" for h in history[-10:])
    prompt = f"""You are StudyMate AI, a friendly and encouraging study assistant.
Help the student with study questions, explanations, motivation, and study strategy.
Keep answers concise, clear, and student-friendly. Use markdown formatting when helpful.

{f"RELEVANT CONTEXT FROM THE STUDENT'S MATERIALS:\n{context[:4000]}" if context else ""}

CONVERSATION SO FAR:
{convo}

STUDENT: {user_message}

Respond as StudyMate AI:"""
    return _call(prompt, temperature=0.6)
