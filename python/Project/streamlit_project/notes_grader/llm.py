from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests


@dataclass(frozen=True)
class LlmConfig:
    provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    timeout_s: int = 60


def _ollama_generate(prompt: str, cfg: LlmConfig) -> Optional[str]:
    url = cfg.ollama_base_url.rstrip("/") + "/api/generate"
    try:
        r = requests.post(
            url,
            json={
                "model": cfg.ollama_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=cfg.timeout_s,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        return (data.get("response") or "").strip() or None
    except Exception:
        return None


def maybe_llm_feedback(*, ocr_text: str, reference_text: Optional[str], cfg: LlmConfig) -> Optional[str]:
    text = (ocr_text or "").strip()
    if not text:
        return None

    ref = (reference_text or "").strip()
    prompt = (
        "You are a strict teacher. Your job is to evaluate handwritten notes after OCR extraction.\n"
        "Give concise feedback with a rating out of 10 and 3-6 bullets.\n\n"
        "Rules:\n"
        "- Focus on correctness, completeness, and clarity.\n"
        "- If OCR is messy, mention that and suggest how to improve the photo.\n"
        "- If reference text is present, compare against it and list the main missing/wrong points.\n"
        "- Output in Markdown.\n\n"
        f"OCR_TEXT:\n{text}\n\n"
    )
    if ref:
        prompt += f"REFERENCE_TEXT:\n{ref}\n\n"

    if cfg.provider == "ollama":
        return _ollama_generate(prompt, cfg)
    return None

