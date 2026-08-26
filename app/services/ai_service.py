"""
AI Service Abstraction Layer
-----------------------------
Every AI-powered feature in StudyMate AI goes through this module.
This means switching providers (Gemini -> OpenAI -> Anthropic -> local model)
never requires touching business logic in the blueprints.

Configured via environment variables:
    AI_PROVIDER=gemini            (default)
    GEMINI_API_KEY=...
    GEMINI_MODEL=gemini-2.5-flash

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
    model_name = current_app.config.get("GEMINI_MODEL", "gemini-2.5-flash")
    return genai.GenerativeModel(model_name)


def _call(prompt, temperature=0.4, max_tokens=2048):
    model = _get_model()
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
    except AIServiceError:
        raise
    except Exception as exc:  # noqa: BLE001 - any SDK/network error becomes a clean AIServiceError
        raise AIServiceError(f"AI request failed: {exc}") from exc

    text = (response.text or "").strip() if response else ""
    if not text:
        raise AIServiceError("The AI returned an empty response. Try again.")
    return text


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


def _clean(raw_text):
    """Strip internal [[PAGE:n]] markers before sending text to the AI."""
    return re.sub(r"\[\[PAGE:\d+\]\]", "", raw_text or "").strip()


def simplify_notes(raw_text, style="simple"):
    text = _clean(raw_text)[:100000]
    prompt = f"""You are an expert tutor. Convert the study material below into short,
clear, easy-to-understand notes for a student. Use bullet points, bold key terms
with **asterisks**, and short paragraphs. Keep the meaning fully intact, just simplify
the language and structure. Style: {style}.

STUDY MATERIAL:
{text}

Return only the simplified notes in Markdown, no preamble."""
    return _call(prompt, temperature=0.3)


def extract_topics(raw_text):
    text = _clean(raw_text)[:100000]
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


def simplify_topic(topic_title, material_text):
    """Produce short, simplified notes for ONE specific topic, pulled from the
    full material. Every important point for this topic must be kept — only
    the language and structure are simplified, nothing is dropped."""
    text = _clean(material_text)[:100000]
    prompt = f"""You are an expert tutor. Below is the FULL study material for a course.
Find everything relevant to the topic "{topic_title}" and rewrite it as short,
clear, easy-to-understand notes for a student.

Rules:
- Cover every important point related to this topic — do not skip or omit any
  fact, definition, formula, or key detail connected to "{topic_title}".
- Simplify the language and structure only. Do not remove information.
- Use bullet points, bold key terms with **asterisks**, short paragraphs.
- If the topic isn't clearly covered in the material, say so briefly and
  summarize the closest related content instead.

FULL STUDY MATERIAL:
{text}

Return only the simplified notes for "{topic_title}" in Markdown, no preamble."""
    return _call(prompt, temperature=0.3)


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
    text = _clean(raw_text)[:100000]
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


def generate_quiz_for_topic(topic_title, material_text, num_questions=5):
    """Create a quiz focused on ONE topic only, using the full material for
    context so every question stays accurate and grounded."""
    text = _clean(material_text)[:100000]
    prompt = f"""Below is the FULL study material for a course. Create a
{num_questions}-question multiple choice quiz that tests ONLY the topic
"{topic_title}". Ignore unrelated sections of the material.

Return ONLY a JSON array like:
[{{
  "question_text": "...",
  "option_a": "...",
  "option_b": "...",
  "option_c": "...",
  "option_d": "...",
  "correct_option": "A",
  "explanation": "...",
  "topic_tag": "{topic_title}"
}}]

FULL STUDY MATERIAL:
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


def coach_reply(history, user_message, topic_title, context=""):
    """AI Coach — a focused, patient tutor for ONE specific topic. Meant to
    be read aloud (voice mode), so responses stay conversational and short."""
    convo = "\n".join(f"{h['role'].upper()}: {h['content']}" for h in history[-10:])
    prompt = f"""You are an expert, patient personal tutor who specializes in
teaching "{topic_title}". A student is studying this exact topic right now and
may ask you to explain it, quiz them, or clear up doubts.

Rules:
- Stay focused on "{topic_title}" unless the student clearly asks something else.
- Teach step by step. Use simple language and short sentences.
- Keep answers conversational and not too long — this may be read aloud to the student.
- Encourage the student and check understanding when it helps.

{f"REFERENCE MATERIAL FOR THIS TOPIC:\n{context[:6000]}" if context else ""}

CONVERSATION SO FAR:
{convo}

STUDENT: {user_message}

Respond as the tutor:"""
    return _call(prompt, temperature=0.6)
