"""
Planner Service
----------------
Local (non-AI) scheduling helpers: fallback greedy planner (used if the AI
call fails or is unavailable), progress calculations, and weekly timetable
generation. Keeping this logic separate from AI means the app degrades
gracefully without an API key.
"""
from datetime import date, timedelta


IMPORTANCE_WEIGHT = {"high": 3, "medium": 2, "low": 1}


def greedy_plan(topics, available_minutes):
    """Fallback deterministic planner: sorts by importance then in_progress
    first, and greedily fills the available time budget."""
    ordered = sorted(
        topics,
        key=lambda t: (
            0 if t["status"] == "in_progress" else 1,
            -IMPORTANCE_WEIGHT.get(t["importance"], 1),
        ),
    )
    remaining = available_minutes
    plan = []
    order_index = 0
    for topic in ordered:
        if remaining <= 0:
            break
        allocated = min(topic["estimated_minutes"], remaining)
        if allocated <= 0:
            continue
        plan.append({"topic_id": topic["id"], "allocated_minutes": allocated, "order_index": order_index})
        remaining -= allocated
        order_index += 1
    return plan


def calculate_completion(topics):
    total = len(topics)
    if total == 0:
        return 0
    completed = sum(1 for t in topics if t["status"] == "completed")
    return round((completed / total) * 100, 1)


def interleave_breaks(items, break_every_minutes=50, break_length=10):
    """Insert short breaks into a plan after roughly every `break_every_minutes`
    of continuous study, Pomodoro-style. `items` is a list of dicts with
    topic_id/allocated_minutes/order_index (as produced by the AI planner or
    greedy_plan). Returns a new list with break entries interleaved."""
    result = []
    continuous = 0
    order_index = 0

    for item in items:
        result.append({
            "topic_id": item["topic_id"],
            "allocated_minutes": item["allocated_minutes"],
            "order_index": order_index,
            "is_break": False,
            "label": None,
        })
        order_index += 1
        continuous += item["allocated_minutes"]

        if continuous >= break_every_minutes:
            result.append({
                "topic_id": None,
                "allocated_minutes": break_length,
                "order_index": order_index,
                "is_break": True,
                "label": "Short break ☕",
            })
            order_index += 1
            continuous = 0

    return result


def week_range(anchor=None):
    anchor = anchor or date.today()
    start = anchor - timedelta(days=anchor.weekday())
    return [start + timedelta(days=i) for i in range(7)]
