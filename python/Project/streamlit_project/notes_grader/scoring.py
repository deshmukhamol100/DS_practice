from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from rapidfuzz import fuzz


@dataclass(frozen=True)
class GradingInput:
    ocr_text: str
    reference_text: Optional[str] = None


@dataclass(frozen=True)
class GradeResult:
    overall_score: float
    rating: str
    accuracy_score: Optional[float]
    summary: str
    warnings: list[str]


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _rating_from_score(score: float) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Average"
    if score >= 40:
        return "Needs improvement"
    return "Poor"


def _basic_quality_score(text: str) -> tuple[float, list[str]]:
    """
    Heuristics for when reference text is missing:
    - more alphabetic content and reasonable word count => better OCR legibility
    - too short / too much noise => worse
    """
    warnings: list[str] = []
    t = (text or "").strip()
    if not t:
        return 0.0, ["No OCR text extracted. Try a clearer photo or different preprocessing."]

    length = len(t)
    words = [w for w in t.split() if w.strip()]
    word_count = len(words)
    alpha = sum(ch.isalpha() for ch in t)
    digits = sum(ch.isdigit() for ch in t)
    spaces = sum(ch.isspace() for ch in t)
    other = length - alpha - digits - spaces

    alpha_ratio = alpha / max(1, length)
    noise_ratio = other / max(1, length)

    score = 35.0
    score += _clamp(alpha_ratio * 55.0, 0, 55)
    score -= _clamp(noise_ratio * 40.0, 0, 40)

    if word_count < 15:
        score -= 10
        warnings.append("Very little text detected; OCR may be missing content.")
    if noise_ratio > 0.22:
        warnings.append("OCR output contains a lot of non-letter characters (possible noise).")

    return _clamp(score), warnings


def _accuracy_vs_reference(ocr_text: str, reference_text: str) -> float:
    # Token-based similarity is more forgiving of OCR spacing/punctuation errors.
    token = fuzz.token_set_ratio(ocr_text, reference_text)
    partial = fuzz.partial_ratio(ocr_text, reference_text)
    ratio = fuzz.ratio(ocr_text, reference_text)
    return float(0.55 * token + 0.25 * partial + 0.20 * ratio)


def grade_notes(inp: GradingInput) -> GradeResult:
    warnings: list[str] = []

    ocr_text = (inp.ocr_text or "").strip()
    if not ocr_text:
        return GradeResult(
            overall_score=0.0,
            rating="Poor",
            accuracy_score=None,
            summary="No text could be extracted from the image.",
            warnings=["Try a clearer photo, better lighting, or different preprocessing (threshold/adaptive)."],
        )

    accuracy: Optional[float] = None
    if inp.reference_text and inp.reference_text.strip():
        ref = inp.reference_text.strip()
        accuracy = _accuracy_vs_reference(ocr_text, ref)
        overall = _clamp(accuracy)
        summary = "Accuracy is computed by comparing OCR text to your reference text (token and character similarity)."
    else:
        overall, w = _basic_quality_score(ocr_text)
        warnings.extend(w)
        summary = (
            "No reference text provided, so the score is based on OCR legibility/quality heuristics. "
            "For true accuracy, paste the correct/expected text in the sidebar."
        )

    return GradeResult(
        overall_score=overall,
        rating=_rating_from_score(overall),
        accuracy_score=accuracy,
        summary=summary,
        warnings=warnings,
    )

