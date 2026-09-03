"""
Spaced Repetition Service (SM-2 algorithm)
--------------------------------------------
Implements the classic SuperMemo SM-2 scheduling algorithm used by Anki and
similar systems. After each review, the card's next_review_date is pushed
further out if the student knew it well, or reset if they struggled.

Quality scale (simplified to 4 UI buttons):
    0 = Again  (didn't know it at all)
    3 = Hard   (knew it, but with real difficulty)
    4 = Good   (knew it after a short pause)
    5 = Easy   (knew it instantly)
"""
from datetime import date, datetime, timedelta

QUALITY_AGAIN = 0
QUALITY_HARD = 3
QUALITY_GOOD = 4
QUALITY_EASY = 5


def schedule_review(card, quality):
    """Mutates and returns the given Flashcard-like object (must have
    ease_factor, interval_days, repetitions, next_review_date,
    last_reviewed_at attributes) according to SM-2."""
    quality = max(0, min(5, int(quality)))

    if quality < 3:
        # Forgot it — reset the repetition streak, review again tomorrow.
        card.repetitions = 0
        card.interval_days = 1
    else:
        if card.repetitions == 0:
            card.interval_days = 1
        elif card.repetitions == 1:
            card.interval_days = 6
        else:
            card.interval_days = round(card.interval_days * card.ease_factor)
        card.repetitions += 1

    # Ease factor adjustment (never drops below 1.3, the SM-2 floor)
    new_ease = card.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    card.ease_factor = max(1.3, round(new_ease, 2))

    card.next_review_date = date.today() + timedelta(days=card.interval_days)
    card.last_reviewed_at = datetime.utcnow()
    return card
