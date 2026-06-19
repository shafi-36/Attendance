"""Local AI text generation with a deterministic fallback."""
from __future__ import annotations

import logging
from functools import lru_cache

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _pipeline():
    settings = get_settings()
    if not settings.ai_enable_local_model:
        return None
    try:
        from transformers import pipeline

        return pipeline("text-generation", model=settings.hf_model_name)
    except Exception as exc:
        logger.warning("Hugging Face model unavailable, using fallback: %s", exc)
        return None


def generate_text(prompt: str, fallback: str) -> str:
    settings = get_settings()
    pipe = _pipeline()
    if pipe is None:
        return fallback

    try:
        result = pipe(
            prompt,
            max_new_tokens=settings.hf_max_new_tokens,
            do_sample=False,
            return_full_text=False,
        )
        text = result[0].get("generated_text", "").strip()
        return text or fallback
    except Exception as exc:
        logger.warning("AI generation failed, using fallback: %s", exc)
        return fallback


def session_summary(stats: dict) -> str:
    fallback = (
        f"{stats['present_students']} of {stats['total_students']} students attended "
        f"{stats['title']} for {stats['subject']} on {stats['session_date']}. "
        f"The attendance rate was {stats['attendance_percentage']}%. "
    )
    if stats["attendance_percentage"] < 75:
        fallback += "Attendance is below the 75% warning threshold and needs follow-up."
    else:
        fallback += "Attendance remained above the warning threshold."

    prompt = (
        "Write a concise faculty attendance summary.\n"
        f"Session data: {stats}\n"
        "Use two sentences and mention risk if attendance is below 75%."
    )
    return generate_text(prompt, fallback)


def low_attendance_warning(student_summary: dict) -> str:
    percentage = student_summary.get("attendance_percentage", 0)
    fallback = (
        f"Your attendance is {percentage}%. Continued absence may affect eligibility "
        "requirements. Please attend upcoming sessions regularly and contact your faculty advisor "
        "if you need support."
    )
    prompt = (
        "Write a short personalized low-attendance warning for a student.\n"
        f"Student attendance data: {student_summary}\n"
        "Keep it respectful, actionable, and under 80 words."
    )
    return generate_text(prompt, fallback)


def department_summary(overview: dict) -> str:
    fallback = (
        f"The department has {overview['total_students']} students across "
        f"{overview['closed_sessions']} closed sessions. Average attendance is "
        f"{overview['average_attendance']}%, with {overview['low_attendance_count']} students "
        "below the 75% threshold."
    )
    prompt = (
        "Write a concise HoD department attendance summary.\n"
        f"Department data: {overview}\n"
        "Mention trend and low-attendance risk."
    )
    return generate_text(prompt, fallback)

